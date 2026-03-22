locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.profile
    Region      = var.region
    Team        = "Data Engineering"
  }

  s3_folders = [
    "inventory",
    "products",
    "shipments",
    "suppliers",
    "warehouses",
    "locations",
    "transactions"
  ]
  s3_folders_in_raw = [ for folder in local.s3_folders : "raw/${folder}/" ]
}

