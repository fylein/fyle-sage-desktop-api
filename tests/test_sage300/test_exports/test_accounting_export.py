import pytest
from apps.sage300.exports.accounting_export import AccountingDataExporter
from apps.accounting_exports.models import AccountingExport


def test_accounting_data_exporter_1():
    workspace_id = 1
    accounting_data_exporter = AccountingDataExporter()

    with pytest.raises(NotImplementedError):
        accounting_data_exporter.post(
            workspace_id=workspace_id,
            body="Random body",
            lineitems="Random lineitems"
        )

    assert True


def test_accounting_data_exporter_2(
    db,
    mocker,
    create_temp_workspace,
    add_advanced_settings,
    add_accounting_export_expenses,
    create_employee_mapping_with_employee,
    create_category_mapping
):
    workspace_id = 1

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    accounting_export.status = 'ENQUEUED'
    accounting_export.save()

    accounting_data_exporter = AccountingDataExporter()

    mock_body_model = mocker.patch.object(accounting_data_exporter, 'body_model')
    mock_lineitem_model = mocker.patch.object(accounting_data_exporter, 'lineitem_model')

    mocker.patch.object(mock_body_model, 'create_or_update_object')
    mocker.patch.object(mock_lineitem_model, 'create_or_update_object')

    with pytest.raises(NotImplementedError):
        accounting_data_exporter.create_sage300_object(
            accounting_export=accounting_export
        )

    assert accounting_export.status == 'IN_PROGRESS'
    assert mock_body_model.create_or_update_object.call_count == 1
    assert mock_lineitem_model.create_or_update_object.call_count == 1


def test_accounting_data_exporter_3(
    db,
    mocker,
    create_temp_workspace,
    add_advanced_settings,
    add_accounting_export_expenses,
    create_employee_mapping_with_employee,
    create_category_mapping
):
    workspace_id = 1

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    accounting_export.status = 'ENQUEUED'
    accounting_export.save()

    accounting_data_exporter = AccountingDataExporter()

    mock_body_model = mocker.patch.object(accounting_data_exporter, 'body_model')
    mock_lineitem_model = mocker.patch.object(accounting_data_exporter, 'lineitem_model')

    mock_post = mocker.patch.object(accounting_data_exporter, 'post', return_value='Random response')

    mocker.patch.object(mock_body_model, 'create_or_update_object')
    mocker.patch.object(mock_lineitem_model, 'create_or_update_object')

    accounting_data_exporter.create_sage300_object(
        accounting_export=accounting_export
    )

    assert accounting_export.status == 'EXPORT_QUEUED'
    assert mock_body_model.create_or_update_object.call_count == 1
    assert mock_lineitem_model.create_or_update_object.call_count == 1
    assert mock_post.call_count == 1

    assert accounting_export.detail == {'export_id': 'Random response'}


def test_accounting_data_exporter_4(
    db,
    mocker,
    create_temp_workspace,
    add_advanced_settings,
    add_accounting_export_expenses,
    create_employee_mapping_with_employee,
    create_category_mapping
):
    workspace_id = 1

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    accounting_export.status = 'COMPLETE'
    accounting_export.save()

    accounting_data_exporter = AccountingDataExporter()

    mock_body_model = mocker.patch.object(accounting_data_exporter, 'body_model')
    mock_lineitem_model = mocker.patch.object(accounting_data_exporter, 'lineitem_model')
    mock_post = mocker.patch.object(accounting_data_exporter, 'post', return_value='Random response')

    mocker.patch.object(mock_body_model, 'create_or_update_object')
    mocker.patch.object(mock_lineitem_model, 'create_or_update_object')

    accounting_data_exporter.create_sage300_object(
        accounting_export=accounting_export
    )

    assert accounting_export.status == 'COMPLETE'
    assert mock_body_model.create_or_update_object.call_count == 0
    assert mock_lineitem_model.create_or_update_object.call_count == 0
    assert mock_post.call_count == 0
