locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.profile
    Region      = var.region
  }

  s3_folders = [
    "inventory",
    "products",
    "shipments",
    "suppliers",
    "warehouses"
  ]
  s3_folders_in_raw = [ for folder in local.s3_folders : "raw/${folder}/" ]
}

