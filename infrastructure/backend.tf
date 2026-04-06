terraform {
  backend "s3" {
    bucket       = "supply-chain-360-data"
    key          = "prod/terraform.tfstate"
    region       = "eu-north-1"
    use_lockfile = true
  }

}