import logging
from uuid import UUID


privacy_logger = logging.getLogger("securedataops.privacy")


def log_privacy_event(action: str, user_id: UUID | None = None) -> None:
    """Emit a minimal privacy audit event without personal-data field values."""
    if user_id is None:
        privacy_logger.info("privacy_action=%s", action)
        return

    privacy_logger.info("privacy_action=%s user_id=%s", action, user_id)
