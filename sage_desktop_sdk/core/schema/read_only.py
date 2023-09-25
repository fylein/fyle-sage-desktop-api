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
    
    @classmethod
    def generate_vendors(cls, vendors):
        for vendor_dict in vendors:
            yield cls(**vendor_dict)


@dataclass
class VendorType:
    id: str
    version: int
    name: str

    @classmethod
    def generate_vendor_type(cls, vendor_types):
        for vendor_type_dict in vendor_types:
            yield cls(**vendor_type_dict)
