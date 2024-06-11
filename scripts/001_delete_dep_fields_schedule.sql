rollback;
begin;

delete from django_q_schedule where func = 'apps.mappings.imports.tasks.auto_import_and_map_fyle_fields';