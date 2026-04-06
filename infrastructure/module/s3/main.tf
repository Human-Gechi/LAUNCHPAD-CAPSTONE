resource "aws_s3_bucket" "dest_bucket" {
  bucket = var.bucket_name
  tags   = var.common_tags
}

resource "aws_s3_object" "folders" {
  for_each = toset(var.s3_folders_in_raw)
  bucket   = aws_s3_bucket.dest_bucket.id
  key      = each.value
}

resource "aws_s3_bucket_versioning" "bucket_versioning" {
  bucket = aws_s3_bucket.dest_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_account_public_access_block" "bucket_restrictions" {
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "s3_storage" {
  bucket = aws_s3_bucket.dest_bucket.id

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