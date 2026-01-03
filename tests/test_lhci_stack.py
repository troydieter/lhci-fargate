import aws_cdk as cdk
from aws_cdk import assertions
from lhci_stack import LHCIStack


def test_lhci_stack_created():
    """Test that LHCIStack can be instantiated successfully."""
    app = cdk.App()
    stack = LHCIStack(app, "TestStack")
    template = assertions.Template.from_stack(stack)
    
    # Verify VPC is created
    template.resource_count_is("AWS::EC2::VPC", 1)
    
    # Verify ECS Cluster is created
    template.resource_count_is("AWS::ECS::Cluster", 1)
    
    # Verify EFS FileSystem is created
    template.resource_count_is("AWS::EFS::FileSystem", 1)
    
    # Verify Fargate Service is created
    template.resource_count_is("AWS::ECS::Service", 1)
    
    # Verify Application Load Balancer is created
    template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)
