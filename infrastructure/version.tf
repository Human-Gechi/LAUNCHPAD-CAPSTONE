terraform {
  required_version = ">=1.14.0"

  required_providers {
    aws = {
      source = "hashicorp/aws"

      version = "~>6.0"
    }

    local = {
      source = "hashicorp/local"

      version = "~>2.0"
    }

    random = {
      source = "hashicorp/random"

      version = "~>3.8.1"
    }

    snowflake = {
      source = "snowflakedb/snowflake"

      version = "~>2.14"
    }

    tls = {
      source = "hashicorp/tls"

      version = "~>4.2.1"
    }
  }
}