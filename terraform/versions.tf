terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state is required for team use and multiple environments; left
  # commented because this assignment has no live AWS account to apply
  # against. Uncomment and `terraform init -migrate-state` per environment.
  #
  # backend "s3" {
  #   bucket         = "tripla-terraform-state"
  #   key            = "eks/terraform.tfstate"   # override per env via -backend-config
  #   region         = "ap-northeast-1"
  #   dynamodb_table = "terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project
      ManagedBy   = "terraform"
    }
  }
}