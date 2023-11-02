
"""
Sage Desktop Commitments
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import Commitment


class Commitments(Client):
    """Class for Documents APIs."""

    GET_COMMITMENT_ITEMS = '/JobCosting/Api/V1/Commitment.svc/commitments/items/synchronize?commitment={}'
    GET_COMMITMENTS = '/JobCosting/Api/V1/Commitment.svc/commitments'

    def get_all(self):
        """
        Get all Vendors
        :return: List of Dicts in Vendors Schema
        """
        commitments = self._query_get_all(Commitments.GET_COMMITMENTS)
        for commitment in commitments:
            yield Commitment.from_dict(commitment)

    def get_commitment_items(self, commitment_id: str):
        """
        Get Commitment By Id
        :return: Dicts in Commitment Schema
        """
        return self._query_get_by_id(Commitments.GET_COMMITMENT_ITEMS.format(commitment_id))
