import hashlib
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, model_validator


class RawDeal(BaseModel):
    company_name: str
    deal_size_raw: Optional[str] = None    # e.g. "$5 Mn", "2.5Bn", "–", None
    stage: Optional[str] = None
    industry: Optional[str] = None
    investors: Optional[str] = None        # Free-text investor list from source
    business_model: Optional[str] = None   # B2B / B2C if provided
    source_row: int                         # 1-based row index for traceability


class RawBatch(BaseModel):
    batch_id: str                           # weekly_batch_YYYY_MM_DD
    input_date: date
    raw_deals: list[RawDeal]
    input_source: Literal["csv", "paste"]
    input_checksum: str                     # sha256 of concatenated raw input rows

    @classmethod
    def compute_checksum(cls, raw_text: str) -> str:
        return hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
