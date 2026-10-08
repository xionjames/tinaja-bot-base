import subprocess
import tomllib

import pytest

from tinaja_base import cli
from tinaja_base.config import Config
from tinaja_base.loader import find_cogs

REMOTE = 'https://github.com/xionjames/tinaja-bot-base'


class DockerCalls(list):
    def __init__(self):
        super().__init__()
        self.uv_lock_status = 0
        self.uv_lock_error = ''
        self.git_answers = {
            ('remote', 'get-url', 'origin'): 'git@github.com:XionJames/My-Bot.git',
            ('rev-parse', '--short', 'HEAD'): 'abc1234',
            ('ls-remote', REMOTE): 'f00\tHEAD\nf00\trefs/heads/main\nba5\trefs/tags/v1',
        }


@pytest.fixture
def docker(monkeypatch):
    """Records docker commands instead of running them; git calls get canned answers"""
    calls = DockerCalls()
    answers = calls.git_answers

    def run(command, **kwargs):
        if command[0] == 'git':
            output = answers.get(tuple(command[3:]))
            return subprocess.CompletedProcess(command, 0 if output else 128, stdout=output or '', stderr='')
        if command[0] == 'uv':
            return subprocess.CompletedProcess(command, calls.uv_lock_status, stdout='', stderr=calls.uv_lock_error)
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, 'run', run)
    return calls


@pytest.fixture
def bot_project(tmp_path, monkeypatch):
    assert cli.main(['new', 'My Bot', '--dir', str(tmp_path), '--source', REMOTE, '--rev', 'v1']) == 0
    project = tmp_path / 'my-bot'
    (project / 'uv.lock').write_text('')
    monkeypatch.chdir(project)
    return project


def test_new_creates_a_working_bot_project(bot_project, monkeypatch):
    names = {str(p.relative_to(bot_project)) for p in bot_project.rglob('*') if p.is_file()}
    assert {
        'bot.toml',
        'env.sample',
        'CONTEXT.md',
        'README.md',
        'pyproject.toml',
        'Dockerfile',
        '.dockerignore',
        '.gitignore',
        '.python-version',
        'cogs/hello.py',
        'tests/test_hello.py',
        '.github/workflows/build-and-push.yaml',
    } <= names

    pyproject = tomllib.loads((bot_project / 'pyproject.toml').read_text())
    assert pyproject['project']['name'] == 'my-bot'
    assert pyproject['tool']['uv']['sources']['tinaja-bot-base'] == {'git': REMOTE, 'rev': 'v1'}

    monkeypatch.setenv('DISCORD_BOT_TOKEN', 'abc')
    config = Config.load(bot_project / 'bot.toml')
    assert config.name == 'My Bot'
    assert config.mention_prefix
    assert [cog.__name__ for cog in find_cogs(config.cogs_path)] == ['Hello']
    # GitHub expressions in the workflow survive templating
    assert '${{ env.REGISTRY }}' in (bot_project / '.github/workflows/build-and-push.yaml').read_text()


def test_new_refuses_an_existing_folder(tmp_path, capsys):
    (tmp_path / 'my-bot').mkdir()
    assert cli.main(['new', 'My Bot', '--dir', str(tmp_path), '--source', REMOTE]) == 1
    assert 'already exists' in capsys.readouterr().err


def test_new_with_local_path_source(tmp_path):
    cli.main(['new', 'Dev', '--dir', str(tmp_path), '--source', str(tmp_path)])
    pyproject = tomllib.loads((tmp_path / 'dev' / 'pyproject.toml').read_text())
    assert pyproject['tool']['uv']['sources']['tinaja-bot-base'] == {'path': tmp_path.as_posix(), 'editable': True}


@pytest.mark.parametrize(
    'remote',
    [
        'git@github.com:xionjames/tinaja-bot-base.git',
        'https://github.com/xionjames/tinaja-bot-base.git',
        'ssh://git@github.com/xionjames/tinaja-bot-base',
    ],
)
def test_github_remotes_become_https(remote):
    assert cli.https_url(remote) == REMOTE


def test_build_tags_from_git_remote(bot_project, docker):
    assert cli.main(['build']) == 0
    assert docker == [
        ['docker', 'build', '-t', 'ghcr.io/xionjames/my-bot:latest', '-t', 'ghcr.io/xionjames/my-bot:abc1234', '.']
    ]


def test_build_with_options_and_push(bot_project, docker):
    cli.main(['build', '--image', 'ghcr.io/Me/Bot', '--tag', 'v1', '--platform', 'linux/arm64', '--push'])
    assert docker == [
        ['docker', 'build', '-t', 'ghcr.io/me/bot:v1', '--platform', 'linux/arm64', '.'],
        ['docker', 'push', 'ghcr.io/me/bot:v1'],
    ]


def test_build_without_git_uses_project_name(bot_project, docker):
    del docker.git_answers['remote', 'get-url', 'origin']
    del docker.git_answers['rev-parse', '--short', 'HEAD']
    cli.main(['build'])
    assert docker == [['docker', 'build', '-t', 'my-bot:latest', '.']]


