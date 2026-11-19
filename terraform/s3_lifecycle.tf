resource "aws_s3_bucket_lifecycle_configuration" "mlops_lifecycle" {
  bucket = aws_s3_bucket.weather_data_lake.id

  rule {
    id     = "expire-old-w8-model-versions"
    status = "Enabled"

    filter {
      prefix = "models/"
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }

  rule {
    id     = "expire-old-spark-dev-model-versions"
    status = "Enabled"

    filter {
      prefix = "mllib/dev/models/"
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }

  rule {
    id     = "expire-old-spark-prod-model-versions"
    status = "Enabled"

    filter {
      prefix = "mllib/prod/models/"
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}
