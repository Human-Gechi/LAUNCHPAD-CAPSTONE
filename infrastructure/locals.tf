locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Region      = var.region
    Team        = var.team
  }

  s3_folders = [
    "inventory",
    "products",
    "shipments",
    "suppliers",
    "warehouses",
    "stores",
    "transactions"
  ]
  s3_folders_in_raw = [for folder in local.s3_folders : "raw/${folder}/"]
}

