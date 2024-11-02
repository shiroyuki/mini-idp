import sys
from argparse import ArgumentParser
from typing import List, Optional, Tuple

from midp.app.cli.commands.abstract import CLICommand
from midp.app.cli.commands.auth.initate_device_code import AuthInitiateDeviceCode
from midp.app.cli.commands.meta.configs import ConfigSetCurrentContext
from midp.app.cli.commands.meta.initialization import MetaInitialization
from midp.app.cli.commands.meta.version import MetaVersion

enabled_commands: List[CLICommand] = sorted([
    AuthInitiateDeviceCode(),
    ConfigSetCurrentContext(),
    MetaInitialization(),
    MetaVersion(),
], key=lambda c: c.name())

parser = ArgumentParser()
subparsers = parser.add_subparsers()

for enabled_command in enabled_commands:
    primary_command_name = enabled_command.name()

    subparser = subparsers.add_parser(primary_command_name, help=enabled_command.doc())
    subparser.set_defaults(handler=enabled_command)
    enabled_command.define(subparser)

    alternate_commands = enabled_command.alternate_names()

    for alternate_command in alternate_commands:
        subparser = subparsers.add_parser(alternate_command, help=f'Alias to "{primary_command_name}"')
        subparser.set_defaults(handler=enabled_command)
        enabled_command.define(subparser)

parsed_args = parser.parse_args()

if hasattr(parsed_args, 'handler'):
    parsed_args.handler.run(parsed_args)
else:
    available_commands: List[Tuple[str, Optional[str]]] = list()

    for enabled_command in enabled_commands:
        primary_command_name = enabled_command.name()
        available_commands.append((primary_command_name, enabled_command.doc()))

        for alternate_command in enabled_command.alternate_names():
            available_commands.append((alternate_command, f'Alias to "{primary_command_name}"'))

    sys.stderr.write('Please specify the command to get started:\n\n')
    for name, doc in available_commands:
        if doc:
            sys.stderr.write(f' ⏺ {name} - {doc}\n')
        else:
            sys.stderr.write(f' ⏺ {name}\n')
    sys.stderr.write('\n')
