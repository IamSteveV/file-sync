"""Client-side encryption using AES-256-GCM."""

import os
import secrets
import struct
from pathlib import Path
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""

    pass


class Encryptor:
    """
    Client-side encryption using AES-256-GCM.

    File Format:
    [Magic: 4B] [Version: 1B] [Salt: 16B] [Nonce: 12B] [Encrypted Data] [Auth Tag: 16B]

    The auth tag is included in the ciphertext from AESGCM.
    """

    MAGIC = b"FSYN"  # FileSync magic bytes
    VERSION = 1
    SALT_SIZE = 16
    NONCE_SIZE = 12
    KEY_SIZE = 32  # 256 bits
    TAG_SIZE = 16  # 128 bits (included in AESGCM output)
    CHUNK_SIZE = 64 * 1024  # 64KB chunks for large files

    def __init__(self, passphrase: str):
        """
        Initialize the encryptor with a passphrase.

        Args:
            passphrase: Master passphrase for key derivation
        """
        if not passphrase:
            raise ValueError("Passphrase cannot be empty")

        self.passphrase = passphrase.encode("utf-8")

    def derive_key(self, salt: bytes) -> bytes:
        """
        Derive encryption key from passphrase using PBKDF2.

        Args:
            salt: Salt for key derivation

        Returns:
            32-byte encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=100000,  # OWASP recommendation
            backend=default_backend(),
        )
        return kdf.derive(self.passphrase)

    def encrypt_file(
        self, input_path: str | Path, output_path: str | Path
    ) -> Tuple[str, int]:
        """
        Encrypt a file.

        Args:
            input_path: Path to the plaintext file
            output_path: Path to save encrypted file

        Returns:
            Tuple of (encryption_key_id, encrypted_size)

        Raises:
            EncryptionError: If encryption fails
        """
        try:
            input_path = Path(input_path)
            output_path = Path(output_path)

            # Generate salt and nonce
            salt = secrets.token_bytes(self.SALT_SIZE)
            nonce = secrets.token_bytes(self.NONCE_SIZE)

            # Derive key
            key = self.derive_key(salt)

            # Create AESGCM cipher
            aesgcm = AESGCM(key)

            # Read plaintext
            with open(input_path, "rb") as f:
                plaintext = f.read()

            # Encrypt
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)

            # Write encrypted file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                # Header
                f.write(self.MAGIC)
                f.write(struct.pack("B", self.VERSION))
                f.write(salt)
                f.write(nonce)

                # Encrypted data (includes auth tag)
                f.write(ciphertext)

            # Generate key ID (first 16 chars of salt hex)
            key_id = f"key-{salt.hex()[:16]}"

            encrypted_size = output_path.stat().st_size

            return key_id, encrypted_size

        except Exception as e:
            raise EncryptionError(f"Failed to encrypt file: {e}")

    def decrypt_file(
        self, input_path: str | Path, output_path: str | Path
    ) -> int:
        """
        Decrypt a file.

        Args:
            input_path: Path to the encrypted file
            output_path: Path to save decrypted file

        Returns:
            Size of decrypted file

        Raises:
            EncryptionError: If decryption fails
        """
        try:
            input_path = Path(input_path)
            output_path = Path(output_path)

            with open(input_path, "rb") as f:
                # Read header
                magic = f.read(4)
                if magic != self.MAGIC:
                    raise EncryptionError("Invalid file format: magic bytes mismatch")

                version = struct.unpack("B", f.read(1))[0]
                if version != self.VERSION:
                    raise EncryptionError(f"Unsupported version: {version}")

                salt = f.read(self.SALT_SIZE)
                nonce = f.read(self.NONCE_SIZE)

                # Read encrypted data (includes auth tag)
                ciphertext = f.read()

            # Derive key
            key = self.derive_key(salt)

            # Create AESGCM cipher
            aesgcm = AESGCM(key)

            # Decrypt and verify
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            # Write decrypted file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(plaintext)

            return len(plaintext)

        except Exception as e:
            raise EncryptionError(f"Failed to decrypt file: {e}")

    def encrypt_bytes(self, plaintext: bytes) -> bytes:
        """
        Encrypt bytes directly.

        Args:
            plaintext: Data to encrypt

        Returns:
            Encrypted data with header

        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # Generate salt and nonce
            salt = secrets.token_bytes(self.SALT_SIZE)
            nonce = secrets.token_bytes(self.NONCE_SIZE)

            # Derive key
            key = self.derive_key(salt)

            # Create AESGCM cipher
            aesgcm = AESGCM(key)

            # Encrypt
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)

            # Build result
            result = bytearray()
            result.extend(self.MAGIC)
            result.extend(struct.pack("B", self.VERSION))
            result.extend(salt)
            result.extend(nonce)
            result.extend(ciphertext)

            return bytes(result)

        except Exception as e:
            raise EncryptionError(f"Failed to encrypt bytes: {e}")

    def decrypt_bytes(self, ciphertext: bytes) -> bytes:
        """
        Decrypt bytes directly.

        Args:
            ciphertext: Encrypted data with header

        Returns:
            Decrypted data

        Raises:
            EncryptionError: If decryption fails
        """
        try:
            # Parse header
            offset = 0

            magic = ciphertext[offset : offset + 4]
            offset += 4
            if magic != self.MAGIC:
                raise EncryptionError("Invalid format: magic bytes mismatch")

            version = ciphertext[offset]
            offset += 1
            if version != self.VERSION:
                raise EncryptionError(f"Unsupported version: {version}")

            salt = ciphertext[offset : offset + self.SALT_SIZE]
            offset += self.SALT_SIZE

            nonce = ciphertext[offset : offset + self.NONCE_SIZE]
            offset += self.NONCE_SIZE

            encrypted_data = ciphertext[offset:]

            # Derive key
            key = self.derive_key(salt)

            # Create AESGCM cipher
            aesgcm = AESGCM(key)

            # Decrypt and verify
            plaintext = aesgcm.decrypt(nonce, encrypted_data, None)

            return plaintext

        except Exception as e:
            raise EncryptionError(f"Failed to decrypt bytes: {e}")

    @staticmethod
    def is_encrypted(file_path: str | Path) -> bool:
        """
        Check if a file is encrypted by this system.

        Args:
            file_path: Path to the file

        Returns:
            True if file appears to be encrypted by this system
        """
        try:
            with open(file_path, "rb") as f:
                magic = f.read(4)
                return magic == Encryptor.MAGIC
        except Exception:
            return False

    @staticmethod
    def get_encrypted_size_estimate(plaintext_size: int) -> int:
        """
        Estimate the size of encrypted file.

        Args:
            plaintext_size: Size of plaintext in bytes

        Returns:
            Estimated encrypted size
        """
        header_size = (
            4 + 1 + Encryptor.SALT_SIZE + Encryptor.NONCE_SIZE
        )  # Magic + Version + Salt + Nonce
        return header_size + plaintext_size + Encryptor.TAG_SIZE


