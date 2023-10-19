from django.conf import settings

from fyle_accounting_mappings.models import DestinationAttribute

from apps.workspaces.models import Sage300Credentials
from sage_desktop_sdk.sage_desktop_sdk import SageDesktopSDK



class SageDesktopConnector:
    """
    Sage300 utility functions
    """

    def __init__(self, credentials_object: Sage300Credentials, workspace_id: int):
        
        self.connection = SageDesktopSDK(
            api_key=credentials_object.api_key,
            api_secret=credentials_object.api_secret,
            user_name=credentials_object.username,
            password=credentials_object.password,
            indentifier=credentials_object.identifier
        )
        
        self.workspace_id = workspace_id


    def _create_destination_attribute(self, attribute_type, display_name, value, destination_id, active, detail):
        return {
            'attribute_type': attribute_type,
            'display_name': display_name,
            'value': value,
            'destination_id': destination_id,
            'active': active,
            'detail': detail
        }


    def _sync_data(self, data, attribute_type, display_name, workspace_id, field_names):
        destination_attributes = []

        for item in data:
            detail = {field: getattr(item, field) for field in field_names}
            destination_attributes.append(self._create_destination_attribute(
                attribute_type,
                display_name,
                item.name,
                item.id,
                item.is_active,
                detail
            ))

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            destination_attributes, attribute_type, workspace_id, True)


    def sync_accounts(self):
        """
        Get accounts
        """            

        accounts = self.connection.accounts.get_all()
        self._sync_data(accounts, 'ACCOUNT', 'accounts', self.workspace_id, ['code', 'version'])
        return []


    def sync_vendors(self):
        """
        Get Vendors
        """

        vendors = self.connection.vendors.get_all()
        field_names = [
            'code', 'version', 'default_expense_account', 'default_standard_category',
            'default_standard_costcode', 'type_id', 'created_on_utc'
        ]
        self._sync_data(vendors, 'VENDOR', 'vendor', self.workspace_id, field_names)
        return []


    def sync_jobs(self):
        """
        Get Jobs
        """
        
        jobs = self.connection.jobs.get_all_jobs()
        field_names = [
            'code', 'status', 'version', 'account_prefix_id', 'created_on_utc'
        ]
        self._sync_data(jobs, 'JOB', 'job', self.workspace_id, field_names)
        return []


    def sync_cost_codes(self):
        """
        Get Cost Codes
        """
        
        cost_codes = self.connection.jobs.get_all_costcodes()
        field_names = ['code', 'version', 'is_standard', 'description']
        self._sync_data(cost_codes, 'COST_CODE', 'cost_code', self.workspace_id, field_names)
        return []


    def sync_categories(self):
        """
        Get Categories
        """
        
        categories = self.connection.jobs.get_all_categories()
        field_names = ['code', 'version', 'description', 'accumulation_name']
        self._sync_data(categories, 'COST_CODE', 'cost_code', self.workspace_id, field_names)
        return []


    def sync_commitments(self):
        """
        Get Commitments
        """
    
        commitments = self.connection.commitments.get_all()
        field_names = [
            'code', 'is_closed', 'version', 'description', 'is_commited',
            'created_on_utc', 'date', 'vendor_id', 'job_id'
        ]
        self._sync_data(commitments, 'COMMITMENT', 'commitment', self.workspace_id, field_names)
        return []

