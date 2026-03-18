terraform {
  backend "s3" {
    bucket = "SupplyChain360"
    key = "env/key/terraform.tfstate"
    region = "eu-north-1"
    use_lockfile = true
    profile = "dev-Supply-Chain"
  }
}