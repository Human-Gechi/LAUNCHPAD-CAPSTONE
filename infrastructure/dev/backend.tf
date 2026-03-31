terraform {
  backend "s3" {
    bucket = "supplychain-test-bucket"
    key = "dev/terraform.tfstate"
    region = "eu-north-1"
    use_lockfile = true
    profile = "dev-Supply-Chain"
  }

}