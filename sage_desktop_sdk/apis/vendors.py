"""
Sage Desktop Vendors
"""
from sage_desktop_sdk.core.client import Client


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
        endpoint = Vendors.GET_VENDORS
        if version:
            # Append the version query parameter if provided
            query_params = '?version={0}'.format(version)
            endpoint += query_params

        # Query the API to get all vendors
        vendors = self._query_get_all_generator(endpoint)
        yield vendors

    def get_vendor_types(self, version: int = None):
        """
        Get vendor types.

        :param version: API version
        :type version: int

        :return: A generator yielding vendor types in the Vendor Types Schema
        :rtype: generator of VendorType objects
        """
        endpoint = Vendors.GET_VENDOR_TYPES
        if version:
            # Append the version query parameter if provided
            query_params = '?version={0}'.format(version)
            endpoint += query_params

        # Query the API to get all vendor types
        vendor_types = self._query_get_all_generator(endpoint)
        yield vendor_types
