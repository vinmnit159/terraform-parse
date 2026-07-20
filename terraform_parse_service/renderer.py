"""Return a complete, valid .tf document for the given S3 bucket.
"""

TF_TEMPLATE = """\
terraform {{
  required_version = ">= 1.5.0"

  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "{region}"
}}

resource "aws_s3_bucket" "bucket" {{
  bucket = "{bucket_name}"
}}

# ACLs require object ownership to allow them; without this block,
# aws_s3_bucket_acl fails on buckets created with BucketOwnerEnforced
# (the default since April 2023).
resource "aws_s3_bucket_ownership_controls" "bucket" {{
  bucket = aws_s3_bucket.bucket.id

  rule {{
    object_ownership = "BucketOwnerPreferred"
  }}
}}

resource "aws_s3_bucket_acl" "bucket" {{
  depends_on = [aws_s3_bucket_ownership_controls.bucket]

  bucket = aws_s3_bucket.bucket.id
  acl    = "{acl}"
}}
"""


def render_s3_tf(region: str, acl: str, bucket_name: str) -> str:
    """Return a complete, valid .tf document for the given S3 bucket.
    """
    return TF_TEMPLATE.format(region=region, acl=acl, bucket_name=bucket_name)