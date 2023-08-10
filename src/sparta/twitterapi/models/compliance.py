from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel


class ComplianceEvent(BaseModel):
    id: str
    action: str
    event_at: datetime
    event: Dict[str, Any]
