from dataclasses import dataclass

@dataclass
class Account:
    id: str
    code: str
    version: int
    is_active: bool
    is_archived: bool
    name: int


    @classmethod
    def from_dict(cls, account_dict):
        return cls(
            id=account_dict['Id'],
            code=account_dict['Code'],
            version=account_dict['Version'],
            is_active=account_dict['IsActive'],
            is_archived=account_dict['IsArchived'],
            name=account_dict['Name'],
        )


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
    def from_dict(cls, vendor_dict):
        return cls(
            id=vendor_dict['Id'],
            version=vendor_dict['Version'],
            code=vendor_dict['Code'],
            created_on_utc=vendor_dict['CreatedOnUtc'],
            default_expense_account=vendor_dict['DefaultExpenseAccount'],
            default_standard_costcode=vendor_dict['DefaultStandardCostCode'],
            default_standard_category=vendor_dict['DefaultStandardCategory'],
            has_external_id=vendor_dict['HasExternalId'],
            invoice_tax_type=vendor_dict['InvoiceTaxType'],
            is_active=vendor_dict['IsActive'],
            is_archived=vendor_dict['IsArchived'],
            name=vendor_dict['Name'],
            type_id=vendor_dict['TypeId']
        )


@dataclass
class VendorType:
    id: str
    version: int
    name: str

    @classmethod
    def from_dict(cls, vendor_type):
        return cls(
            id=vendor_type['Id'],
            version=vendor_type['Version'],
            name=vendor_type['Name']
        )
