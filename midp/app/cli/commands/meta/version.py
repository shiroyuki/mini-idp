from argparse import ArgumentParser, Namespace
from platform import platform

from midp import static_info
from midp.app.cli.commands.abstract import CLICommand


class MetaVersion(CLICommand):
    def name(self):
        return 'version'

    def define(self, parser: ArgumentParser):
        pass

    def run(self, args: Namespace):
        print(f'{static_info.ARTIFACT_ID} {static_info.VERSION_INFO} ({platform()})')
