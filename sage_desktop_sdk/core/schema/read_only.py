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


@dataclass
class Jobs:
    id: str
    version: int
    account_prefix_id: str
    address1: str
    address2: str
    billing_level: int
    billing_method: int
    city: str
    code: str
    created_on_utc: str
    has_external_id: bool
    is_active: bool
    is_archived: bool
    job_to_date_cost_amount: float
    job_to_date_cost_payment_amount: float
    job_to_date_revenue_payment_amount: float
    job_to_date_revenue_retainage_held_amount: float
    job_to_date_work_billed_amount: float
    last_month_cost_amount: float
    last_month_cost_payment_amount: float
    last_month_revenue_payment_amount: float
    last_month_revenue_retainage_held_amount: float
    last_month_work_billed_amount: float
    misc1_amount: float
    misc2_amount: float
    misc3_amount: float
    month_to_date_cost_amount: float
    month_to_date_cost_payment_amount: float
    month_to_date_revenue_payment_amount: float
    month_to_date_revenue_retainage_held_amount: float
    month_to_date_work_billed_amount: float
    name: str
    postal_code: str
    should_use_project_management: bool
    status: int


    @classmethod
    def from_dict(cls, job_dict):
        return cls(
            id=job_dict['Id'],
            version=job_dict['Version'],
            account_prefix_id=job_dict['AccountPrefixId'],
            address1=job_dict['Address1'],
            address2=job_dict['Address2'],
            billing_level=job_dict['BillingLevel'],
            billing_method=job_dict['BillingMethod'],
            city=job_dict['City'],
            code=job_dict['Code'],
            created_on_utc=job_dict['CreatedOnUtc'],
            has_external_id=job_dict['HasExternalId'],
            is_active=job_dict['IsActive'],
            is_archived=job_dict['IsArchived'],
            job_to_date_cost_amount=job_dict['JobToDateCostAmount'],
            job_to_date_cost_payment_amount=job_dict['JobToDateCostPaymentAmount'],
            job_to_date_revenue_payment_amount=job_dict['JobToDateRevenuePaymentAmount'],
            job_to_date_revenue_retainage_held_amount=job_dict['JobToDateRevenueRetainageHeldAmount'],
            job_to_date_work_billed_amount=job_dict['JobToDateWorkBilledAmount'],
            last_month_cost_amount=job_dict['LastMonthCostAmount'],
            last_month_cost_payment_amount=job_dict['LastMonthCostPaymentAmount'],
            last_month_revenue_payment_amount=job_dict['LastMonthRevenuePaymentAmount'],
            last_month_revenue_retainage_held_amount=job_dict['LastMonthReveueRetainageHeldAmount'],
            last_month_work_billed_amount=job_dict['LastMonthWorkBilledAmount'],
            misc1_amount=job_dict['Misc1Amount'],
            misc2_amount=job_dict['Misc2Amount'],
            misc3_amount=job_dict['Misc3Amount'],
            month_to_date_cost_amount=job_dict['MonthToDateCostAmount'],
            month_to_date_cost_payment_amount=job_dict['MonthToDateCostPaymentAmount'],
            month_to_date_revenue_payment_amount=job_dict['MonthToDateRevenuePaymentAmount'],
            month_to_date_revenue_retainage_held_amount=job_dict['MonthToDateRevenueRetainageHeldAmount'],
            month_to_date_work_billed_amount=job_dict['MonthToDateWorkBilledAmount'],
            name=job_dict['Name'],
            postal_code=job_dict['PostalCode'],
            should_use_project_management=job_dict['ShouldUseProjectManagement'],
            status=job_dict['Status']
        )


@dataclass
class CostCode:
    id: str
    version: int
    code: str
    description: str
    is_active: bool
    is_archived: bool
    is_group_code: bool
    is_standard: bool
    name: str


    @classmethod
    def from_dict(cls, costcode_dict):
        return cls(
            id=costcode_dict['Id'],
            version=costcode_dict['Version'],
            code=costcode_dict['Code'],
            description=costcode_dict['Description'],
            is_active=costcode_dict['IsActive'],
            is_archived=costcode_dict['IsArchived'],
            is_group_code=costcode_dict['IsGroupCode'],
            is_standard=costcode_dict['IsStandard'],
            name=costcode_dict['Name']
        )


@dataclass
class Category:
    id: str
    version: int
    accumulation_name: str
    code: str
    description: str
    is_active: bool
    is_archived: bool
    name: str


    @classmethod
    def from_dict(cls, category_dict):
        return cls(
            id=category_dict['Id'],
            version=category_dict['Version'],
            accumulation_name=category_dict['AccumulationName'],
            code=category_dict['Code'],
            description=category_dict['Description'],
            is_active=category_dict['IsActive'],
            is_archived=category_dict['IsArchived'],
            name=category_dict['Name']
        )


@dataclass
class OperationStatusResponse:
    Id: str
    CreatedOn: str
    TransmittedOn: str
    ReceivedOn: str
    DisabledOn: str
    CompletedOn: str
