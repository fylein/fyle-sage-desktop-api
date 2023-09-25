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
    job_id: str
    retainage_percent: float
    name: str
    ship_to_address1: str
    ship_to_address2: str
    ship_to_city: str
    ship_to_postal_code: str
    ship_to_state: str
    tax: float
    type: int
    vendor_id: str
    was_printed: bool
    tax_group_id: str


    @classmethod
    def from_dict(cls, commitment):
        return cls(
            id=commitment['Id'],
            version=commitment['Version'],
            amount=commitment['Amount'],
            amount_approved=commitment['AmountApproved'],
            amount_retained=commitment['AmountRetained'],
            amount_invoiced=commitment['AmountInvoiced'],
            amount_original=commitment['AmountOriginal'],
            amount_paid=commitment['AmountPaid'],
            amount_pending=commitment['AmountPending'],
            code=commitment['Code'],
            created_on_utc=commitment['CreatedOnUtc'],
            date=commitment['Date'],
            description=commitment['Description'],
            has_external_id=commitment['HasExternalId'],
            is_active=commitment['IsActive'],
            is_archived=commitment['IsArchived'],
            is_closed=commitment['IsClosed'],
            is_commited=commitment['IsCommited'],
            job_id=commitment['JobId'],
            retainage_percent=commitment['RetainagePercent'],
            name=commitment['Name'],
            ship_to_address1=commitment['ShipToAddress1'],
            ship_to_address2=commitment['ShipToAddress2'],
            ship_to_city=commitment['ShipToCity'],
            ship_to_postal_code=commitment['ShipToPostalCode'],
            ship_to_state=commitment['ShipToState'],
            tax=commitment['Tax'],
            type=commitment['Type'],
            vendor_id=commitment['VendorId'],
            was_printed=commitment['WasPrinted'],
            tax_group_id=commitment['TaxGroupId']
        )
