"""
Sage Desktop Vendors
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import Vendor, VendorType

class Vendors(Client):
    """Class for Accounts APIs."""

    GET_VENDORS = '/AccountsPayable/Api/V1/Vendor.svc/vendors'


    def get_all(self):
        """
        Get all Vendors
        :return: List of Dicts in Vendors Schema
        """

        return self._query_get_all(Vendors.GET_VENDORS)
