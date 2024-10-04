import traceback
from typing import Callable, List, Dict, Any
from unittest import TestCase

import yaml

from midp.app.web_client import MiniIDP, ClientOutput
from midp.common.env_helpers import optional_env
from midp.config import MainConfig


class TestingConfig:
    TEST_BASE_URL = optional_env('TEST_BASE_URL', 'http://localhost:8081/')

    # Load the test configuration.
    with open(optional_env('TEST_CONFIG_FILE_PATH', 'config-auto-testing.yml'), 'r') as f:
        TEST_CONFIG: MainConfig = MainConfig(**yaml.load(f.read(), Loader=yaml.SafeLoader))
    TEST_REALM_NAMES = [r.name for r in TEST_CONFIG.realms]


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
    @classmethod
    def setUpClass(cls):
        cls._client_output = _ClientOutput()
        cls._client = MiniIDP(TestingConfig.TEST_BASE_URL, output=cls._client_output)
        cls._client.restore(TestingConfig.TEST_CONFIG)
        cls.defer_after_all(cls._remove_test_realms)

    @classmethod
    def tearDownClass(cls):
        cls._run_class_deferred_operations()

    def tearDown(self):
        self._run_method_deferred_operations()

    @classmethod
    def _remove_test_realms(cls):
        realms = cls._client.rest_realms.list()

        for realm in realms:
            if realm.name not in TestingConfig.TEST_REALM_NAMES:
                continue

            try:
                cls._client.rest_realms.delete(realm.id)
            except AssertionError as e:
                print(f'❌ NOT DELETED: {realm} (ERROR)')
                traceback.print_exc()
