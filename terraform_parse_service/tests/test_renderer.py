import shutil
import subprocess

import pytest

from renderer import render_s3_tf


def test_contains_required_blocks():
    tf = render_s3_tf("eu-west-1", "private", "tripla-bucket")
    assert 'provider "aws"' in tf
    assert 'resource "aws_s3_bucket" "bucket"' in tf
    assert 'resource "aws_s3_bucket_acl" "bucket"' in tf


def test_values_are_interpolated():
    tf = render_s3_tf("ap-northeast-1", "public-read", "my-bucket")
    assert 'region = "ap-northeast-1"' in tf
    assert 'bucket = "my-bucket"' in tf
    assert 'acl    = "public-read"' in tf


def test_acl_depends_on_ownership_controls():
    # Without ownership controls, aws_s3_bucket_acl fails on modern buckets
    # (BucketOwnerEnforced default disables ACLs entirely).
    tf = render_s3_tf("eu-west-1", "private", "tripla-bucket")
    assert 'resource "aws_s3_bucket_ownership_controls" "bucket"' in tf
    assert "depends_on = [aws_s3_bucket_ownership_controls.bucket]" in tf


@pytest.mark.skipif(shutil.which("terraform") is None, reason="terraform not installed")
def test_output_passes_terraform_validate(tmp_path):
    (tmp_path / "main.tf").write_text(
        render_s3_tf("eu-west-1", "private", "tripla-bucket")
    )
    subprocess.run(
        ["terraform", "init", "-backend=false", "-input=false"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    result = subprocess.run(
        ["terraform", "validate"], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr