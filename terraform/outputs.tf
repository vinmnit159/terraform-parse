output "cluster_name" {
  description = "EKS cluster name."
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS API server endpoint."
  value       = module.eks.cluster_endpoint
}

output "static_assets_bucket" {
  description = "Name of the static assets bucket."
  value       = aws_s3_bucket.static_assets.id
}