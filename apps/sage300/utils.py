from fyle_accounting_mappings.models import DestinationAttribute
from apps.workspaces.models import Sage300Credential
from sage_desktop_sdk.sage_desktop_sdk import SageDesktopSDK
from apps.sage300.models import CostCategory
from apps.mappings.models import Version


class SageDesktopConnector:
    """
    Sage300 utility functions for syncing data from Sage Desktop SDK to your application
    """

    def __init__(self, credentials_object: Sage300Credential, workspace_id: int):
        """
        Initialize the Sage Desktop Connector with credentials and workspace ID
        :param credentials_object: Sage300Credential instance containing API credentials
        :param workspace_id: ID of the workspace
        """

        self.connection = SageDesktopSDK(
            api_key=credentials_object.api_key,
            api_secret=credentials_object.api_secret,
            user_name=credentials_object.username,
            password=credentials_object.password,
            indentifier=credentials_object.identifier
        )

        self.workspace_id = workspace_id

    def _create_destination_attribute(self, attribute_type, display_name, value, destination_id, active, detail):
        """
        Create a destination attribute object
        :param attribute_type: Type of the attribute
        :param display_name: Display name for the attribute
        :param value: Value of the attribute
        :param destination_id: ID of the destination
        :param active: Whether the attribute is active
        :param detail: Details related to the attribute
        :return: A destination attribute dictionary
        """
        return {
            'attribute_type': attribute_type,
            'display_name': display_name,
            'value': value,
            'destination_id': destination_id,
            'active': active,
            'detail': detail
        }

    def _update_latest_version(self, attribute_type: str):
        """
        Update the latest version in Version Table
        :param attribute_type: Type of the attribute
        """

        latest_version = DestinationAttribute.objects.filter(
            attribute_type=attribute_type
        ).order_by('-detail__version').first()

        Version.objects.update_or_create(
            workspace_id=self.workspace_id,
            defaults={
                attribute_type.lower(): latest_version.detail['version']
            }
        )

        return []

    def _sync_data(self, data, attribute_type, display_name, workspace_id, field_names):
        """
        Synchronize data from Sage Desktop SDK to your application
        :param data: Data to synchronize
        :param attribute_type: Type of the attribute
        :param display_name: Display name for the data
        :param workspace_id: ID of the workspace
        :param field_names: Names of fields to include in detail
        """

        destination_attributes = []
        for item in data:
            detail = {field: getattr(item, field) for field in field_names}
            if item.name:
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

        self._update_latest_version(attribute_type)

    def sync_accounts(self):
        """
        Synchronize accounts from Sage Desktop SDK to your application
        """
        version = Version.objects.get(workspace_id=self.workspace_id).account
        accounts = self.connection.accounts.get_all(version=version)
        self._sync_data(accounts, 'ACCOUNT', 'accounts', self.workspace_id, ['code', 'version'])
        return []

    def sync_vendors(self):
        """
        Synchronize vendors from Sage Desktop SDK to your application
        """
        version = Version.objects.get(workspace_id=self.workspace_id).vendor
        vendors = self.connection.vendors.get_all(version=version)
        field_names = [
            'code', 'version', 'default_expense_account', 'default_standard_category',
            'default_standard_costcode', 'type_id', 'created_on_utc'
        ]

        self._sync_data(vendors, 'VENDOR', 'vendor', self.workspace_id, field_names)
        return []

    def sync_jobs(self):
        """
        Synchronize jobs from Sage Desktop SDK to your application
        """
        version = Version.objects.get(workspace_id=self.workspace_id).job
        jobs = self.connection.jobs.get_all_jobs(version=version)
        field_names = [
            'code', 'status', 'version', 'account_prefix_id', 'created_on_utc'
        ]
        self._sync_data(jobs, 'JOB', 'job', self.workspace_id, field_names)
        return []

    def sync_standard_cost_codes(self):
        """
        Synchronize standard cost codes from Sage Desktop SDK to your application
        """
        version = Version.objects.get(workspace_id=self.workspace_id).standard_cost_code
        cost_codes = self.connection.jobs.get_standard_costcodes(version=version)
        field_names = ['code', 'version', 'is_standard', 'description']
        self._sync_data(cost_codes, 'STANDARD_COST_CODE', 'standard_cost_code', self.workspace_id, field_names)
        return []

    def sync_standard_categories(self):
        """
        Synchronize standard categories from Sage Desktop SDK to your application
        """
        version = Version.objects.get(workspace_id=self.workspace_id).standard_category
        categories = self.connection.jobs.get_standard_categories(version=version)
        field_names = ['code', 'version', 'description', 'accumulation_name']
        self._sync_data(categories, 'STANDARD_CATEGORY', 'standard_category', self.workspace_id, field_names)
        return []

    def sync_commitments(self):
        """
        Synchronize commitments from Sage Desktop SDK to your application
        """
        version = Version.objects.get(workspace_id=self.workspace_id).commitment
        commitments = self.connection.commitments.get_all(version=version)
        field_names = [
            'code', 'is_closed', 'version', 'description', 'is_commited',
            'created_on_utc', 'date', 'vendor_id', 'job_id'
        ]
        self._sync_data(commitments, 'COMMITMENT', 'commitment', self.workspace_id, field_names)
        return []

    def sync_commitment_items(self):
        """
        Sync commitment items from Sage Desktop SDK to your application
        """
        commitments = DestinationAttribute.objects.filter(
            workspace_id=self.workspace_id,
            attribute_type='COMMITMENT'
        )

        for commitment in commitments:
            commitment_items = self.connection.commitments.get_commitment_items(commitment.destination_id)
            field_names = [
                'code', 'version', 'description', 'cost_code_id',
                'category_id', 'created_on_utc', 'job_id', 'commitment_id'
            ]
            self._sync_data(commitment_items, 'COMMITMENT_ITEM', 'commitment_item', self.workspace_id, field_names)

    def sync_cost_codes(self):
        """
        Synchronize cost codes from Sage Desktop SDK to your application
        """
        version = Version.objects.get(workspace_id=self.workspace_id).cost_code
        cost_codes = self.connection.cost_codes.get_all_costcodes(version=version)
        field_names = ['code', 'version', 'job_id']
        self._sync_data(cost_codes, 'COST_CODE', 'cost_code', self.workspace_id, field_names)
        return []

    def sync_cost_categories(self):
        """
         Synchronize categories from Sage Desktop SDK to your application
        """
        cost_categories = self.connection.categories.get_all_categories()

        CostCategory.bulk_create_or_update(cost_categories, self.workspace_id)
