from argparse import Namespace, ArgumentParser

from midp.app.cli.commands.abstract import CLICommand
from midp.app.models import ClientConfiguration


class MetaInitialization(CLICommand):
    """ Initialize a new context or override the existing context. """

    def name(self) -> str:
        return 'init'

    def define(self, parser: ArgumentParser):
        super().define(parser)
        parser.add_argument('--base-url', '-u', help='Base URL')

    def run(self, args: Namespace):
        context_name: str = args.context
        base_url: str = args.base_url
        self.set_context(context_name, ClientConfiguration(base_url=base_url))