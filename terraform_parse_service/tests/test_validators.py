import pytest

from validators import ValidationError, validate_payload


def make_body(region="eu-west-1", acl="private", bucket="tripla-bucket"):
    return {
        "payload": {
            "properties": {
                "aws-region": region,
                "acl": acl,
                "bucket-name": bucket,
            }
        }
    }


def test_valid_payload_returns_values():
    assert validate_payload(make_body()) == ("eu-west-1", "private", "tripla-bucket")


def test_values_are_stripped():
    body = make_body(region=" eu-west-1 ", bucket=" tripla-bucket ")
    assert validate_payload(body) == ("eu-west-1", "private", "tripla-bucket")


@pytest.mark.parametrize("body", [None, [], "text", 42])
def test_non_object_body_rejected(body):
    with pytest.raises(ValidationError, match="JSON object"):
        validate_payload(body)


def test_missing_payload_key():
    with pytest.raises(ValidationError, match="'payload'"):
        validate_payload({"properties": {}})


def test_missing_properties_key():
    with pytest.raises(ValidationError, match="'payload.properties'"):
        validate_payload({"payload": {}})


def test_missing_properties_are_named():
    body = {"payload": {"properties": {"acl": "private"}}}
    with pytest.raises(ValidationError, match="aws-region, bucket-name"):
        validate_payload(body)


@pytest.mark.parametrize("value", ["", "   ", 3, None, ["eu-west-1"]])
def test_non_string_or_empty_property_rejected(value):
    with pytest.raises(ValidationError, match="non-empty string"):
        validate_payload(make_body(region=value))


@pytest.mark.parametrize("region", ["euwest1", "EU-WEST-1", "eu-west", "eu-west-11"])
def test_invalid_region_rejected(region):
    with pytest.raises(ValidationError, match="valid AWS region"):
        validate_payload(make_body(region=region))


def test_gov_region_accepted():
    region, _, _ = validate_payload(make_body(region="us-gov-west-1"))
    assert region == "us-gov-west-1"


@pytest.mark.parametrize("acl", ["Private", "public", "bucket-owner-full-control"])
def test_unknown_acl_rejected(acl):
    with pytest.raises(ValidationError, match="acl must be one of"):
        validate_payload(make_body(acl=acl))


@pytest.mark.parametrize(
    "bucket",
    [
        "ab",                # too short
        "a" * 64,            # too long
        "Tripla-Bucket",     # uppercase
        "-tripla",           # leading hyphen
        "tripla-",           # trailing hyphen
        "tripla_bucket",     # underscore
        "tripla..bucket",    # consecutive dots
        "192.168.1.1",       # IP-like
    ],
)
def test_invalid_bucket_names_rejected(bucket):
    with pytest.raises(ValidationError):
        validate_payload(make_body(bucket=bucket))


@pytest.mark.parametrize("bucket", ["abc", "a" * 63, "tripla.bucket-1"])
def test_valid_bucket_names_accepted(bucket):
    _, _, name = validate_payload(make_body(bucket=bucket))
    assert name == bucket