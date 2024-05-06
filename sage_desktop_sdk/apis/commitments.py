
"""
Sage Desktop Commitments
"""
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.read_only import CommitmentItem


class Commitments(Client):
    """Class for Documents APIs."""

    GET_COMMITMENT_ITEMS = '/JobCosting/Api/V1/Commitment.svc/commitments/items?commitment={}'
    GET_COMMITMENTS = '/JobCosting/Api/V1/Commitment.svc/commitments'

    def get_all(self, version: int = None):
        """
        Get all commitments.

        :param version: API version
        :type version: int

        :return: A generator yielding commitments in the Commitments Schema
        :rtype: generator of Commitment objects
        """
        endpoint = Commitments.GET_COMMITMENTS + '?page={0}'
        if version:
            # Append the version query parameter if provided
            query_params = f'&version={version}'
            endpoint += query_params

        # Query the API to get all commitments
        commitments = self._query_get_all_generator(endpoint)
        yield commitments

    def get_commitment_items(self, commitment_id: str, version: int = None):
        """
        Get commitment items by ID.

        :param commitment_id: Commitment ID
        :type commitment_id: str
        :param version: API version
        :type version: int

        :return: A dictionary in the Commitment Schema
        :rtype: Commitment object
        """
        if version:
            # Append the version query parameter if provided
            query_params = '?version={0}'.format(version)
            endpoint = Commitments.GET_COMMITMENT_ITEMS.format(commitment_id) + query_params
        else:
            endpoint = Commitments.GET_COMMITMENT_ITEMS.format(commitment_id)

        commitment_items = self._query_get_by_id(endpoint)

        for commitment_item in commitment_items:
            yield CommitmentItem.from_dict(commitment_item)
