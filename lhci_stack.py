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
        
        # ECS Cluster
        ecs_cluster = ecs.Cluster(self, "LHCIECSCluster", vpc=vpc)
        
        # EFS FileSystem
        file_system = efs.FileSystem(
            self,
            "LHCIEfsFileSystem",
            vpc=vpc,
            encrypted=True,
            lifecycle_policy=efs.LifecyclePolicy.AFTER_14_DAYS,
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            throughput_mode=efs.ThroughputMode.BURSTING,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # EFS AccessPoint
        access_point = efs.AccessPoint(
            self,
            "AccessPoint",
            file_system=file_system
        )
        
        # Volume name for EFS mount
        volume_name = "efs-volume"
        
        # Fargate Task Definition
        task_def = ecs.FargateTaskDefinition(
            self,
            "LHCITaskDef",
            cpu=512,
            memory_limit_mib=1024
        )
        
        # Add EFS volume to task definition
        task_def.add_volume(
            name=volume_name,
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=file_system.file_system_id,
                transit_encryption="ENABLED",
                authorization_config=ecs.AuthorizationConfig(
                    access_point_id=access_point.access_point_id,
                    iam="ENABLED"
                )
            )
        )
        
        # Container Definition
        container_def = ecs.ContainerDefinition(
            self,
            "LHCIContainerDef",
            image=ecs.ContainerImage.from_registry("patrickhulce/lhci-server:latest"),
            task_definition=task_def
        )
        
        # Add mount points
        container_def.add_mount_points(
            ecs.MountPoint(
                container_path="/data",
                source_volume=volume_name,
                read_only=False
            )
        )
        
        # Add port mappings
        container_def.add_port_mappings(
            ecs.PortMapping(container_port=9001)
        )
        
        # Route53 HostedZone lookup
        lhci_domain_zone_name = HostedZone.from_lookup(
            self,
            "lhci_domain_zone_name",
            domain_name=self.node.try_get_context("lhci_domain_zone_name")
        )
        
        # ACM Certificate with DNS validation
        cert = Certificate(
            self,
            "certificate",
            domain_name=self.node.try_get_context("lhci_domain_name"),
            validation=CertificateValidation.from_dns(lhci_domain_zone_name)
        )
        
        # Application Load Balanced Fargate Service
        alb_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "Service01",
            cluster=ecs_cluster,
            task_definition=task_def,
            desired_count=2,
            listener_port=443,
            certificate=cert,
            redirect_http=True,
            domain_name=self.node.try_get_context("lhci_domain_name"),
            domain_zone=lhci_domain_zone_name
        )
        
        # Load balancer reference
        lhcilb = alb_fargate_service.load_balancer
        
        # Auto-scaling configuration
        scalable_target = alb_fargate_service.service.auto_scale_task_count(
            min_capacity=2,
            max_capacity=4
        )
        
        # CPU-based auto-scaling
        scalable_target.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=75
        )
        
        # Target group configuration
        alb_fargate_service.target_group.set_attribute(
            "deregistration_delay.timeout_seconds",
            "30"
        )
        
        # Health check configuration
        alb_fargate_service.target_group.configure_health_check(
            healthy_http_codes=self.node.try_get_context("lhci_health_check_port")
        )
