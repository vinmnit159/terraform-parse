environment = "prod"
aws_region  = "ap-northeast-1"

vpc_id     = "vpc-00000000000000000"
subnet_ids = ["subnet-00000000000000001", "subnet-00000000000000002", "subnet-00000000000000003"]

node_instance_types     = ["m6i.large"]
node_group_min_size     = 2
node_group_max_size     = 6
node_group_desired_size = 3