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


    def sync_accounts(self):
        """
        Get accounts
        """            
        accounts = self.connection.accounts.get_all()
        account_attributes = []

        for account in accounts:
            account_attributes.append({
                'attribute_type': 'ACCOUNT',
                'display_name': 'accounts',
                'value': account.name,
                'destination_id': account.id,
                'active': account.is_active,
                'detail': {
                    'code': account.code,
                    'version': account.version
                }
            })
        
        DestinationAttribute.bulk_create_or_update_destination_attributes(
            account_attributes, 'ACCOUNT', self.workspace_id, True)

        return []


    def sync_vendors(self):
        """
        Get Vendors
        """
        vendors = self.connection.vendors.get_all()
        vendor_attributes = []
        
        for vendor in vendors:
            vendor_attributes.append({
                'attribute_type': 'VENDOR',
                'display_name': 'vendor',
                'value': vendor.name,
                'destination_id': vendor.id,
                'active': vendor.is_active,
                'detail': {
                    'code': vendor.code,
                    'version': vendor.version,
                    'default_expense_account': vendor.default_expense_account,
                    'default_standard_category': vendor.default_standard_category,
                    'default_standard_costcode': vendor.default_standard_costcode,
                    'type_id': vendor.type_id,
                    'created_on_utc': vendor.created_on_utc
                }
            })
            
        DestinationAttribute.bulk_create_or_update_destination_attributes(
            vendor_attributes, 'VENDOR', self.workspace_id, True)
        
        return []


    def sync_jobs(self):
        """
        Get Jobs
        """
        
        jobs = self.connection.jobs.get_all_jobs()
        job_attributes = []

        for job in jobs:
            job_attributes.append({
                'attribute_type': 'JOB',
                'display_name': 'job',
                'value': job.name,
                'destination_id': job.id,
                'active': job.is_active,
                'detail': {
                    'code': job.code,
                    'status': job.status,
                    'account_prefix_id': job.account_prefix_id,
                    'created_on_utc': job.created_on_utc,
                    'version': job.version
                }
            })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            job_attributes, 'JOB', self.workspace_id, True)
        
        return []


    def sync_cost_codes(self):
        """
        Get Cost Codes
        """
        
        cost_codes = self.connection.jobs.get_all_costcodes()
        cost_code_attributes = []
        
        for cost_code in cost_codes:
            cost_code_attributes.append({
                'attribute_type': 'COST_CODE',
                'display_name': 'cost code',
                'value': cost_code.name,
                'destination_id': cost_code.id,
                'active': cost_code.is_active,
                'detail': {
                    'code': cost_code.code,
                    'description': cost_code.description,
                    'is_standard': cost_code.is_standard,
                    'version': cost_code.version
                }
            })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            cost_code_attributes, 'COST_CODE', self.workspace_id, True)
                
        return []


    def sync_categories(self):
        """
        Get Categories
        """
        
        categories = self.connection.jobs.get_all_categories()
        category_attributes = []
        
        for category in categories:
            category_attributes.append({
                'attribute_type': 'CATEGORY',
                'display_name': 'category',
                'value': category.name,
                'destination_id': category.id,
                'active': category.is_active,
                'detail': {
                    'code': category.code,
                    'description': category.description,
                    'is_standard': category.is_standard,
                    'accumulation_name': category.accumulation_name,
                    'version': category.version
                }
            })

        DestinationAttribute.bulk_create_or_update_destination_attributes(
            category_attributes, 'CATEGORY', self.workspace_id, True)
                
        return []


    def sync_commitments(self):
        """
        Get Commitments
        """
    
        commitments = self.connection.commitments.get_all()
        commitment_attributes = []
        
        for commitment in commitments:
            commitment_attributes.append({
                'attribute_type': 'COMMITMENT',
                'display_name': 'commitment',
                'value': commitment.name,
                'destination_id': commitment.id,
                'active': commitment.is_active,
                'detail': {
                    'code': commitment.code,
                    'description': commitment.description,
                    'is_closed': commitment.is_closed,
                    'is_commited': commitment.is_commited,
                    'job_id': commitment.job_id,
                    'vendor_id': commitment.vendor_id,
                    'version': commitment.version,
                    'created_on_utc': commitment.created_on_utc,
                    'date': commitment.date
                }
            })
