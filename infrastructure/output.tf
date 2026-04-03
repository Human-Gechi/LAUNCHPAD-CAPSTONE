output "generated_password" {
    value = random_password.dynamic_password.result
    sensitive = true

}

output "access_key_id" {
  value = aws_iam_access_key.DE_access_key.id
}

output "secret_access_key" {
  value     = aws_iam_access_key.DE_access_key.secret
  sensitive = true
}