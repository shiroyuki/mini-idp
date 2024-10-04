from base64 import b64encode, b64decode
from typing import Any, Dict, Union

import jwt
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from imagination.decorator.service import Service


@Service()
class Enigma:
    def __init__(self, ):
        # TODO Improve with https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/.
        with open(f'private.pem', 'r') as f:
            self._private_key = serialization.load_pem_private_key(f.read().encode(), password=None)

        with open(f'public.pem', 'r') as f:
            self._public_key = serialization.load_pem_public_key(f.read().encode())

        self._algorithm = 'RS256'

    def decode(self, token: str) -> Dict[str, Any]:
        return jwt.decode(token, key=self._public_key, algorithms=[self._algorithm])

    def encode(self, payload: Dict[str, Any]) -> str:
        return jwt.encode(payload=payload, key=self._private_key, algorithm=self._algorithm)

    def encrypt(self, message: Union[bytes, str], *, as_hex: bool = True) -> bytes:
        """ Encrypt the message with a permanent key pair """
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
