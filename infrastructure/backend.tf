terraform {
  backend "s3" {
    bucket = "supply-chain-360"
    key = "prod/terraform.tfstate"
    region = "eu-north-1"
    use_lockfile = true
  }

}