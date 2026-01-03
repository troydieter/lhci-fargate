import os
import aws_cdk as cdk
from aws_cdk import RemovalPolicy
from aws_cdk.aws_certificatemanager import Certificate, CertificateValidation
from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_efs as efs,
    aws_iam as iam,
    aws_wafv2 as wafv2,
)
from aws_cdk.aws_route53 import HostedZone
from cdk_watchful import Watchful


class LHCIStack(cdk.Stack):
    def __init__(self, scope: cdk.App, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # VPC configuration
        vpc = ec2.Vpc(
            self, 
            "lhcivpc",
            ip_addresses=ec2.IpAddresses.cidr(
                self.node.try_get_context("fargate_vpc_cidr")
            )
        )
