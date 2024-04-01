from dataclasses import dataclass


@dataclass
class Account:
    id: str
    code: str
    version: int
    is_active: bool
    is_archived: bool
    name: str

    @classmethod
    def from_dict(cls, account_dict):
        return cls(
            id=account_dict.get('Id'),
            code=account_dict.get('Code'),
            version=account_dict.get('Version'),
            is_active=account_dict.get('IsActive'),
            is_archived=account_dict.get('IsArchived'),
            name=account_dict.get('Name'),
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
            id=vendor_dict.get('Id'),
            version=vendor_dict.get('Version'),
            code=vendor_dict.get('Code'),
            created_on_utc=vendor_dict.get('CreatedOnUtc'),
            default_expense_account=vendor_dict.get('DefaultExpenseAccount'),
            default_standard_costcode=vendor_dict.get('DefaultStandardCostCode'),
            default_standard_category=vendor_dict.get('DefaultStandardCategory'),
            has_external_id=vendor_dict.get('HasExternalId'),
            invoice_tax_type=vendor_dict.get('InvoiceTaxType'),
            is_active=vendor_dict.get('IsActive'),
            is_archived=vendor_dict.get('IsArchived'),
            name=vendor_dict.get('Name'),
            type_id=vendor_dict.get('TypeId')
        )


