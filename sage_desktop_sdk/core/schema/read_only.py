from dataclasses import dataclass

@dataclass
class Account:
    id: str
    code: str
    version: int
    cost_requirement: int
    code: str
    description: str
    is_active: bool
    is_archived: bool
    name: int
    parent_code: str
    parent_id: str
    parent_name: str


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
