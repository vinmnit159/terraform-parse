"""Render validated payload properties into Terraform HCL for an S3 bucket.

Pure functions only: no I/O, no Flask imports. This keeps rendering trivially
unit-testable and reusable outside the HTTP layer.
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

resource "aws_s3_bucket" "this" {{
  bucket = "{bucket_name}"
}}

# ACLs require object ownership to allow them; without this block,
# aws_s3_bucket_acl fails on buckets created with BucketOwnerEnforced
# (the default since April 2023).
resource "aws_s3_bucket_ownership_controls" "this" {{
  bucket = aws_s3_bucket.this.id

  rule {{
    object_ownership = "BucketOwnerPreferred"
  }}
}}

resource "aws_s3_bucket_acl" "this" {{
  depends_on = [aws_s3_bucket_ownership_controls.this]

  bucket = aws_s3_bucket.this.id
  acl    = "{acl}"
}}
"""


def render_s3_tf(region: str, acl: str, bucket_name: str) -> str:
    """Return a complete, valid .tf document for the given S3 bucket.

    Inputs are assumed to be already validated (see validators.py); values
    are interpolated into a fixed template, never into arbitrary HCL.
    """
    return TF_TEMPLATE.format(region=region, acl=acl, bucket_name=bucket_name)