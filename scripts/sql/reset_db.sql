DROP FUNCTION if exists delete_workspace;

CREATE OR REPLACE FUNCTION delete_workspace(IN _workspace_id integer) RETURNS void AS $$
DECLARE
  rcount integer;
  _org_id varchar(255);
BEGIN
  RAISE NOTICE 'Deleting data from workspace % ', _workspace_id;

  DELETE
  FROM errors er
  where er.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % errors', rcount;

  DELETE
  FROM last_export_details l
  where l.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % last_export_details', rcount;
  
  DELETE
  FROM accounting_export_summary aes
  WHERE aes.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % accounting_export_summary', rcount;

  DELETE
  FROM dependent_field_settings dfs
  WHERE dfs.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % dependent_field_settings', rcount;

  DELETE
  FROM cost_category cc
  WHERE cc.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % cost_category', rcount;

  DELETE 
  FROM import_logs il
  WHERE il.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % import_logs', rcount;

  DELETE 
  FROM versions mv
  WHERE mv.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % versions', rcount;

  DELETE
  FROM purchase_invoice_lineitems pil
  WHERE pil.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % purchase_invoice_lineitems', rcount;

  DELETE
  FROM purchase_invoices pi
  WHERE pi.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % purchase_invoices', rcount;

  DELETE
  FROM expenses e
  WHERE e.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % expenses', rcount;

  DELETE
  FROM expenses 
  WHERE is_skipped=true and org_id in (SELECT org_id FROM workspaces WHERE id=_workspace_id);
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % skipped expenses', rcount;

  DELETE
  FROM accounting_exports_expenses aee
  WHERE aee.accountingexport_id IN (
      SELECT ae.id FROM accounting_exports ae WHERE ae.workspace_id = _workspace_id
  );
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % accounting_exports_expenses', rcount;

  DELETE
  FROM accounting_exports ae
  WHERE ae.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % accounting_exports', rcount;

  DELETE
  FROM employee_mappings em
  WHERE em.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % employee_mappings', rcount;

  DELETE
  FROM category_mappings cm
  WHERE cm.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % category_mappings', rcount;

  DELETE
  FROM mappings m
  WHERE m.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % mappings', rcount;

  DELETE
  FROM mapping_settings ms
  WHERE ms.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % mapping_settings', rcount;

  DELETE
  FROM export_settings es
  WHERE es.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % export_settings', rcount;

  DELETE
  FROM import_settings wis
  WHERE wis.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % import_settings', rcount;

  DELETE
  FROM advanced_settings was
  WHERE was.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % advanced_settings', rcount;

  DELETE
  FROM expense_fields ef
  WHERE ef.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % expense_fields', rcount;

  DELETE
  FROM fyle_credentials fc
  WHERE fc.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % fyle_credentials', rcount;

  DELETE
  FROM sage300_credentials sc
  WHERE sc.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % sage300_credentials', rcount;

  DELETE
  FROM expense_attributes ea
  WHERE ea.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % expense_attributes', rcount;

  DELETE
  FROM expense_filters ef
  WHERE ef.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % expense_filters', rcount;

  DELETE
  FROM destination_attributes da
  WHERE da.workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % destination_attributes', rcount;

  DELETE
  FROM django_q_schedule dqs
  WHERE dqs.args = _workspace_id::varchar(255);
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % django_q_schedule', rcount;

  DELETE
  FROM auth_tokens aut
  WHERE aut.user_id IN (
      SELECT u.id FROM users u WHERE u.id IN (
          SELECT wu.user_id FROM workspaces_user wu WHERE workspace_id = _workspace_id
      )
  );
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % auth_tokens', rcount;

  DELETE
  FROM workspaces_user wu
  WHERE workspace_id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % workspaces_user', rcount;

  DELETE
  FROM users u
  WHERE u.id IN (
      SELECT wu.user_id FROM workspaces_user wu WHERE workspace_id = _workspace_id
  );
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % users', rcount;

  DELETE
  FROM workspaces w
  WHERE w.id = _workspace_id;
  GET DIAGNOSTICS rcount = ROW_COUNT;
  RAISE NOTICE 'Deleted % workspaces', rcount;

  _org_id := (SELECT fyle_org_id FROM workspaces WHERE id = _workspace_id);


    RAISE NOTICE E'\n\n\n\n\n\n\n\n\nSwitch to prod db and run the below queries to delete dependent fields';
    RAISE NOTICE E'rollback;begin; delete from platform_schema.dependent_expense_field_mappings where expense_field_id in (select id from platform_schema.expense_fields where org_id =''%'' and type=''DEPENDENT_SELECT''); delete from platform_schema.expense_fields where org_id = ''%'' and type = ''DEPENDENT_SELECT'';\n\n\n\n\n\n\n\n\n\n\n', _org_id, _org_id;

RETURN;
END
$$ LANGUAGE plpgsql;
