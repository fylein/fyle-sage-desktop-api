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
class Job:
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
class StandardCostCode:
    id: str
    version: int
    code: str
    description: str
    is_active: bool
    is_archived: bool
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
            is_standard=costcode_dict['IsStandard'],
            name=costcode_dict['Name']
        )


@dataclass
class StandardCategory:
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


@dataclass
class CostCode:
    code: str
    cost_code_status: int
    created_on_utc: str
    estimate: float
    estimate_units: float
    has_external_id: bool
    id: str
    is_active: bool
    is_archived: bool
    is_group_code: bool
    job_id: str
    labor_estimate_units: float
    misc1_amount: float
    misc2_amount: float
    misc3_amount: float
    misc4_amount: float
    misc5_amount: float
    misc6_amount: float
    name: str
    original_production_units_estimate: float
    percent_complete: float
    previous_percent_complete: float
    production_estimate_units: float
    production_unit_of_measure: str
    production_units_in_place: float
    standard_cost_code_id: str
    version: int

    @classmethod
    def from_dict(cls, data_dict):
        return cls(
            code=data_dict['Code'],
            cost_code_status=data_dict['CostCodeStatus'],
            created_on_utc=data_dict['CreatedOnUtc'],
            estimate=data_dict['Estimate'],
            estimate_units=data_dict['EstimateUnits'],
            has_external_id=data_dict['HasExternalId'],
            id=data_dict['Id'],
            is_active=data_dict['IsActive'],
            is_archived=data_dict['IsArchived'],
            is_group_code=data_dict['IsGroupCode'],
            job_id=data_dict['JobId'],
            labor_estimate_units=data_dict['LaborEstimateUnits'],
            misc1_amount=data_dict['Misc1Amount'],
            misc2_amount=data_dict['Misc2Amount'],
            misc3_amount=data_dict['Misc3Amount'],
            misc4_amount=data_dict['Misc4Amount'],
            misc5_amount=data_dict['Misc5Amount'],
            misc6_amount=data_dict['Misc6Amount'],
            name=data_dict['Name'],
            original_production_units_estimate=data_dict['OriginalProductionUnitsEstimate'],
            percent_complete=data_dict['PercentComplete'],
            previous_percent_complete=data_dict['PreviousPercentComplete'],
            production_estimate_units=data_dict['ProductionEstimateUnits'],
            production_unit_of_measure=data_dict['ProductionUnitOfMeasure'],
            production_units_in_place=data_dict['ProductionUnitsInPlace'],
            standard_cost_code_id=data_dict['StandardCostCodeId'],
            version=data_dict['Version']
        )


@dataclass
class Category:
    id: str
    version: int
    approved_commitment_changes: float
    approved_estimate_changes: float
    approved_estimate_unit_changes: float
    code: str
    commitment_invoiced: float
    cost_code_id: str
    created_on_utc: str
    estimate: float
    estimate_unit_of_measure: str
    estimate_units: float
    has_external_id: bool
    is_active: bool
    is_archived: bool
    job_id: str
    job_to_date_cost: float
    job_to_date_dollars_paid: float
    job_to_date_units: float
    month_to_date_cost: float
    month_to_date_dollars_paid: float
    month_to_date_units: float
    name: str
    original_commitment: float
    original_estimate: float
    original_estimate_units: float
    percent_complete: float
    revised_commitment: float
    standard_category_id: str
    standard_category_accumulation_name: str
    standard_category_description: str
    standard_category_name: str

    @classmethod
    def from_dict(cls, data_dict):
        return cls(
            id=data_dict['Id'],
            version=data_dict['Version'],
            approved_commitment_changes=data_dict['ApprovedCommitmentChanges'],
            approved_estimate_changes=data_dict['ApprovedEstimateChanges'],
            approved_estimate_unit_changes=data_dict['ApprovedEstimateUnitChanges'],
            code=data_dict['Code'],
            commitment_invoiced=data_dict['CommitmentInvoiced'],
            cost_code_id=data_dict['CostCodeId'],
            created_on_utc=data_dict['CreatedOnUtc'],
            estimate=data_dict['Estimate'],
            estimate_unit_of_measure=data_dict['EstimateUnitOfMeasure'],
            estimate_units=data_dict['EstimateUnits'],
            has_external_id=data_dict['HasExternalId'],
            is_active=data_dict['IsActive'],
            is_archived=data_dict['IsArchived'],
            job_id=data_dict['JobId'],
            job_to_date_cost=data_dict['JobToDateCost'],
            job_to_date_dollars_paid=data_dict['JobToDateDollarsPaid'],
            job_to_date_units=data_dict['JobToDateUnits'],
            month_to_date_cost=data_dict['MonthToDateCost'],
            month_to_date_dollars_paid=data_dict['MonthToDateDollarsPaid'],
            month_to_date_units=data_dict['MonthToDateUnits'],
            name=data_dict['Name'],
            original_commitment=data_dict['OriginalCommitment'],
            original_estimate=data_dict['OriginalEstimate'],
            original_estimate_units=data_dict['OriginalEstimateUnits'],
            percent_complete=data_dict['PercentComplete'],
            revised_commitment=data_dict['RevisedCommitment'],
            standard_category_id=data_dict['StandardCategoryId'],
            standard_category_accumulation_name=data_dict['StandardCategoryAccumulationName'],
            standard_category_description=data_dict['StandardCategoryDescription'],
            standard_category_name=data_dict['StandardCategoryName']
        )
