"""
Sage Desktop Documents
"""
import json
from sage_desktop_sdk.core.client import Client
from sage_desktop_sdk.core.schema.write_only import DocumentPostPayload


class Documents(Client):
    """Class for Documents APIs."""

    GET_DOCUMENTS = '/Api/V1/Document.svc/document?id={}'
    POST_DOCUMENT = '/documentmanagement/Api/V1/Document.svc/document'
    POST_DOCUMENT_EXPORT = '/DocumentManagement/Api/V1/Document.svc/document/actions/export?document={}'


    def get(self, document_id: str):
        """
        Get all Vendors
        :return: List of Dicts in Vendors Schema
        """
        return self._query_get_by_id(Documents.GET_DOCUMENTS.format(document_id))


    def post_document(self, data: dict):
        """
        Get Vendor Types
        :return: List of Dicts in Vendor Types Schema
        """
        return self._post_request(Documents.POST_DOCUMENT, data=json.dumps(data.__dict__))


    def export_document(self, document_id: str):
       """
       Export Document to Sage300
       """
       return self._post_request(Documents.POST_DOCUMENT_EXPORT.format(document_id))
