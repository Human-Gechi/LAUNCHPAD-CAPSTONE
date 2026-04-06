resource "random_password" "snowflake_password" {
  length  = var.password_lenght
  special = true
  upper   = true
  lower   = true
  numeric = true
}
data "aws_ssm_parameter" "my_organization" {
  name            = "/snowflake/organization"
  with_decryption = true
}

data "aws_ssm_parameter" "my_account" {
  name            = "/snowflake/account"
  with_decryption = true
}

data "aws_ssm_parameter" "my_username" {
  name            = "/snowflake/username"
  with_decryption = true
}

data "aws_ssm_parameter" "my_password" {
  name            = "/snowflake/password"
  with_decryption = true
}

provider "snowflake" {
  organization_name = data.aws_ssm_parameter.my_organization.value
  account_name      = data.aws_ssm_parameter.my_account.value
  user              = data.aws_ssm_parameter.my_username.value
  password          = data.aws_ssm_parameter.my_password.value
}

resource "snowflake_warehouse" "wh" {
  name           = "SUPPLYCHAIN360_WH"
  warehouse_size = "XSMALL"
  auto_suspend   = 60
  auto_resume    = true
}

resource "snowflake_database" "db" {
  name = "SUPPLYCHAIN360DB"
}

resource "snowflake_schema" "raw_schema" {
  name     = "RAW_SUPPLYCHAIN"
  database = snowflake_database.db.name
}

resource "snowflake_schema" "staging_schema" {
  name     = "STAGING_SUPPLYCHAIN"
  database = snowflake_database.db.name
}

resource "snowflake_schema" "intermediate_schema" {
  name     = "INTERMEDIATE_SUPPLYCHAIN"
  database = snowflake_database.db.name
}

resource "snowflake_schema" "mart_schema" {
  name     = "MARTS_SUPPLYCHAIN"
  database = snowflake_database.db.name
}

resource "snowflake_account_role" "new_role" {
  name = "SC_DATA_ENGINEER"
}

resource "snowflake_user" "new_user" {
  name         = "SC360_DATAENGINEER"
  password     = random_password.snowflake_password.result
  default_role = snowflake_account_role.new_role.name
}

resource "snowflake_grant_account_role" "grant_role_to_user" {
  role_name = snowflake_account_role.new_role.name
  user_name = snowflake_user.new_user.name
}

resource "snowflake_grant_privileges_to_account_role" "db_usage" {
  privileges        = ["USAGE"]
  account_role_name = snowflake_account_role.new_role.name
  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.db.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "warehouse_usage" {
  privileges        = ["USAGE"]
  account_role_name = snowflake_account_role.new_role.name
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.wh.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "all_schema_usage" {
  privileges        = ["USAGE"]
  account_role_name = snowflake_account_role.new_role.name
  on_schema {
    all_schemas_in_database = snowflake_database.db.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "create_schema" {
  privileges = ["CREATE SCHEMA"]
  account_role_name = snowflake_account_role.new_role.name
  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.db.name
  }

}

resource "snowflake_grant_privileges_to_account_role" "schema_create" {
  privileges        = ["CREATE TABLE", "CREATE VIEW"]
  account_role_name = snowflake_account_role.new_role.name
  on_schema {
    all_schemas_in_database = snowflake_database.db.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "current_table_DML" {
  privileges        = ["SELECT", "INSERT", "UPDATE", "TRUNCATE", "DELETE", "REFERENCES"]
  account_role_name = snowflake_account_role.new_role.name
  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_database        = snowflake_database.db.name
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "future_table_DML" {
  privileges        = ["SELECT", "INSERT", "UPDATE", "TRUNCATE", "DELETE", "REFERENCES"]
  account_role_name = snowflake_account_role.new_role.name
  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_database        = snowflake_database.db.name
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "future_views_DML" {
  privileges        = ["SELECT", "INSERT", "UPDATE", "TRUNCATE", "DELETE", "REFERENCES"]
  account_role_name = snowflake_account_role.new_role.name
  on_schema_object {
    future {
      object_type_plural = "VIEWS"
      in_database        = snowflake_database.db.name
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "current_views_DML" {
  privileges        = ["SELECT", "INSERT", "UPDATE", "TRUNCATE", "DELETE", "REFERENCES"]
  account_role_name = snowflake_account_role.new_role.name
  on_schema_object {
    all {
      object_type_plural = "VIEWS"
      in_database        = snowflake_database.db.name
    }
  }
}