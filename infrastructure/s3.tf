resource "aws_s3_bucket" "SupplyChain360" {
    bucket = "supply-chain-360"

    tags = merge(local.common_tags,
    {
        Name = "${var.project_name}-s3"
    }
    )
}

resource "aws_s3_bucket_versioning" "SupplyChain360" {
    bucket = aws_s3_bucket.SupplyChain360.id

    versioning_configuration {
      status = "Enabled"
    }
}

resource "aws_s3_object" "folder" {
    for_each = toset(local.s3_folders_in_raw)
    bucket = aws_s3_bucket.SupplyChain360.id
    key = each.value
}

resource "aws_s3_account_public_access_block" "example" {
  block_public_acls   = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "s3_storage" {
  bucket = aws_s3_bucket.SupplyChain360.id

  rule {
    id     = "MoveStorage"
    status = "Enabled"

    transition {
      days          = 60
      storage_class = "GLACIER"
    }

    filter {
        prefix = "raw"
    }
  }
}