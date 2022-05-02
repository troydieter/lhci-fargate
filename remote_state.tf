terraform {
  backend "s3" {
    bucket               = "troydieter.com-tfstate"
    key                  = "lhci-fargate.tfstate"
    workspace_key_prefix = "lhci-fargate-tfstate"
    region               = "us-east-1"
    dynamodb_table       = "td-tf-lockstate"
  }
}
