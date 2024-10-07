import asyncio
import traceback
from typing import Callable, List, Dict, Any
from unittest import TestCase
from uuid import uuid4

import yaml
from dotenv import load_dotenv

from midp.app.web_client import MiniIDP, ClientOutput, RestAPIClient
from midp.common.env_helpers import optional_env
from midp.config import MainConfig


class TestConfig:
    TEST_BASE_URL = optional_env('TEST_BASE_URL', 'http://localhost:8081/')

    # Load the test configuration.
    with open(optional_env('TEST_CONFIG_FILE_PATH', 'config-auto-testing.yml'), 'r') as f:
        TEST_BASE_CONFIG: MainConfig = MainConfig(**yaml.load(f.read(), Loader=yaml.SafeLoader))


class _ClientOutput(ClientOutput):
    def __init__(self):
        self._events: Dict[str, Callable[[Dict[str, Any]], None]] = dict()

    def on(self, event: str, handle: Callable[[Dict[str, Any]], None]):
        self._events[event] = handle

    def off(self, event: str):
        del self._events[event]

    def write(self, event: str, template: str, context: Dict[str, Any]):
        if event not in self._events:
            return
        # super().write(event, template, context)
        self._events[event](context)


class GenericDeferrableFeature:
    @classmethod
    def defer_after_all(cls, operation: Callable[[], None]):
        if not hasattr(cls, '_class_deferred_operations'):
            cls._class_deferred_operations: List[Callable[[], None]] = []

        cls._class_deferred_operations.append(operation)

    @classmethod
    def _run_class_deferred_operations(cls):
        if hasattr(cls, '_class_deferred_operations'):
            for op in cls._class_deferred_operations:
                op()

    def defer(self, operation: Callable[[], None]):
        if not hasattr(self, '_method_deferred_operations'):
            self._method_deferred_operations: List[Callable[[], None]] = []

        self._method_deferred_operations.append(operation)

    def _run_method_deferred_operations(self):
        if hasattr(self, '_method_deferred_operations'):
            for op in self._method_deferred_operations:
                op()


class GenericAppFeature(GenericDeferrableFeature, TestCase):
    _env_loaded: bool = False

    @classmethod
    def setUpClass(cls):
        if not cls._env_loaded:
            load_dotenv()
            cls._env_loaded = True

        cls._test_config = TestConfig.TEST_BASE_CONFIG.model_copy()

        cls._client_output = _ClientOutput()
        cls._client = MiniIDP(TestConfig.TEST_BASE_URL, output=cls._client_output)
        cls._client.restore(cls._test_config)
        cls.defer_after_all(cls._remove_test_resources)

    @classmethod
    def tearDownClass(cls):
        cls._run_class_deferred_operations()

    def tearDown(self):
        self._run_method_deferred_operations()

    @classmethod
    def _remove_test_resources(cls):
        async def do_delete(rest_api: RestAPIClient, id: str):
            await asyncio.to_thread(rest_api.delete, id)

        coroutines = []
        for rest_api_name in ('clients',
                              'policies',
                              'roles',
                              'scopes',
                              'users',):
            rest_api: RestAPIClient = getattr(cls._client, rest_api_name)
            resources = getattr(cls._test_config, rest_api_name)
            coroutines.extend([do_delete(rest_api, item.id) for item in resources])

        async def delete_many():
            await asyncio.gather(*coroutines)

        asyncio.run(delete_many())
