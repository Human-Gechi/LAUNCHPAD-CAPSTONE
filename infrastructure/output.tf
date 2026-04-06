output "generated_password" {
  value     = random_password.dynamic_password.result
  sensitive = true

}

output "my_access_key_id" {
  value = aws_iam_access_key.DE_access_key.id
}

output "my_secret_access_key" {
  value     = aws_iam_access_key.DE_access_key.secret
  sensitive = true
}

output "db_name" {
  value     = aws_ssm_parameter.db_name.value
  sensitive = true
}

output "db_host" {
  value     = aws_ssm_parameter.db_host.value
  sensitive = true
}

output "db_password" {
  value     = aws_ssm_parameter.db_password.value
  sensitive = true
}

output "db_user" {
  value     = aws_ssm_parameter.db_user.value
  sensitive = true
}

output "db_port" {
  value     = aws_ssm_parameter.db_port.value
  sensitive = true
}

output "bucket_name" {
  value = module.s3.bucket_name
}

output "bucket_arn" {
  value = module.s3.bucket_arn
}

output "snowflake_generated_password" {
  value     = module.snowflake.snowflake_generated_password
  sensitive = true

}

output "snowflake_user_name" {
  value = module.snowflake.snowflake_user_name
}

output "snowflake_role_name" {
  value = module.snowflake.snowflake_role_name
}

output "snowflake_database_name" {
  value = module.snowflake.snowflake_database_name
}

output "snowflake_warehouse_name" {
  value = module.snowflake.snowflake_warehouse_name
}

output "raw_schema_name" {
  value = module.snowflake.raw_schema_name
}

output "staging_schema_name" {
  value = module.snowflake.staging_schema_name
}

output "intermediate_schema_name" {
  value = module.snowflake.intermediate_schema_name
}

output "mart_schema_name" {
  value = module.snowflake.mart_schema_name
}