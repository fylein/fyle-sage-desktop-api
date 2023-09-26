from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Distribution:
    AccountsPayableAccountId: str
    Amount: float
    Description: str
    ExpenseAccountId: str
    CategoryId: Optional[str] = None
    CostCodeId: Optional[str] = None
    JobId: Optional[str] = None


@dataclass
class Header:
    AccountingDate: str
    Amount: float
    Code: str
    DeductionAppliedAmount: float
    Description: str
    DiscountAmount: float
    HasExternalId: bool
    InvoiceDate: str
    IsArchived: bool
    IsPending: bool
    IsSuspended: bool
    ReceivedDate: str
    RetainageAmount: float
    RetainageHeldAmount: float
    RetainagePaidAmount: float
    Status: int
    TaxAmount: float
    TaxPaidAmount: float
    TotalPaidAmount: float
    VendorId: str
    Version: int


@dataclass
class Snapshot:
    Distributions: List[Distribution]
    Header: Header


@dataclass
class DocumentPostPayload:
    DocumentTypeId: str
    Snapshot: Snapshot
    ExternalUrl: str
