environment = "dev"
aws_region  = "ap-northeast-1"

# Pre-existing network (see NOTES.md — VPC creation is intentionally out of
# scope; these are consumed as inputs).
vpc_id     = "vpc-00000000000000000"
subnet_ids = ["subnet-00000000000000001", "subnet-00000000000000002"]

node_instance_types     = ["t3.medium"]
node_group_min_size     = 1
node_group_max_size     = 3
node_group_desired_size = 2