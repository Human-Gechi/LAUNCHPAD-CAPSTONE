module "s3" {
  source            = "./module/s3"
  bucket_name       = var.supply_chain_360_oge
  common_tags       = local.common_tags
  s3_folders_in_raw = local.s3_folders_in_raw
}

module "snowflake" {
  source = "./module/snowflake"
  password_lenght = 16
}
data "aws_ssm_parameter" "db_name" {
  provider        = aws.default
  name            = "/supplychain360/db/dbname"
  with_decryption = true
}

data "aws_ssm_parameter" "db_host" {
  provider        = aws.default
  name            = "/supplychain360/db/host"
  with_decryption = true
}

data "aws_ssm_parameter" "db_password" {
  provider        = aws.default
  name            = "/supplychain360/db/password"
  with_decryption = true
}

data "aws_ssm_parameter" "db_user" {
  provider        = aws.default
  name            = "/supplychain360/db/user"
  with_decryption = true
}

data "aws_ssm_parameter" "db_port" {
  provider        = aws.default
  name            = "/supplychain360/db/port"
  with_decryption = true
}


resource "aws_ssm_parameter" "db_name" {
  name      = "/supplychain360/db/dbname"
  type      = "String"
  value     = data.aws_ssm_parameter.db_name.value
  overwrite = true
}

resource "aws_ssm_parameter" "db_host" {
  name      = "/supplychain360/db/host"
  type      = "String"
  value     = data.aws_ssm_parameter.db_host.value
  overwrite = true
}

resource "aws_ssm_parameter" "db_password" {
  name      = "/supplychain360/db/password"
  type      = "SecureString"
  value     = data.aws_ssm_parameter.db_password.value
  overwrite = true
}

resource "aws_ssm_parameter" "db_user" {
  name      = "/supplychain360/db/user"
  type      = "String"
  value     = data.aws_ssm_parameter.db_user.value
  overwrite = true
}

resource "aws_ssm_parameter" "db_port" {
  name      = "/supplychain360/db/port"
  type      = "SecureString"
  value     = data.aws_ssm_parameter.db_port.value
  overwrite = true
}
