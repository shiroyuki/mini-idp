import os
from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional, Iterable

import yaml

from midp.app.cli.models import CLIConfiguration
from midp.app.cli.static_info import DEFAULT_CONTEXT
from midp.app.models import ClientConfiguration
from midp.app.web_client import MiniIDP
from midp.common.env_helpers import optional_env
from midp.log_factory import get_logger_for


class UnsetCurrentContextError(RuntimeError):
    pass


class UnknownContextError(RuntimeError):
    pass


class CLICommand(ABC):
    def __init__(self):
        self._log = get_logger_for(f'CLI/{self.name()}')

    @classmethod
    def doc(cls):
        return cls.__doc__ or None

    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError()

    def alternate_names(self) -> Iterable[str]:
        return tuple()

    @abstractmethod
    def define(self, parser: ArgumentParser):
        parser.add_argument('--context', '-c', help='Context Name', required=False, default=DEFAULT_CONTEXT)

    @abstractmethod
    def run(self, args: Namespace):
        raise NotImplementedError()

    def _get_config_dir_path(self) -> str:
        return optional_env('MINI_IDP_CONFIG_DIR',
                            os.path.join(Path.home(), '.config', 'mini-idp'),
                            help='The path of the directory containing configuration and session data')

    def _get_config_file_path(self) -> str:
        return optional_env('MINI_IDP_CONFIG_FILE',
                            os.path.join(self._get_config_dir_path(), 'cli.yml'),
                            help='The path of the configuration file')

    def _load_config(self) -> CLIConfiguration:
        config_path = self._get_config_file_path()
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                raw_config = yaml.load(f.read(), Loader=yaml.SafeLoader)
                return CLIConfiguration(**raw_config)
        else:
            return CLIConfiguration()

    def _save_config(self, config: CLIConfiguration):
        config_path = self._get_config_file_path()
        if not os.path.exists(config_path):
            os.makedirs(os.path.dirname(config_path))
        with open(config_path, 'w') as f:
            f.write(yaml.dump(config.model_dump(mode='python'), Dumper=yaml.SafeDumper))

    def set_current_context(self, name: str):
        config = self._load_config()

        if name not in config.contexts:
            raise UnknownContextError(name)

        config.current_context = name
        self._save_config(config)

        return self

    def set_context(self, name: str, client_config: ClientConfiguration):
        config = self._load_config()
        config.contexts[name] = client_config

        if not config.current_context:
            config.current_context = name
            self._log.debug(f'The current context is set to "{name}".')

        self._save_config(config)

        return self

    def get_context(self, name: Optional[str] = None) -> ClientConfiguration:
        config = self._load_config()
        target_context = name or config.current_context

        if not target_context:
            if config.contexts:
                raise UnsetCurrentContextError(f'Run "config:set-current-context" to set the "{target_context}" '
                                               f'context as the current context. Your options are: "{"\", \"".join([
                                                   c for c in config.contexts.keys()
                                               ])}".')
            else:
                raise UnsetCurrentContextError('Run "init" to initialize your first context.')
        elif name not in config.contexts:
            raise UnknownContextError(target_context)
        else:
            return config[name]

    def delete_context(self, name: str):
        config = self._load_config()

        if name not in config.contexts:
            self._log.debug(f'The given context is not registered.')
        else:
            del config[name]
            self._log.debug(f'The given context is now REMOVED.')

            if config.current_context == name:
                config.current_context = None
                self._log.debug(f'The current context is now UNSET.')

            self._save_config(config)

    def _get_client(self, name: Optional[str] = None) -> MiniIDP:
        config = self._load_config()
        target_context = name or config.current_context

        if target_context not in config.contexts:
            raise UnknownContextError(target_context)

        client_config = config.contexts[target_context]

        return MiniIDP(client_config.base_url)
