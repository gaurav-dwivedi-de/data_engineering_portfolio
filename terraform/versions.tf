terraform {
  required_version = ">= 1.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0"
    }

    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0"
    }
  }
}