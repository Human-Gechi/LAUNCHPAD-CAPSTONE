variable "supply_chain_360_oge" {
  description = "Name of the bucket"
  default     = "supply-chain-360-data"
}

variable "region" {
  description = "Region for Infra"
  type        = string
  default     = "eu-north-1"

}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "prod-SupplyChain360"

}

variable "team" {
  description = "Team in the Company"
  type        = string
  default     = "Data Engineering"

}

variable "environment" {
  description = "Environment"
  type        = string
  default     = "production"

}
variable "password_lenght" {
  description = "Length of the generated password"
  type        = number
  default     = 16
}

variable "iam_region" {
  description = "Region for Infra"
  type        = string
  default     = "eu-west-2"

}