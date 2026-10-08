import importlib.util
import inspect
import sys
from pathlib import Path

from discord.ext import commands


def find_cogs(directory):
    """Import every module in directory and return the Cog classes each one defines"""
    directory = Path(directory)
    if not directory.is_dir():
        return []

    cogs = []
    for path in sorted(directory.glob('*.py')):
        if path.name.startswith('_'):
            continue
        module = _import(path)
        for _, obj in inspect.getmembers(module, inspect.isclass):
            # Skip Cogs the module only imported, so each one loads once
            if issubclass(obj, commands.Cog) and obj.__module__ == module.__name__:
                cogs.append(obj)
    return cogs


def _import(path):
    name = f'tinaja_base_cogs.{path.stem}'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
