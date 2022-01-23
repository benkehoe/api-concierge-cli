from typing import cast

import click

from . import __version__
from .list import list_handler, add_global_list_options
from .invoke import invoke_handler, add_global_invoke_options
from .get_schema import get_schema_handler, add_global_get_schema_options
from .aws import awslambda
from .platform import Platform


@click.group(name="api-concierge")
@click.version_option(version=__version__, message="%(version)s")
def cli():
    pass

for module in [awslambda]:
    for platform in module.PLATFORMS:
        platform = cast(Platform, platform)
        name = platform.get_name()

        group = click.Group(name)
        cli.add_command(group)

        list_command = platform.get_list_command(list_handler)
        add_global_list_options(list_command)
        group.add_command(list_command, name="list")

        invoke_command = platform.get_invoke_command(invoke_handler)
        add_global_invoke_options(invoke_command)
        group.add_command(invoke_command, name="invoke")

        get_schema_command = platform.get_get_schema_command(get_schema_handler)
        add_global_get_schema_options(get_schema_command)
        group.add_command(get_schema_command, name="get-schema")
