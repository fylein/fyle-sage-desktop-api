
import pytest
from asyncio.log import logger
from datetime import datetime, timedelta, timezone
from unittest import mock
from django.db import transaction
from django_q.models import Schedule

from fyle.platform.exceptions import WrongParamsError
from fyle_accounting_mappings.models import (
    MappingSetting,
    Mapping,
    ExpenseAttribute,
    CategoryMapping,
    DestinationAttribute
)

from apps.workspaces.models import ImportSetting
from apps.accounting_exports.models import Error
from fyle_integrations_imports.models import ImportLog
from .fixtures import data as fyle_data


@pytest.mark.django_db()
def test_resolve_post_category_mapping_errors(test_connection, create_temp_workspace):

    source_category, _ = ExpenseAttribute.objects.update_or_create(
        attribute_type='CATEGORY',
        value='Test Category',
        workspace_id=1,
        defaults={
            'active': None,
            'source_id': 'assf',
            'display_name': 'Test Category',
            'detail': None
        }
    )

    destination_account, _ = DestinationAttribute.objects.update_or_create(
        attribute_type='ACCOUNT',
        value='Test Category',
        workspace_id=1,
        defaults={
            'active': None,
            'destination_id': 'randomid',
            'display_name': 'Test Category',
            'detail': None
        }
    )

    Error.objects.update_or_create(
        workspace_id=1,
        expense_attribute=source_category,
        defaults={
            'type': 'CATEGORY_MAPPING',
            'error_title': source_category.value,
            'error_detail': 'Category mapping is missing',
            'is_resolved': False
        }
    )
    category_mapping, _ = CategoryMapping.objects.update_or_create(
        source_category_id=source_category.id,
        destination_account_id=destination_account.id,
        workspace_id=1
    )

    error = Error.objects.filter(expense_attribute_id=category_mapping.source_category_id).first()
    assert error.is_resolved == True


