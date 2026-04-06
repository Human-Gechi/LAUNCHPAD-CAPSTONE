output "snowflake_generated_password" {
  value     = random_password.snowflake_password.result
  sensitive = true

}

output "snowflake_user_name" {
  value = snowflake_user.new_user.name
}

output "snowflake_role_name" {
  value = snowflake_account_role.new_role.name
}

output "snowflake_database_name" {
  value = snowflake_database.db.name
}

output "snowflake_warehouse_name" {
  value = snowflake_warehouse.wh.name
}

output "raw_schema_name" {
  value = snowflake_schema.raw_schema.name
}

output "staging_schema_name" {
  value = snowflake_schema.staging_schema.name
}

output "intermediate_schema_name" {
  value = snowflake_schema.intermediate_schema.name
}

output "mart_schema_name" {
  value = snowflake_schema.mart_schema.name
}