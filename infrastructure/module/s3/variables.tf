variable "bucket_name" {
  type = string
}

variable "common_tags" {
  type = map(string)
}

variable "s3_folders_in_raw" {
  type = list(string)
}