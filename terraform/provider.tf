provider "oci" {
  config_file_profile = "DEFAULT"
}

provider "aws" {
  region = var.aws_region
}