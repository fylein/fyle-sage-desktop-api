"""
Sage Desktop Vendors
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import Vendor, VendorType


class Vendors(Client):
    """Class for Accounts APIs."""

    GET_VENDORS = '/AccountsPayable/Api/V1/Vendor.svc/vendors'
    GET_VENDOR_TYPES = '/AccountsPayable/Api/V1/Vendor.svc/vendors/types'

    def get_all(self, version: int = None):
        """
        Get all vendors.

        :param version: API version
        :type version: int

        :return: A generator yielding vendors in the Vendors Schema
        :rtype: generator of Vendor objects
        """
        if version:
            # Append the version query parameter if provided
            query_params = '?version={0}'.format(version)
            endpoint = Vendors.GET_VENDORS + query_params
        else:
            endpoint = Vendors.GET_VENDORS

        # Query the API to get all vendors
        vendors = self._query_get_all(endpoint)

        for vendor in vendors:
            # Convert each vendor dictionary to a Vendor object and yield it
            yield Vendor.from_dict(vendor)

    def get_vendor_types(self, version: int = None):
        """
        Get vendor types.

        :param version: API version
        :type version: int

        :return: A generator yielding vendor types in the Vendor Types Schema
        :rtype: generator of VendorType objects
        """
        if version:
            # Append the version query parameter if provided
            query_params = '?version={0}'.format(version)
            endpoint = Vendors.GET_VENDOR_TYPES + query_params
        else:
            endpoint = Vendors.GET_VENDOR_TYPES

        # Query the API to get all vendor types
        vendor_types = self._query_get_all(endpoint)

        for vendor_type in vendor_types:
            # Convert each vendor type dictionary to a VendorType object and yield it
            yield VendorType.from_dict(vendor_type)
