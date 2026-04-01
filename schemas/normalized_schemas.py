from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel


class NormalizedDeal(BaseModel):
    company_name: str
    deal_size_mn: Optional[float] = None   # Always in $ Mn; None = undisclosed
    deal_size_disclosed: bool
    stage_normalized: str                  # Canonical stage bucket from STAGE_MAP
    sector_normalized: str                 # Canonical sector from SECTOR_MAP
    business_model: Literal["B2B", "B2C"]
    investors_list: list[str]              # Split, stripped, deduplicated
    source_row: int                        # Traces back to RawDeal.source_row


class NormalizedBatch(BaseModel):
    batch_id: str
    input_date: date
    total_deals: int
    total_disclosed_capital_mn: float      # Sum of all disclosed deal sizes
    deals: list[NormalizedDeal]
