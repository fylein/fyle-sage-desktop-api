rollback;
begin;

select COUNT(*) from cost_category cs 
inner join dependent_field_settings dfs 
on cs.workspace_id = dfs.workspace_id
where cs.updated_at >= dfs.last_successful_import_at 
and cs.is_imported = 'f';

update cost_category cs
set is_imported = 't'
from dependent_field_settings dfs
where cs.workspace_id = dfs.workspace_id
and cs.updated_at >= dfs.last_successful_import_at
and cs.is_imported = 'f';