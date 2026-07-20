locals {
  cluster_name = var.cluster_name != "" ? var.cluster_name : "${var.project}-${var.environment}"
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = local.cluster_name
  cluster_version = var.cluster_version
  vpc_id          = var.vpc_id
  subnet_ids      = var.subnet_ids

  # v19+ renamed `node_groups` to `eks_managed_node_groups`; the old key
  # was silently ignored, producing a cluster with zero worker nodes.
  eks_managed_node_groups = {
    default = {
      instance_types = var.node_instance_types
      min_size       = var.node_group_min_size
      max_size       = var.node_group_max_size
      desired_size   = var.node_group_desired_size
    }
  }
}

# S3 bucket names are globally unique, so the name must vary per environment.
resource "aws_s3_bucket" "static_assets" {
  bucket = "${var.project}-static-assets-${var.environment}"
}

resource "aws_s3_bucket_public_access_block" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}