class KeyManager:
    """
    Manages encryption keys and key derivation.

    In a production system, this would integrate with OS keychain
    or a dedicated key management service.
    """

    def __init__(self):
        """Initialize key manager."""
        self._master_passphrase: Optional[str] = None

    def set_master_passphrase(self, passphrase: str) -> None:
        """
        Set the master passphrase.

        In production, this should:
        1. Validate passphrase strength
        2. Store in secure memory (e.g., using mlock)
        3. Clear from memory when done

        Args:
            passphrase: Master passphrase
        """
        if not passphrase:
            raise ValueError("Passphrase cannot be empty")

        # TODO: Validate passphrase strength
        # - Minimum length (e.g., 12 characters)
        # - Complexity requirements
        # - Check against common passwords

        self._master_passphrase = passphrase

    def get_master_passphrase(self) -> Optional[str]:
        """Get the master passphrase."""
        return self._master_passphrase

    def has_passphrase(self) -> bool:
        """Check if a passphrase is set."""
        return self._master_passphrase is not None

    def clear_passphrase(self) -> None:
        """Clear the master passphrase from memory."""
        # TODO: Securely zero out memory
        self._master_passphrase = None

    def create_encryptor(self) -> Encryptor:
        """
        Create an encryptor using the master passphrase.

        Returns:
            Encryptor instance

        Raises:
            ValueError: If no passphrase is set
        """
        if not self.has_passphrase():
            raise ValueError("No master passphrase set")

        return Encryptor(self._master_passphrase)

    @staticmethod
    def validate_passphrase_strength(passphrase: str) -> Tuple[bool, str]:
        """
        Validate passphrase strength.

        Args:
            passphrase: Passphrase to validate

        Returns:
            Tuple of (is_valid, message)
        """
        if len(passphrase) < 12:
            return False, "Passphrase must be at least 12 characters"

        # Check for variety
        has_upper = any(c.isupper() for c in passphrase)
        has_lower = any(c.islower() for c in passphrase)
        has_digit = any(c.isdigit() for c in passphrase)
        has_special = any(not c.isalnum() for c in passphrase)

        variety_count = sum([has_upper, has_lower, has_digit, has_special])

        if variety_count < 3:
            return (
                False,
                "Passphrase should contain uppercase, lowercase, digits, and special characters",
            )

        # TODO: Check against common password lists

        return True, "Passphrase is strong"


# Global key manager instance
key_manager = KeyManager()
