"""Validate the incoming request payload before any rendering happens.

Every failure raises ValidationError with a message safe to return to the
client. Validation is strict: unknown ACLs, malformed bucket names, or
suspicious regions are rejected rather than passed through to Terraform,
where they would fail later (or worse, succeed with something unintended).
"""

import re

# Canned bucket ACLs accepted by aws_s3_bucket_acl.
# https://docs.aws.amazon.com/AmazonS3/latest/userguide/acl-overview.html#canned-acl
ALLOWED_ACLS = frozenset(
    {
        "private",
        "public-read",
        "public-read-write",
        "authenticated-read",
        "log-delivery-write",
    }
)

# Standard AWS region shape: "eu-west-1", "ap-northeast-1", "us-gov-west-1".
REGION_RE = re.compile(r"^[a-z]{2}(-gov)?-[a-z]+-\d$")

# S3 bucket naming rules (subset): 3-63 chars, lowercase letters, digits,
# dots and hyphens; must start/end with letter or digit.
# https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html
BUCKET_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")
IP_LIKE_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

REQUIRED_PROPERTIES = ("aws-region", "acl", "bucket-name")


class ValidationError(Exception):
    """Payload failed validation; str(exc) is a client-safe message."""


def validate_payload(body: object) -> tuple[str, str, str]:
    """Validate the full request body, returning (region, acl, bucket_name).

    Expected shape:
        {"payload": {"properties": {"aws-region": ..., "acl": ..., "bucket-name": ...}}}
    """
    if not isinstance(body, dict):
        raise ValidationError("request body must be a JSON object")

    payload = body.get("payload")
    if not isinstance(payload, dict):
        raise ValidationError("missing or invalid 'payload' object")

    properties = payload.get("properties")
    if not isinstance(properties, dict):
        raise ValidationError("missing or invalid 'payload.properties' object")

    missing = [key for key in REQUIRED_PROPERTIES if key not in properties]
    if missing:
        raise ValidationError(f"missing properties: {', '.join(missing)}")

    for key in REQUIRED_PROPERTIES:
        if not isinstance(properties[key], str) or not properties[key].strip():
            raise ValidationError(f"property '{key}' must be a non-empty string")

    region = properties["aws-region"].strip()
    acl = properties["acl"].strip()
    bucket_name = properties["bucket-name"].strip()

    if not REGION_RE.match(region):
        raise ValidationError(f"'{region}' does not look like a valid AWS region")

    if acl not in ALLOWED_ACLS:
        raise ValidationError(
            f"acl should be one of: {', '.join(sorted(ALLOWED_ACLS))}"
        )

    if not BUCKET_RE.match(bucket_name):
        raise ValidationError(
            "bucket-name must be 3-63 chars of lowercase letters, digits, "
            "dots or hyphens, starting and ending with a letter or digit"
        )
    if ".." in bucket_name or IP_LIKE_RE.match(bucket_name):
        raise ValidationError(
            "bucket-name must not contain consecutive dots or look like an IP address"
        )

    return region, acl, bucket_name