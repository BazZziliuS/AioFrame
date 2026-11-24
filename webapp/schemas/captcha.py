from typing import Any

from pydantic import BaseModel


class CaptchaChallengeOut(BaseModel):
    enabled: bool
    challenge: dict[str, Any] | None = None