@dataclass
class VendorType:
    id: str
    version: int
    name: str

    @classmethod
    def from_dict(cls, vendor_type):
        return cls(
            id=vendor_type.get('Id'),
            version=vendor_type.get('Version'),
            name=vendor_type.get('Name')
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
            id=commitment.get('Id'),
            version=commitment.get('Version'),
            amount=commitment.get('Amount'),
            amount_approved=commitment.get('AmountApproved'),
            amount_retained=commitment.get('AmountRetained'),
            amount_invoiced=commitment.get('AmountInvoiced'),
            amount_original=commitment.get('AmountOriginal'),
            amount_paid=commitment.get('AmountPaid'),
            amount_pending=commitment.get('AmountPending'),
            code=commitment.get('Code'),
            created_on_utc=commitment.get('CreatedOnUtc'),
            date=commitment.get('Date'),
            description=commitment.get('Description'),
            has_external_id=commitment.get('HasExternalId'),
            is_active=commitment.get('IsActive'),
            is_archived=commitment.get('IsArchived'),
            is_closed=commitment.get('IsClosed'),
            is_commited=commitment.get('IsCommited'),
            job_id=commitment.get('JobId'),
            retainage_percent=commitment.get('RetainagePercent'),
            name=commitment.get('Name'),
            ship_to_address1=commitment.get('ShipToAddress1'),
            ship_to_address2=commitment.get('ShipToAddress2'),
            ship_to_city=commitment.get('ShipToCity'),
            ship_to_postal_code=commitment.get('ShipToPostalCode'),
            ship_to_state=commitment.get('ShipToState'),
            tax=commitment.get('Tax'),
            type=commitment.get('Type'),
            vendor_id=commitment.get('VendorId'),
            was_printed=commitment.get('WasPrinted'),
            tax_group_id=commitment.get('TaxGroupId')
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
            id=job_dict.get('Id'),
            version=job_dict.get('Version'),
            account_prefix_id=job_dict.get('AccountPrefixId'),
            address1=job_dict.get('Address1'),
            address2=job_dict.get('Address2'),
            billing_level=job_dict.get('BillingLevel'),
            billing_method=job_dict.get('BillingMethod'),
            city=job_dict.get('City'),
            code=job_dict.get('Code'),
            created_on_utc=job_dict.get('CreatedOnUtc'),
            has_external_id=job_dict.get('HasExternalId'),
            is_active=job_dict.get('IsActive'),
            is_archived=job_dict.get('IsArchived'),
            job_to_date_cost_amount=job_dict.get('JobToDateCostAmount'),
            job_to_date_cost_payment_amount=job_dict.get('JobToDateCostPaymentAmount'),
            job_to_date_revenue_payment_amount=job_dict.get('JobToDateRevenuePaymentAmount'),
            job_to_date_revenue_retainage_held_amount=job_dict.get('JobToDateRevenueRetainageHeldAmount'),
            job_to_date_work_billed_amount=job_dict.get('JobToDateWorkBilledAmount'),
            last_month_cost_amount=job_dict.get('LastMonthCostAmount'),
            last_month_cost_payment_amount=job_dict.get('LastMonthCostPaymentAmount'),
            last_month_revenue_payment_amount=job_dict.get('LastMonthRevenuePaymentAmount'),
            last_month_revenue_retainage_held_amount=job_dict.get('LastMonthRevenueRetainageHeldAmount'),
            last_month_work_billed_amount=job_dict.get('LastMonthWorkBilledAmount'),
            misc1_amount=job_dict.get('Misc1Amount'),
            misc2_amount=job_dict.get('Misc2Amount'),
            misc3_amount=job_dict.get('Misc3Amount'),
            month_to_date_cost_amount=job_dict.get('MonthToDateCostAmount'),
            month_to_date_cost_payment_amount=job_dict.get('MonthToDateCostPaymentAmount'),
            month_to_date_revenue_payment_amount=job_dict.get('MonthToDateRevenuePaymentAmount'),
            month_to_date_revenue_retainage_held_amount=job_dict.get('MonthToDateRevenueRetainageHeldAmount'),
            month_to_date_work_billed_amount=job_dict.get('MonthToDateWorkBilledAmount'),
            name=job_dict.get('Name'),
            postal_code=job_dict.get('PostalCode'),
            should_use_project_management=job_dict.get('ShouldUseProjectManagement'),
            status=job_dict.get('Status')
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
            id=costcode_dict.get('Id'),
            version=costcode_dict.get('Version'),
            code=costcode_dict.get('Code'),
            description=costcode_dict.get('Description'),
            is_active=costcode_dict.get('IsActive'),
            is_archived=costcode_dict.get('IsArchived'),
            is_standard=costcode_dict.get('IsStandard'),
            name=costcode_dict.get('Name')
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
            id=category_dict.get('Id'),
            version=category_dict.get('Version'),
            accumulation_name=category_dict.get('AccumulationName'),
            code=category_dict.get('Code'),
            description=category_dict.get('Description'),
            is_active=category_dict.get('IsActive'),
            is_archived=category_dict.get('IsArchived'),
            name=category_dict.get('Name')
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
            code=data_dict.get('Code'),
            cost_code_status=data_dict.get('CostCodeStatus'),
            created_on_utc=data_dict.get('CreatedOnUtc'),
            estimate=data_dict.get('Estimate'),
            estimate_units=data_dict.get('EstimateUnits'),
            has_external_id=data_dict.get('HasExternalId'),
            id=data_dict.get('Id'),
            is_active=data_dict.get('IsActive'),
            is_archived=data_dict.get('IsArchived'),
            is_group_code=data_dict.get('IsGroupCode'),
            job_id=data_dict.get('JobId'),
            labor_estimate_units=data_dict.get('LaborEstimateUnits'),
            misc1_amount=data_dict.get('Misc1Amount'),
            misc2_amount=data_dict.get('Misc2Amount'),
            misc3_amount=data_dict.get('Misc3Amount'),
            misc4_amount=data_dict.get('Misc4Amount'),
            misc5_amount=data_dict.get('Misc5Amount'),
            misc6_amount=data_dict.get('Misc6Amount'),
            name=data_dict.get('Name'),
            original_production_units_estimate=data_dict.get('OriginalProductionUnitsEstimate'),
            percent_complete=data_dict.get('PercentComplete'),
            previous_percent_complete=data_dict.get('PreviousPercentComplete'),
            production_estimate_units=data_dict.get('ProductionEstimateUnits'),
            production_unit_of_measure=data_dict.get('ProductionUnitOfMeasure'),
            production_units_in_place=data_dict.get('ProductionUnitsInPlace'),
            standard_cost_code_id=data_dict.get('StandardCostCodeId'),
            version=data_dict.get('Version')
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
            id=data_dict.get('Id'),
            version=data_dict.get('Version'),
            approved_commitment_changes=data_dict.get('ApprovedCommitmentChanges'),
            approved_estimate_changes=data_dict.get('ApprovedEstimateChanges'),
            approved_estimate_unit_changes=data_dict.get('ApprovedEstimateUnitChanges'),
            code=data_dict.get('Code'),
            commitment_invoiced=data_dict.get('CommitmentInvoiced'),
            cost_code_id=data_dict.get('CostCodeId'),
            created_on_utc=data_dict.get('CreatedOnUtc'),
            estimate=data_dict.get('Estimate'),
            estimate_unit_of_measure=data_dict.get('EstimateUnitOfMeasure'),
            estimate_units=data_dict.get('EstimateUnits'),
            has_external_id=data_dict.get('HasExternalId'),
            is_active=data_dict.get('IsActive'),
            is_archived=data_dict.get('IsArchived'),
            job_id=data_dict.get('JobId'),
            job_to_date_cost=data_dict.get('JobToDateCost'),
            job_to_date_dollars_paid=data_dict.get('JobToDateDollarsPaid'),
            job_to_date_units=data_dict.get('JobToDateUnits'),
            month_to_date_cost=data_dict.get('MonthToDateCost'),
            month_to_date_dollars_paid=data_dict.get('MonthToDateDollarsPaid'),
            month_to_date_units=data_dict.get('MonthToDateUnits'),
            name=data_dict.get('Name'),
            original_commitment=data_dict.get('OriginalCommitment'),
            original_estimate=data_dict.get('OriginalEstimate'),
            original_estimate_units=data_dict.get('OriginalEstimateUnits'),
            percent_complete=data_dict.get('PercentComplete'),
            revised_commitment=data_dict.get('RevisedCommitment'),
            standard_category_id=data_dict.get('StandardCategoryId'),
            standard_category_accumulation_name=data_dict.get('StandardCategoryAccumulationName'),
            standard_category_description=data_dict.get('StandardCategoryDescription'),
            standard_category_name=data_dict.get('StandardCategoryName')
        )


