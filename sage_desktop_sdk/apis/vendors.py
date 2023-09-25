"""
Sage Desktop Vendors
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import Vendor, VendorType

class Vendors(Client):
    """Class for Accounts APIs."""

    GET_VENDORS = '/AccountsPayable/Api/V1/Vendor.svc/vendors'
    GET_VENDOR_TYPES = '/AccountsPayable/Api/V1/Vendor.svc/vendors/types'


    def get_all(self):
        """
        Get all Vendors
        :return: List of Dicts in Vendors Schema
        """

        list_of_vendors = []
        vendors = self._query_get_all(Vendors.GET_VENDORS)

        for vendor in vendors:
            vendor = Vendor(
                id=vendor['Id'],
                version=vendor['Version'],
                code=vendor['Code'],
                created_on_utc=vendor['CreatedOnUtc'],
                default_expense_account=vendor['DefaultExpenseAccount'],
                default_standard_costcode=vendor['DefaultStandardCostCode'],
                default_standard_category=vendor['DefaultStandardCategory'],
                has_external_id=vendor['HasExternalId'],
                invoice_tax_type=vendor['InvoiceTaxType'],
                is_active=vendor['IsActive'],
                is_archived=vendor['IsArchived'],
                name=vendor['Name'],
                type_id=vendor['TypeId']
            )
            list_of_vendors.append(vendor)

        return list_of_vendors


    def get_vendor_types(self):
        """
        Get Vendor Types
        :return: List of Dicts in Vendor Types Schema
        """

        list_of_vendor_types = []
        vendor_types = self._query_get_all(Vendors.GET_VENDOR_TYPES)

        for vendor_type in vendor_types:
            vendor_type = VendorType(
                id=vendor_type['Id'],
                version=vendor_type['Version'],
                Name=vendor_type['Name']
            )
            list_of_vendor_types.append(vendor_type)
        return vendor_types
