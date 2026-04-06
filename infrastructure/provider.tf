provider "aws" {
  region = var.region
}

provider "aws" {
  alias  = "default"
  region = var.iam_region
  profile = "source"
}