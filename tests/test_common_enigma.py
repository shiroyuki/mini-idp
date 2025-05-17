from unittest import TestCase

from imagination import container

from midp.common.debugging import measure_method_runtime
from midp.common.enigma import Enigma
from midp.log_factory import midp_logger
from tests.common.base_feature import GenericDeferrableFeature

LOG = midp_logger('tests.common.enigma')


class E2ETest(GenericDeferrableFeature, TestCase):
    @classmethod
    def tearDownClass(cls):
        cls._run_class_deferred_operations()

    def setUp(self):
        self._enigma: Enigma = container.get(Enigma)

    def tearDown(self):
        self._run_method_deferred_operations()

    def test_jwt_conversation(self):
        expected_claims = {'a': 1, 'b': 'c'}
        token = self._enigma.encode({'a': 1, 'b': 'c'})
        decoded_claims = self._enigma.decode(token)
        self.assertEqual(expected_claims, decoded_claims)

    # @measure_method_runtime
    def test_asymmetric_encryption_conversation_with_base64_encoding(self):
        expected_message = b'abcdefghijklmnop1234567890'
        encrypted_message = self._enigma.encrypt(expected_message)
        decrypted_message = self._enigma.decrypt(encrypted_message)
        self.assertEqual(expected_message, decrypted_message)
        # LOG.warning(f'test_asymmetric_encryption_conversation_with_base64_encoding:\n{expected_message} → {encrypted_message} ({len(encrypted_message)}) → {decrypted_message}')

    # @measure_method_runtime
    def test_asymmetric_encryption_conversation_without_base64_encoding(self):
        expected_message = b'abcdefghijklmnop1234567890'
        encrypted_message = self._enigma.encrypt(expected_message, as_hex=False)
        decrypted_message = self._enigma.decrypt(encrypted_message, as_hex=False)
        self.assertEqual(expected_message, decrypted_message)
        # LOG.warning(f'test_asymmetric_encryption_conversation_without_base64_encoding:\n{expected_message} → {encrypted_message} ({len(encrypted_message)}) → {decrypted_message}')
