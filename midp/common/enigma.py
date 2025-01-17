import hashlib
import os
from base64 import b64encode, b64decode
from typing import Any, Dict, Union, Optional

import jwt
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from imagination.decorator.service import Service

from midp.common.env_helpers import optional_env
from midp.log_factory import get_logger_for_object


@Service()
class Enigma:
    def __init__(self, ):
        self._log = get_logger_for_object(self)

        self._private_key: Optional[RSAPrivateKey] = None
        self._public_key: Optional[RSAPublicKey] = None

        self._private_key_pem_file_path = optional_env(
            'MINI_IDP_PRIVATE_KEY_FILE',
            'private.pem',
            help="The path to the private key PEM file",
        )

        self._public_key_pem_file_path = optional_env(
            'MINI_IDP_PUBLIC_KEY_FILE',
            'public.pem',
            help="The path to the private key PEM file",
        )

        # TODO Improve with https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/.
        if os.path.exists(self._private_key_pem_file_path):
            with open(self._private_key_pem_file_path, 'r') as f:
                self._private_key = serialization.load_pem_private_key(f.read().encode(), password=None)
        else:
            self._log.debug("The private key file (PEM) and the cryptographic features are not available.")

        if os.path.exists(self._public_key_pem_file_path):
            with open(self._public_key_pem_file_path, 'r') as f:
                self._public_key = serialization.load_pem_public_key(f.read().encode())
        else:
            self._log.debug("The public key file (PEM) and the cryptographic features are not available.")

        self._algorithm = 'RS256'

    def compute_hash(self, token: str) -> str:
        """ Compute the hash of the given token """
        m = hashlib.new('sha512')
        m.update(token.encode('utf-8'))
        return m.hexdigest()

    def _assert_cryptographic_capabilities(self):
        assert self._private_key is not None and self._public_key is not None, \
            "The cryptographic operation is not available."

    def decode(self, token: str, issuer: Optional[str] = None, audience: Optional[str] = None) -> Dict[str, Any]:
        """ Decode the JWT string """
        self._assert_cryptographic_capabilities()

        return jwt.decode(
            token,
            key=self._public_key,
            algorithms=[self._algorithm],
            issuer=issuer,
            audience=audience,
        )

    def encode(self, payload: Dict[str, Any]) -> str:
        """ Encode the payload into a JWT string """
        self._assert_cryptographic_capabilities()

        return jwt.encode(payload=payload, key=self._private_key, algorithm=self._algorithm)

    def encrypt(self, message: Union[bytes, str], *, as_hex: bool = True) -> bytes:
        """ Encrypt the message with a permanent key pair """
        self._assert_cryptographic_capabilities()

        target = message.encode() if isinstance(message, str) else message

        encrypted_message = self._public_key.encrypt(
            target,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return b64encode(encrypted_message) if as_hex else encrypted_message

    def decrypt(self, message: Union[bytes, str], *, as_hex: bool = True) -> bytes:
        """ Decrypt the message with a permanent key pair """
        self._assert_cryptographic_capabilities()

        target = message.encode() if isinstance(message, str) else message

        decrypted_message = self._private_key.decrypt(
            b64decode(target) if as_hex else target,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return decrypted_message