@dataclass
class CommitmentItem:
    id: str
    version: int
    amount: float
    amount_approved: float
    amount_invoiced: float
    amount_paid: float
    amount_original: float
    amount_pending: float
    amount_retained: float
    category_id: str
    code: str
    commitment_id: str
    cost_code_id: str
    created_on_utc: str
    description: str
    has_external_id: bool
    is_active: bool
    is_archived: bool
    job_id: str
    name: str
    standard_category_id: str
    tax: float
    tax_group_id: str
    tax_group_code: str
    unit_cost: float
    units: float

    @classmethod
    def from_dict(cls, item_dict):
        return cls(
            id=item_dict.get('Id'),
            version=item_dict.get('Version'),
            amount=item_dict.get('Amount'),
            amount_approved=item_dict.get('AmountApproved'),
            amount_invoiced=item_dict.get('AmountInvoiced'),
            amount_paid=item_dict.get('AmountPaid'),
            amount_original=item_dict.get('AmountOriginal'),
            amount_pending=item_dict.get('AmountPending'),
            amount_retained=item_dict.get('AmountRetained'),
            category_id=item_dict.get('CategoryId'),
            code=item_dict.get('Code'),
            commitment_id=item_dict.get('CommitmentId'),
            cost_code_id=item_dict.get('CostCodeId'),
            created_on_utc=item_dict.get('CreatedOnUtc'),
            description=item_dict.get('Description'),
            has_external_id=item_dict.get('HasExternalId'),
            is_active=item_dict.get('IsActive'),
            is_archived=item_dict.get('IsArchived'),
            job_id=item_dict.get('JobId'),
            name=item_dict.get('Name'),
            standard_category_id=item_dict.get('StandardCategoryId'),
            tax=item_dict.get('Tax'),
            tax_group_id=item_dict.get('TaxGroupId'),
            tax_group_code=item_dict.get('TaxGroupCode'),
            unit_cost=item_dict.get('UnitCost'),
            units=item_dict.get('Units')
        )
