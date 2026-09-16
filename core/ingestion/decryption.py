import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

class FernetDecryptor:
    """
    Decryption helper for Exotel VoiceBot encrypted fields.
    Transcripts and summaries use a single shared Fernet key.
    """
    def __init__(self, key: Optional[str] = None):
        self.key = key or os.getenv("FERNET_KEY")
        self._fernet = None
        if self.key:
            try:
                self._fernet = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
            except Exception as e:
                print(f"Warning: Invalid Fernet key format: {e}")

    def decrypt(self, value: str) -> str:
        """
        Decrypts a string if it starts with 'gAAAA'.
        Returns original value if not encrypted or if decryption fails.
        """
        if not isinstance(value, str) or not value.startswith("gAAAA"):
            return value

        if not self._fernet:
            return value  # Cannot decrypt without valid key

        try:
            return self._fernet.decrypt(value.encode()).decode("utf-8")
        except (InvalidToken, Exception):
            return value

    def decrypt_transcript_line(self, line: str) -> dict:
        """
        Parses a single newline-separated line from encrypted_transcript.
        Format: "BOT: gAAAAAB..." or "CUSTOMER: gAAAAAB..."
        The speaker label (BOT/CUSTOMER) is in plaintext. Only text after ': ' is encrypted.
        """
        line = line.strip()
        if not line:
            return {"speaker": "UNKNOWN", "text": "", "is_encrypted": False}

        if ":" in line:
            parts = line.split(":", 1)
            speaker = parts[0].strip()
            ciphertext = parts[1].strip()
            text = self.decrypt(ciphertext)
            return {
                "speaker": speaker,
                "text": text,
                "is_encrypted": ciphertext.startswith("gAAAA")
            }
        else:
            return {"speaker": "UNKNOWN", "text": line, "is_encrypted": False}
