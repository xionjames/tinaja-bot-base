from tinaja_base.loader import find_cogs


def test_finds_cogs_defined_in_each_module(tmp_path):
    (tmp_path / 'hello.py').write_text(
        'from discord.ext import commands\n\n\nclass Hello(commands.Cog):\n    pass\n\n\nclass NotACog:\n    pass\n'
    )
    # Hello is imported here, so it must not load twice
    (tmp_path / 'more.py').write_text(
        'from discord.ext import commands\n\nfrom tinaja_base_cogs.hello import Hello\n\n\n'
        'class More(commands.Cog):\n    pass\n'
    )
    (tmp_path / '_private.py').write_text('raise RuntimeError("should not be imported")\n')

    assert [cog.__name__ for cog in find_cogs(tmp_path)] == ['Hello', 'More']


def test_missing_folder_has_no_cogs(tmp_path):
    assert find_cogs(tmp_path / 'cogs') == []
