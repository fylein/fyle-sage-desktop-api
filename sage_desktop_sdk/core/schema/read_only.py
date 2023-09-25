from dataclasses import dataclass

@dataclass
class Account:
    id: str
    code: str
    version: int
    is_active: bool
    is_archived: bool
    name: int


@dataclass
class Vendor:
    id: str
    version: int
    code: str
    created_on_utc: str
    default_expense_account: str
    default_standard_category: str
    default_standard_costcode: str
    has_external_id: bool
    invoice_tax_type: int
    is_active: bool
    is_archived: bool
    name: str
    type_id: str


@dataclass
class VendorType:
    id: str
    version: int
    name: str

    @classmethod
    def generate_vendor_type(cls, vendor_types):
        for vendor_type_dict in vendor_types:
            yield cls(**vendor_type_dict)

@dataclass
class Commitment:
    id: str
    version: str
    amount: int
    amount_approved: float
    amount_retained: float
    amount_invoiced: float
    amount_original: float
    amount_paid: float
    amount_pending: float
    code: int
    created_on_utc: str
    date: str
    description: str 
    has_external_id: bool
    is_active: bool
    is_archived: bool
    is_closed: bool
    is_commited: bool
    is_committed: bool
    job_id: str
    retainagePercent: float
    name: str
    shipToAddress1: str
    shipToAddress2: str
    shipToCity: str
    shipToPostalCode: str
    shipToState: str
    tax: float
    type: int
    vendorId: str
    was_printed: bool
    tax_group_id: str
