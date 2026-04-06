output "state_bucket_id" {
  value       = aws_s3_bucket.terraform_state.id
  description = "S3 bucket name for Terraform state"

}

output "state_bucket_region" {
  value       = aws_s3_bucket.terraform_state.region
  description = "S3 bucket region"

}

output "state_bucket_arn" {
  value       = aws_s3_bucket.terraform_state.arn
  description = "S3 bucket ARN"

}
