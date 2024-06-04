rollback;
begin;

insert into mapping_settings (source_field, destination_field, import_to_fyle, is_custom, workspace_id, created_at, updated_at)
select 'CORPORATE_CARD', 'VENDOR', 'f', 'f', ws.id, now(), now()
from workspaces ws
where not exists (
    select 1
    from mapping_settings ms 
    inner join export_settings es 
    on es.workspace_id = ms.workspace_id
    where ms.source_field = 'CORPORATE_CARD'
    and ms.destination_field = 'VENDOR'
    and ms.workspace_id = ws.id
    and es.credit_card_expense_export_type = 'PURCHASE_INVOICE'
);