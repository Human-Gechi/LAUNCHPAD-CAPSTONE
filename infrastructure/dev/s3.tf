resource "aws_s3_bucket" "SupplyChain360" {
    bucket = "supplychain-test-bucket"

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
