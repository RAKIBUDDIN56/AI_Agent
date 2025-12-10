Database Configuration

This section defines database connectivity:

DefaultDbContext sets the database context. Could be PostgreSQL, MSSQL, etc.

CheckTablePermission set to false disables table-level permission checks.

DynamicViewModelHandlers registers handlers such as UpdateCommonFields to automate metadata updates.

You can extend this by implementing custom handlers for audit logs, validation, or computed properties.