def test_run_post_mapping_settings_triggers(
    db,
    mocker,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_sage300_creds,
    add_import_settings,
    add_export_settings
):
    mocker.patch(
        'apps.sage300.utils.SageDesktopConnector.__init__',
        return_value=None
    )

    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value=[]
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.ExpenseFields.list_all',
        return_value=fyle_data['get_all_expense_fields']
    )

    workspace_id = 1

    MappingSetting.objects.all().delete()
    Schedule.objects.all().delete()

    mapping_setting = MappingSetting(
        source_field='PROJECT',
        destination_field='PROJECT',
        workspace_id=workspace_id,
        import_to_fyle=True,
        is_custom=False
    )
    mapping_setting.save()

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle'
    assert schedule.args == '1'

    mapping_setting = MappingSetting(
        source_field='COST_CENTER',
        destination_field='CLASS',
        workspace_id=workspace_id,
        import_to_fyle=True,
        is_custom=False
    )
    mapping_setting.save()

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle'
    assert schedule.args == '1'

    mapping_setting = MappingSetting(
        source_field='SAMPLEs',
        destination_field='JOB',
        workspace_id=workspace_id,
        import_to_fyle=True,
        is_custom=True
    )
    mapping_setting.save()

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle'
    assert schedule.args == '1'

    mapping_setting = MappingSetting.objects.filter(
        source_field='PROJECT',
        workspace_id=workspace_id
    ).delete()
    configuration = ImportSetting.objects.filter(workspace_id=workspace_id).first()
    configuration.import_categories = False
    configuration.import_vendors_as_merchants = False
    configuration.save()

    mapping_setting = MappingSetting(
        source_field='LOLOOO',
        destination_field='JOB',
        workspace_id=workspace_id,
        import_to_fyle=True,
        is_custom=False
    )
    mapping_setting.save()

    schedule = Schedule.objects.filter(
        func='apps.mappings.imports.tasks.auto_import_and_map_fyle_fields',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule == None


@pytest.mark.django_db(transaction=True)
def test_run_pre_mapping_settings_triggers(
    db,
    mocker,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_sage300_creds,
    add_import_settings,
    add_export_settings
):
    mocker.patch(
        'apps.sage300.utils.SageDesktopConnector.__init__',
        return_value=None
    )

    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value=[]
    )

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.ExpenseFields.list_all',
        return_value=fyle_data['get_all_expense_fields']
    )

    workspace_id = 1
    custom_mappings = Mapping.objects.filter(workspace_id=workspace_id, source_type='CUSTOM_INTENTS').count()
    assert custom_mappings == 0

    try:
        mapping_setting = MappingSetting.objects.create(
            source_field='CUSTOM_INTENTS',
            destination_field='JOB',
            workspace_id=workspace_id,
            import_to_fyle=True,
            is_custom=True
        )
    except Exception:
        logger.info('Duplicate custom field name')

    custom_mappings = Mapping.objects.last()

    custom_mappings = Mapping.objects.filter(workspace_id=workspace_id, source_type='CUSTOM_INTENTS').count()
    assert custom_mappings == 0

    import_log = ImportLog.objects.filter(
        workspace_id=1,
        attribute_type='CUSTOM_INTENTS'
    ).first()

    assert import_log.status == 'COMPLETE'

    time_difference = datetime.now() - timedelta(hours=2)
    offset_aware_time_difference = time_difference.replace(tzinfo=timezone.utc)
    import_log.last_successful_run_at = offset_aware_time_difference
    import_log.save()

    ImportLog.objects.filter(workspace_id=1, attribute_type='CUSTOM_INTENTS').delete()

    # case where error will occur but we reach the case where there are no destination attributes
    # so we mark the import as complete
    with mock.patch('fyle_integrations_platform_connector.apis.ExpenseCustomFields.post') as mock_call:
        mock_call.side_effect = WrongParamsError(msg='invalid params', response={'code': 400, 'message': 'duplicate key value violates unique constraint '
        '"idx_expense_fields_org_id_field_name_is_enabled_is_custom"', 'Detail': 'Invalid parametrs'})

        mapping_setting = MappingSetting(
            source_field='CUSTOM_INTENTS',
            destination_field='CUSTOM_INTENTS',
            workspace_id=workspace_id,
            import_to_fyle=True,
            is_custom=True
        )

        try:
            with transaction.atomic():
                mapping_setting.save()
        except Exception:
            logger.info('duplicate key value violates unique constraint')

    with mock.patch('fyle_integrations_platform_connector.apis.ExpenseCustomFields.post') as mock_call:
        mock_call.side_effect = WrongParamsError(msg='invalid params', response={'data': None, 'error': 'InvalidUsage', 'message': 'text_column cannot be added as it exceeds the maximum limit(15) of columns of a single type'})

        mapping_setting = MappingSetting(
            source_field='CUSTOM_INTENTS',
            destination_field='CUSTOM_INTENTS',
            workspace_id=workspace_id,
            import_to_fyle=True,
            is_custom=True
        )

        try:
            mapping_setting.save()
        except Exception:
            logger.info('text_column cannot be added as it exceeds the maximum limit(15) of columns of a single type')

    with mock.patch('fyle_integrations_platform_connector.apis.ExpenseCustomFields.post') as mock_call:
        mock_call.side_effect = WrongParamsError(msg='invalid params', response={'data': None,'error': 'IntegrityError','message': 'The values ("or79Cob97KSh", "text_column15", "1") already exists'})

        mapping_setting = MappingSetting(
            source_field='CUSTOM_INTENTS',
            destination_field='CUSTOM_INTENTS',
            workspace_id=workspace_id,
            import_to_fyle=True,
            is_custom=True
        )

        try:
            mapping_setting.save()
        except Exception:
            logger.info('The values ("or79Cob97KSh", "text_column15", "1") already exists')
