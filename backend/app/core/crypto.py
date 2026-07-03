from cryptography.fernet import Fernet

from app.core.config import settings

_fernet = Fernet(settings.ENCRYPTION_KEY.encode())


def encrypt(value: str) -> str:
    """Encrypt a plaintext value (e.g. a CNP) for storage at rest (NFR-1)."""
    return _fernet.encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet.decrypt(token.encode()).decode()


def mask_cnp(cnp: str) -> str:
    """Mask a Romanian CNP for API responses, revealing only the last 4 digits."""
    if len(cnp) <= 4:
        return "*" * len(cnp)
    return "*" * (len(cnp) - 4) + cnp[-4:]
