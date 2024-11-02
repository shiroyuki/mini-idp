from argparse import Namespace, ArgumentParser
from collections.abc import Iterable

from midp.app.cli.commands.abstract import CLICommand


class ConfigSetCurrentContext(CLICommand):
    def name(self) -> str:
        return 'config:set-current-context'

    def alternate_names(self) -> Iterable[str]:
        return [
            'config:use',
        ]

    def define(self, parser: ArgumentParser):
        pass

    def run(self, args: Namespace):
        pass