def test_build_refuses_a_local_path_source(tmp_path, monkeypatch, docker, capsys):
    cli.main(['new', 'Dev', '--dir', str(tmp_path), '--source', str(tmp_path)])
    (tmp_path / 'dev' / 'uv.lock').write_text('')
    monkeypatch.chdir(tmp_path / 'dev')
    assert cli.main(['build']) == 1
    assert 'switch to a git source' in capsys.readouterr().err
    assert docker == []


def test_build_needs_a_lockfile(bot_project, docker, capsys):
    (bot_project / 'uv.lock').unlink()
    assert cli.main(['build']) == 1
    assert 'uv.lock not found' in capsys.readouterr().err


def test_publish_pushes_every_tag(bot_project, docker):
    cli.main(['publish'])
    assert docker == [
        ['docker', 'push', 'ghcr.io/xionjames/my-bot:latest'],
        ['docker', 'push', 'ghcr.io/xionjames/my-bot:abc1234'],
    ]


def test_publish_failure_explains_login(bot_project, monkeypatch, capsys):
    monkeypatch.setattr(subprocess, 'run', lambda command, **kw: subprocess.CompletedProcess(command, 1, stdout=''))
    assert cli.main(['publish', '--image', 'ghcr.io/me/bot']) == 1
    assert 'docker login ghcr.io' in capsys.readouterr().err


def test_default_source_is_the_framework_remote_over_https(monkeypatch):
    monkeypatch.setattr(cli, 'git', lambda directory, *args: 'git@github.com:xionjames/tinaja-bot-base.git')
    assert cli.framework_source(None, 'main') == f'{{ git = "{REMOTE}", rev = "main" }}'


def test_default_source_needs_a_remote(monkeypatch):
    monkeypatch.setattr(cli, 'git', lambda directory, *args: None)
    with pytest.raises(cli.CliError, match='--source'):
        cli.framework_source(None, 'main')


def test_check_passes_for_a_new_bot(bot_project, docker, capsys):
    assert cli.main(['check']) == 0
    assert 'ready to build' in capsys.readouterr().out


def check_problems(project):
    problems, _ = cli.check_project(project)
    return '\n'.join(problems)


def test_check_needs_the_framework_pushed(bot_project, docker):
    del docker.git_answers['ls-remote', REMOTE]
    assert 'cannot reach https://github.com/xionjames/tinaja-bot-base' in check_problems(bot_project)


def test_check_needs_the_rev_to_exist(bot_project, docker):
    pyproject = bot_project / 'pyproject.toml'
    pyproject.write_text(pyproject.read_text().replace('rev = "v1"', 'rev = "v2"'))
    assert 'no branch or tag "v2"' in check_problems(bot_project)

    pyproject.write_text(pyproject.read_text().replace('rev = "v2"', 'rev = "0a1b2c3d"'))
    assert check_problems(bot_project) == ''  # a commit can't be listed by ls-remote, so it isn't checked


def test_check_needs_something_for_the_bot_to_do(bot_project, docker):
    (bot_project / 'cogs' / 'hello.py').unlink()
    bot_toml = bot_project / 'bot.toml'
    bot_toml.write_text(bot_toml.read_text().replace('ping = "pong {author}"', ''))
    assert 'the bot does nothing yet' in check_problems(bot_project)


def test_check_reports_cogs_that_fail_to_import(bot_project, docker):
    (bot_project / 'cogs' / 'broken.py').write_text('import not_installed_anywhere\n')
    assert "cogs/ failed to import: ModuleNotFoundError: No module named 'not_installed_anywhere'" in check_problems(
        bot_project
    )


def test_check_reports_missing_files_and_bad_toml(bot_project, docker):
    (bot_project / 'Dockerfile').unlink()
    (bot_project / 'bot.toml').write_text('name = ')
    problems = check_problems(bot_project)
    assert 'Dockerfile not found' in problems
    assert 'bot.toml:' in problems


def test_check_warns_about_an_empty_glossary(bot_project, docker, capsys):
    (bot_project / 'CONTEXT.md').unlink()
    assert cli.main(['check']) == 0
    assert 'defines no glossary terms' in capsys.readouterr().out


def test_build_stops_before_docker_when_not_ready(bot_project, docker, capsys):
    (bot_project / 'cogs' / 'broken.py').write_text('raise RuntimeError("boom")\n')
    assert cli.main(['build']) == 1
    assert 'RuntimeError: boom' in capsys.readouterr().err
    assert docker == []


def test_check_needs_a_usable_lockfile(bot_project, docker):
    docker.uv_lock_status = 1
    docker.uv_lock_error = 'error: Failed to build tinaja-bot-base\n  does not appear to be a Python project'
    problems = check_problems(bot_project)
    assert 'uv.lock is not usable' in problems
    assert 'does not appear to be a Python project' in problems
