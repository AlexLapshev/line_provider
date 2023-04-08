import decimal
import enum
from typing import Optional, Any

from pydantic import BaseModel, validator


class Status(enum.Enum):
    NEW = 1
    FINISHED_WIN = 2
    FINISHED_LOSE = 3


class Event(BaseModel):
    event_id: str
    status: Optional[Status] = None
    coefficient: Optional[decimal.Decimal] = None
    deadline: Optional[int] = None

    @validator("coefficient", pre=True)
    def validate_coefficient(cls, v: Any) -> decimal.Decimal:
        s = str(v).split(".")
        if len(s) != 2 or len(s[-1]) > 2 or v <= 0:
            raise ValueError("Incorrect coefficient")
        return v


class MessageSchema(BaseModel):
    event_id: str
    status: Status
