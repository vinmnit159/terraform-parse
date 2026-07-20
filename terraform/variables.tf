variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "ap-northeast-1"
}

variable "project" {
  description = "Project slug used in resource names and tags."
  type        = string
  default     = "tripla"
}

variable "environment" {
  description = "Deployment environment; drives naming and tagging."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "cluster_name" {
  description = "EKS cluster name. Defaults to <project>-<environment> when empty."
  type        = string
  default     = ""
}

variable "cluster_version" {
  description = "Kubernetes version for the EKS control plane."
  type        = string
  default     = "1.31"
}

# No defaults on network inputs: an empty vpc_id/subnet_ids passes `plan`
# but explodes at `apply` with a confusing module error. Failing fast at
# input time is safer.
variable "vpc_id" {
  description = "ID of the pre-existing VPC to deploy the cluster into."
  type        = string

  validation {
    condition     = startswith(var.vpc_id, "vpc-")
    error_message = "vpc_id must be a valid VPC ID (vpc-...)."
  }
}

variable "subnet_ids" {
  description = "Private subnet IDs (at least two AZs) for the cluster and nodes."
  type        = list(string)

  validation {
    condition     = length(var.subnet_ids) >= 2 && alltrue([for s in var.subnet_ids : startswith(s, "subnet-")])
    error_message = "Provide at least two valid subnet IDs (subnet-...)."
  }
}

variable "node_instance_types" {
  description = "Instance types for the default managed node group."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_group_min_size" {
  description = "Minimum nodes in the default managed node group."
  type        = number
  default     = 1
}

variable "node_group_max_size" {
  description = "Maximum nodes in the default managed node group."
  type        = number
  default     = 3
}

variable "node_group_desired_size" {
  description = "Desired nodes in the default managed node group."
  type        = number
  default     = 2
}