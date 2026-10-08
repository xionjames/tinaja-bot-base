import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from string import Template

FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = Path(__file__).resolve().parent / 'templates' / 'new_bot'
GITHUB_REMOTE = re.compile(r'github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$')


class CliError(Exception):
    pass


def main(argv=None):
    parser = argparse.ArgumentParser(prog='tinaja-bot', description='Build and run Discord bots on tinaja-bot-base')
    sub = parser.add_subparsers(dest='command', required=True)

    run = sub.add_parser('run', help='connect the bot to Discord')
    run.add_argument('--config', default='bot.toml')
    run.set_defaults(func=cmd_run)

    new = sub.add_parser('new', help='create a new bot project')
    new.add_argument('name')
    new.add_argument('--dir', default='.', help='where to create the project folder')
    new.add_argument('--source', help="the framework's git URL, or a local path while developing the framework")
    new.add_argument('--rev', default='main', help='framework branch, tag or commit to depend on')
    new.set_defaults(func=cmd_new)

    check = sub.add_parser('check', help='check the bot is ready to build and ship')
    check.set_defaults(func=cmd_check)

    for name, func, help_text in [
        ('build', cmd_build, 'build the Docker image'),
        ('publish', cmd_publish, 'push the Docker image, e.g. to ghcr.io'),
    ]:
        command = sub.add_parser(name, help=help_text)
        command.add_argument('--image', help='image name; defaults to ghcr.io/<owner>/<repo> from the git remote')
        command.add_argument('--tag', action='append', help='repeatable; defaults to latest and the short git SHA')
        if name == 'build':
            command.add_argument('--platform', help='e.g. linux/amd64,linux/arm64')
            command.add_argument('--push', action='store_true', help='publish after building')
        command.set_defaults(func=func)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (CliError, ValueError, FileNotFoundError, subprocess.CalledProcessError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 1
    return 0


def cmd_run(args):
    from tinaja_base.bot import BaseBot
    from tinaja_base.config import Config

    config = Config.load(args.config)
    BaseBot(config).run(config.token)


def cmd_new(args):
    slug = re.sub(r'[^a-z0-9]+', '-', args.name.lower()).strip('-')
    if not slug:
        raise CliError(f'"{args.name}" is not a usable bot name')
    target = Path(args.dir) / slug
    if target.exists():
        raise CliError(f'{target} already exists')

    values = {
        'bot_name': args.name,
        'bot_slug': slug,
        'framework_source': framework_source(args.source, args.rev),
    }
    for template in sorted(TEMPLATE_DIR.rglob('*')):
        if template.is_dir() or '__pycache__' in template.parts:
            continue
        # Dotfiles are stored as dot-<name> so packaging tools don't skip them
        relative = Path(*[part.replace('dot-', '.', 1) for part in template.relative_to(TEMPLATE_DIR).parts])
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        # safe_substitute leaves ${{ github.* }} and $PATH in the templates untouched
        destination.write_text(Template(template.read_text()).safe_substitute(values))

    print(f'Created {target}. Next steps:')
    print(f'  cd {target} && uv sync && cp env.sample .env  # then set DISCORD_BOT_TOKEN')
    print('  uv run tinaja-bot run')


def framework_source(source, rev):
    """The [tool.uv.sources] entry a new bot uses to depend on this framework"""
    if source is None:
        source = git(FRAMEWORK_ROOT, 'remote', 'get-url', 'origin')
        if source is None:
            raise CliError('could not find the framework git remote; pass --source <git-url>')
    if not _is_remote(source):
        return f'{{ path = "{Path(source).resolve().as_posix()}", editable = true }}'
    return f'{{ git = "{https_url(source)}", rev = "{rev}" }}'


def https_url(remote):
    """Turn an ssh GitHub remote into https, so Docker and CI can fetch it without ssh keys"""
    match = GITHUB_REMOTE.search(remote)
    if match is None:
        return remote
    return f'https://github.com/{match["owner"]}/{match["repo"]}'


def cmd_check(args):
    problems, warnings = check_project(Path.cwd())
    for warning in warnings:
        print(f'warning: {warning}')
    if problems:
        raise CliError('the bot is not ready to build:\n' + '\n'.join(f'  - {problem}' for problem in problems))
    print('The bot is ready to build.')


def check_project(project):
    """What stops the bot in project from becoming a working image: (problems, warnings)"""
    problems = []
    warnings = []

    try:
        pyproject = read_pyproject(project)
    except (CliError, tomllib.TOMLDecodeError) as error:
        return [f'pyproject.toml: {error}'], warnings
    source = pyproject.get('tool', {}).get('uv', {}).get('sources', {}).get('tinaja-bot-base')
    if source is None:
        problems.append('pyproject.toml has no [tool.uv.sources] entry for tinaja-bot-base')
    elif 'path' in source:
        problems.append('tinaja-bot-base comes from a local path; switch to a git source to build images')
    elif 'git' in source:
        problems += _check_git_source(project, source['git'], source.get('rev'))

    for required, fix in [('Dockerfile', 'copy it from "tinaja-bot new"'), ('uv.lock', 'run "uv lock"')]:
        if not (project / required).is_file():
            problems.append(f'{required} not found; {fix}')
    if not problems:
        # Resolves the framework source for real, so it also catches a rev that doesn't contain the framework yet
        problems += _check_lockfile(project)

    from tinaja_base.config import Config
    from tinaja_base.context import Context
    from tinaja_base.loader import find_cogs

    try:
        config = Config.load(project / 'bot.toml', require_token=False)
    except (OSError, tomllib.TOMLDecodeError, TypeError) as error:
        problems.append(f'bot.toml: {error}')
        return problems, warnings
    try:
        cogs = find_cogs(config.cogs_path)
    except Exception as error:  # noqa: BLE001 - any error in the bot's own code would crash it on start
        problems.append(f'{config.cogs_dir}/ failed to import: {type(error).__name__}: {error}')
        return problems, warnings
    if not config.replies and not any(cog.__cog_commands__ or cog.__cog_listeners__ for cog in cogs):
        problems.append(f'the bot does nothing yet: add a Cog to {config.cogs_dir}/ or a [replies] entry to bot.toml')
    if not Context.from_file(config.context_path).terms:
        warnings.append(f'{config.context_file} defines no glossary terms, so !glossary will be empty')
    return problems, warnings


def _check_git_source(project, url, rev):
    refs = git(project, 'ls-remote', url)
    if refs is None:
        return [f'cannot reach {url}; is it pushed and public?']
    names = {line.split('\t')[1] for line in refs.splitlines() if '\t' in line}
    is_commit = rev is not None and re.fullmatch(r'[0-9a-f]{7,40}', rev)
    if rev is not None and not is_commit and not names & {f'refs/heads/{rev}', f'refs/tags/{rev}'}:
        return [f'{url} has no branch or tag "{rev}"; push it or change rev in pyproject.toml']
    return []


def _check_lockfile(project):
    try:
        result = subprocess.run(['uv', 'lock', '--check'], cwd=project, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return ['uv not found; install it to check uv.lock']
    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip().splitlines()
        return ['uv.lock is not usable ("uv lock --check" failed): ' + ' '.join(line.strip() for line in details[-3:])]
    return []


def cmd_build(args):
    project = Path.cwd()
    problems, _ = check_project(project)
    if problems:
        raise CliError(
            'the bot is not ready to build (see "tinaja-bot check"):\n'
            + '\n'.join(f'  - {problem}' for problem in problems)
        )
    pyproject = read_pyproject(project)

    command = ['docker', 'build']
    for name in image_names(project, args.image, args.tag, pyproject):
        command += ['-t', name]
    if args.platform:
        command += ['--platform', args.platform]
    command.append('.')
    subprocess.run(command, check=True)
    if args.push:
        cmd_publish(args)


def cmd_publish(args):
    project = Path.cwd()
    for name in image_names(project, args.image, args.tag, read_pyproject(project)):
        if subprocess.run(['docker', 'push', name], check=False).returncode != 0:
            raise CliError(
                f'pushing {name} failed. For ghcr.io, log in first: '
                'echo $CR_PAT | docker login ghcr.io -u <github-user> --password-stdin'
            )


def image_names(project, image, tags, pyproject):
    if image is None:
        match = GITHUB_REMOTE.search(git(project, 'remote', 'get-url', 'origin') or '')
        if match is not None:
            image = f'ghcr.io/{match["owner"]}/{match["repo"]}'
        else:
            image = pyproject.get('project', {}).get('name', project.name)
    if not tags:
        tags = ['latest']
        sha = git(project, 'rev-parse', '--short', 'HEAD')
        if sha:
            tags.append(sha)
    # Registries reject uppercase, and GitHub owners often have it
    return [f'{image.lower()}:{tag}' for tag in tags]


def read_pyproject(project):
    path = project / 'pyproject.toml'
    if not path.is_file():
        raise CliError('pyproject.toml not found; run this from the bot project folder')
    with path.open('rb') as f:
        return tomllib.load(f)


def git(directory, *args):
    """Output of a git command, or None outside a repository or without git"""
    try:
        result = subprocess.run(['git', '-C', str(directory), *args], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _is_remote(source):
    return '://' in source or source.startswith('git@')
