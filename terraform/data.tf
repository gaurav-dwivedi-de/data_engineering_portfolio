data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

resource "aws_s3_bucket" "weather_data_lake" {
  bucket = "weather-data-lake-mlops"
}

resource "aws_s3_bucket_public_access_block" "weather_data_lake" {
  bucket = aws_s3_bucket.weather_data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}