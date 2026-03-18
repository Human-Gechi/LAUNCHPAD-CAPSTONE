locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.profile
    Region      = var.region
  }
}