variable "compartment_id" {
  description = "OCI compartment used for the Weather Intelligence Platform"
  type        = string
  default     = "ocid1.tenancy.oc1..aaaaaaaarhdmxiuer7rn7aasjzq2xv2d5jotqnghsgsdggmzzqevav5pimya"
}


variable "aws_region" {
  description = "AWS region containing the Weather Intelligence Platform S3 bucket"
  type        = string
  default     = "eu-west-2"
}