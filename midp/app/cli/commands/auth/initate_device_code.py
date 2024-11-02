from argparse import ArgumentParser, Namespace

from midp.app.cli.commands.abstract import CLICommand


class AuthInitiateDeviceCode(CLICommand):
    def name(self) -> str:
        return 'auth:device-code'

    def define(self, parser: ArgumentParser):
        super().define(parser)
        parser.add_argument('--client-id', help='Client ID')

    def run(self, args: Namespace):
        target_context = args.context
        client_id = args.client_id

        client = self._get_client(target_context)
        client.initiate_device_code(client_id)
