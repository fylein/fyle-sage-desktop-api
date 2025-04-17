# fyle-sage-desktop-api
API to connect to Sage Desktop Products

* ### Adding a New View, Function, or Trigger:
    Follow these steps to ensure your changes are applied correctly:

    1. **Make changes** in the [`fyle-integrations-db-migrations`](https://github.com/fylein/fyle-integrations-db-migrations) repository.
    2. **Update the submodule** in the Sage300 API:
        ```bash
        git submodule init
        git submodule update
        ```
    3. **Enter the Sage300 API container**:
        ```bash
        enter sage-desktop-api
        ```
    4. **Generate a migration file** using the provided convenient command:
        ```bash
        python3 manage.py create_sql_migration <file-path1>
        ```
        - Replace `<file-path1>` with the relative path to your SQL file from the fyle-integrations-db-migrations folder.
        - The migration will always be created in the `internal` app.

        **Example:**
        ```bash
        python3 manage.py create_sql_migration fyle-integrations-db-migrations/sage300/functions/delete_workspace.sql
        ```

    5. **Review the newly generated migration file**:
        Navigate to the `apps/internal/migrations/` directory and ensure the migration file content is as expected.

    6. **Restart the Sage300 API service and apply the migration**:
        ```bash
        restart sage-desktop-api
        logs sage-desktop-api
        ```
        Confirm in the logs that the migration has been applied successfully.