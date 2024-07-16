import logging
from django.utils.module_loading import import_string
from fyle_accounting_mappings.models import DestinationAttribute
from apps.workspaces.models import Sage300Credential
from sage_desktop_sdk.sage_desktop_sdk import SageDesktopSDK
from apps.sage300.models import CostCategory
from apps.mappings.models import Version
from apps.mappings.exceptions import handle_import_exceptions

logger = logging.getLogger(__name__)
logger.level = logging.INFO


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

    def _create_destination_attribute(self, attribute_type, display_name, value, destination_id, active, detail, code):
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
            'detail': detail,
            'code': code
        }

    def _update_latest_version(self, attribute_type: str):
        """
        Update the latest version in Version Table
        :param attribute_type: Type of the attribute
        """

        latest_version = DestinationAttribute.objects.filter(
            attribute_type=attribute_type,
            workspace_id=self.workspace_id
        ).order_by('-detail__version').first()

        Version.objects.update_or_create(
            workspace_id=self.workspace_id,
            defaults={
                attribute_type.lower(): latest_version.detail['version']
            }
        )

        return []

    def _add_to_destination_attributes(self, item, attribute_type, display_name, field_names, vendor_type_mapping = None):

        detail = {field: getattr(item, field) for field in field_names}
        if vendor_type_mapping:
            if item.type_id in vendor_type_mapping:
                detail['type'] = vendor_type_mapping[item.type_id]
            else:
                detail['type'] = None
        if item.name:
            return self._create_destination_attribute(
                attribute_type,
                display_name,
                " ".join(item.name.split()),
                item.id,
                item.is_active,
                detail,
                item.code
            )

    def _get_attribute_class(self, attribute_type: str):
        """
        Get the attribute class for the attribute type
        :param attribute_type: Type of the attribute
        :return: Attribute class
        """
        ATTRIBUTE_CLASS_MAP = {
            'ACCOUNT': 'Account',
            'VENDOR': 'Vendor',
            'JOB': 'Job',
            'STANDARD_COST_CODE': 'StandardCostCode',
            'STANDARD_CATEGORY': 'StandardCategory',
            'COMMITMENT': 'Commitment',
            'COMMITMENT_ITEM': 'CommitmentItem',
            'COST_CODE': 'CostCode',
            'VENDOR_TYPE': 'VendorType'
        }

        return ATTRIBUTE_CLASS_MAP[attribute_type]

    def _remove_credit_card_vendors(self):
        credit_card_vendor = DestinationAttribute.objects.filter(
            workspace_id=self.workspace_id,
            attribute_type='VENDOR',
            detail__type='Credit Card'
        )
        vendor_count = credit_card_vendor.count()
        logger.info(f'Deleting {vendor_count} credit card vendors from workspace_id {self.workspace_id}')
        credit_card_vendor.delete()

    def _sync_data(self, data_gen, attribute_type, display_name, workspace_id, field_names, is_generator: bool = True, vendor_type_mapping = None):
        """
        Synchronize data from Sage Desktop SDK to your application
        :param data: Data to synchronize
        :param attribute_type: Type of the attribute
        :param display_name: Display name for the data
        :param workspace_id: ID of the workspace
        :param field_names: Names of fields to include in detail
        """

        if is_generator:
            for data in data_gen:
                for items in data:
                    destination_attributes = []
                    for _item in items:
                        attribute_class = self._get_attribute_class(attribute_type)
                        item = import_string(f'sage_desktop_sdk.core.schema.read_only.{attribute_class}').from_dict(_item)
                        destination_attr = self._add_to_destination_attributes(item, attribute_type, display_name, field_names, vendor_type_mapping)
                        if destination_attr:
                            destination_attributes.append(destination_attr)

                    if attribute_type == 'JOB':
                        project_disable_callback_path = 'apps.sage300.helpers.disable_projects'
                        DestinationAttribute.bulk_create_or_update_destination_attributes(
                            destination_attributes,
                            attribute_type,
                            workspace_id,
                            True,
                            attribute_disable_callback_path=project_disable_callback_path
                        )
                    else:
                        DestinationAttribute.bulk_create_or_update_destination_attributes(
                            destination_attributes, attribute_type, workspace_id, True)
        else:
            destination_attributes = []
            for item in data_gen:
                destination_attr = self._add_to_destination_attributes(item, attribute_type, display_name, field_names)
                if destination_attr:
                    destination_attributes.append(destination_attr)

            DestinationAttribute.bulk_create_or_update_destination_attributes(
                destination_attributes, attribute_type, workspace_id, True)

        if attribute_type != 'VENDOR_TYPE':
            self._update_latest_version(attribute_type)
        if attribute_type == 'VENDOR':
            self._remove_credit_card_vendors()

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
        vendor_types = None
        vendor_type_mapping = None

        if not DestinationAttribute.objects.filter(workspace_id=self.workspace_id, attribute_type='VENDOR_TYPE').exists():
            vendor_types = self.connection.vendors.get_vendor_types()
            self._sync_data(vendor_types, 'VENDOR_TYPE', 'vendor_type', self.workspace_id, ['version'])

        vendor_types = DestinationAttribute.objects.filter(workspace_id=self.workspace_id, attribute_type='VENDOR_TYPE').values('destination_id', 'value').distinct()
        vendor_type_mapping = {vendor_type['destination_id']: vendor_type['value'] for vendor_type in vendor_types}

        self._sync_data(vendors, 'VENDOR', 'vendor', self.workspace_id, field_names, vendor_type_mapping=vendor_type_mapping)
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
            self._sync_data(commitment_items, 'COMMITMENT_ITEM', 'commitment_item', self.workspace_id, field_names, False)

    @handle_import_exceptions
    def sync_cost_codes(self, _import_log = None):
        """
        Synchronize cost codes from Sage Desktop SDK to your application
        """
        version = Version.objects.get(workspace_id=self.workspace_id).cost_code
        cost_codes = self.connection.cost_codes.get_all_costcodes(version=version)
        field_names = ['code', 'version', 'job_id']
        self._sync_data(cost_codes, 'COST_CODE', 'cost_code', self.workspace_id, field_names)
        return []

    @handle_import_exceptions
    def sync_cost_categories(self, import_log = None):
        """
         Synchronize categories from Sage Desktop SDK to your application
        """
        version = Version.objects.get(workspace_id=self.workspace_id)
        cost_categories_generator = self.connection.categories.get_all_categories(version=version.cost_category)

        for cost_categories in cost_categories_generator:
            for categories in cost_categories:
                latest_version = max([int(category['Version']) for category in categories])
                CostCategory.bulk_create_or_update(categories, self.workspace_id)
                version.cost_category = latest_version
                version.save()
