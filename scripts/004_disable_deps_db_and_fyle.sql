/*
Script to disable Cost Code and Cost Category
Future Modifications:
    1. Add Project Name/Id if specific Cost Code are to be deleted.
    2. Add Cost Code Name/Id and Project Name/Id if specific Cost Category are to be deleted.

CSV Template for Cost Code:
    cost_code_name
CSV Template for Cost Category:
    cost_category_name

Steps for Cost Code:
1. Create a temp table to store the data from the CSV
2. Copy the data from the CSV to the temp table
3. Delete the Cost Code from destination_attributes
4. Delete the Cost Category having the Cost Code as the mentioned Cost Code
5. Delete from the fyle dependent_fields_values table where expense_field_value is the Cost Code
6. Delete from the fyle dependent_fields_values table where parent_expense_field_value is the Cost Code

Steps for Cost Category:
1. Create a temp table to store the data from the CSV
2. Copy the data from the CSV to the temp table
3. Delete from the Cost Category table where Cost Category is the mentioned Cost Category
4. Delete from the fyle dependent_fields_values table where expense_field_value is the Cost Category
*/

------ Cost Code ------
rollback;
begin;

create temp table temp_cost_code (
    cost_code_name TEXT
);

--- update the path here
\copy temp_cost_code (cost_code_name)
from '/Users/hrishabh/Desktop/cost_code_org_name.csv' WITH CSV HEADER;

--- update the workspace id here
delete from destination_attributes
where attribute_type = 'COST_CODE'
and value in (
    select cost_code_name from temp_cost_code
) and workspace_id = _workspace_id;

--- update the workspace id here
delete from cost_category
where cost_code_name in (
    select cost_code_name from temp_cost_code
)
and workspace_id = _workspace_id;

---- Fyle DB ----
--- update the org id here
delete from platform_schema.dependent_expense_field_values 
where expense_field_value in (
    select cost_code_name from temp_cost_code
)
and org_id = _org_id;

--- update the org id here
rollback;
begin;

delete from platform_schema.dependent_expense_field_values 
where parent_expense_field_value in (
    select cost_code_name from temp_cost_code
)
and org_id = _org_id;


----- Cost Category ------
rollback;
begin;

create temp table temp_cost_category (
    cost_category_name TEXT
);

--- update the path here
\copy temp_cost_category (cost_category_name)
from '/Users/hrishabh/Desktop/cost_category_org_name.csv' WITH CSV HEADER;

--- update the workspace id here
delete from cost_category
where name in (
    select cost_category_name from temp_cost_category
)
and workspace_id = _workspace_id;

---- Fyle DB ----
--- update the org id here
rollback;
begin;

delete from platform_schema.dependent_expense_field_values 
where expense_field_value in (
    select cost_category_name from temp_cost_category
)
and org_id = _org_id;