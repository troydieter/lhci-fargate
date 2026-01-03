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
    aws_logs as logs,
    aws_wafv2 as wafv2,
)
from aws_cdk.aws_route53 import HostedZone
from cdk_watchful import Watchful
import config


class LHCIStack(cdk.Stack):
    def __init__(self, scope: cdk.App, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Apply common tags to all resources
        cdk.Tags.of(self).add("Project", "LHCI-Fargate")
        cdk.Tags.of(self).add("Environment", "Production")
        cdk.Tags.of(self).add("Owner", self.node.try_get_context("lhci_mon_email") or "admin")
        cdk.Tags.of(self).add("CostCenter", "Engineering")
        cdk.Tags.of(self).add("ManagedBy", "CDK")

        # Validate required context values
        required_context = [
            "fargate_vpc_cidr",
            "lhci_domain_name", 
            "lhci_domain_zone_name",
            "lhci_mon_email"
        ]
        
        for key in required_context:
            if not self.node.try_get_context(key):
                raise ValueError(f"Required context value '{key}' is missing from cdk.json")

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
            cpu=config.FARGATE_CPU,
            memory_limit_mib=config.FARGATE_MEMORY_MB
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
            image=ecs.ContainerImage.from_registry(config.LHCI_CONTAINER_IMAGE),
            task_definition=task_def,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="lhci",
                log_retention=logs.RetentionDays.ONE_MONTH
            ),
            environment=config.CONTAINER_ENVIRONMENT,
            user=config.LHCI_CONTAINER_USER,
            readonly_root_filesystem=False  # Required for LHCI to write temp files
        )
        
        # Add mount points
        container_def.add_mount_points(
            ecs.MountPoint(
                container_path=config.EFS_MOUNT_PATH,
                source_volume=volume_name,
                read_only=False
            )
        )
        
        # Add port mappings
        container_def.add_port_mappings(
            ecs.PortMapping(container_port=config.LHCI_CONTAINER_PORT)
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
            desired_count=1,  # Start lean with 1 instance
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
            min_capacity=config.MIN_CAPACITY,
            max_capacity=config.MAX_CAPACITY
        )
        
        # CPU-based auto-scaling
        scalable_target.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=config.CPU_TARGET_UTILIZATION,
            scale_in_cooldown=cdk.Duration.minutes(config.SCALE_IN_COOLDOWN_MINUTES),
            scale_out_cooldown=cdk.Duration.minutes(config.SCALE_OUT_COOLDOWN_MINUTES)
        )
        
        # Memory-based auto-scaling
        scalable_target.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=config.MEMORY_TARGET_UTILIZATION,
            scale_in_cooldown=cdk.Duration.minutes(config.SCALE_IN_COOLDOWN_MINUTES),
            scale_out_cooldown=cdk.Duration.minutes(config.SCALE_OUT_COOLDOWN_MINUTES)
        )
        
        # Target group configuration
        alb_fargate_service.target_group.set_attribute(
            "deregistration_delay.timeout_seconds",
            "30"
        )
        
        # Health check configuration
        alb_fargate_service.target_group.configure_health_check(
            healthy_http_codes=config.HEALTH_CHECK_CODES,
            path=config.HEALTH_CHECK_PATH,
            interval=cdk.Duration.seconds(config.HEALTH_CHECK_INTERVAL_SECONDS),
            timeout=cdk.Duration.seconds(config.HEALTH_CHECK_TIMEOUT_SECONDS),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3
        )
        
        # Override Platform version (until Latest = 1.4.0)
        alb_fargate_service_resource = alb_fargate_service.service.node.find_child("Service")
        alb_fargate_service_resource.add_property_override("PlatformVersion", "1.4.0")
        
        # Allow access to EFS from Fargate ECS
        file_system.connections.allow_default_port_from(alb_fargate_service.service.connections)
        
        # IAM policy for EFS access
        task_def.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    "elasticfilesystem:ClientRootAccess",
                    "elasticfilesystem:ClientWrite",
                    "elasticfilesystem:ClientMount",
                    "elasticfilesystem:DescribeMountTargets"
                ],
                resources=[
                    f"arn:aws:elasticfilesystem:{os.environ.get('CDK_DEFAULT_REGION')}:{os.environ.get('CDK_DEFAULT_ACCOUNT')}:file-system/{file_system.file_system_id}"
                ]
            )
        )
        
        # IAM policy for EC2 describe permissions
        task_def.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=["ec2:DescribeAvailabilityZones"],
                resources=["*"]
            )
        )
        
        # WAF v2 WebACL with managed rules
        web_acl = wafv2.CfnWebACL(
            self,
            "web-acl",
            default_action={"allow": {}},
            scope="REGIONAL",
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="webACL",
                sampled_requests_enabled=True
            ),
            rules=[
                wafv2.CfnWebACL.RuleProperty(
                    name="AWS-AWSManagedRulesCommonRuleSet",
                    priority=1,
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(
                        none={}
                    ),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            name="AWSManagedRulesCommonRuleSet",
                            vendor_name="AWS",
                            excluded_rules=[
                                wafv2.CfnWebACL.ExcludedRuleProperty(name="CrossSiteScripting_BODY"),
                                wafv2.CfnWebACL.ExcludedRuleProperty(name="NoUserAgent_HEADER"),
                                wafv2.CfnWebACL.ExcludedRuleProperty(name="SizeRestrictions_BODY"),
                                wafv2.CfnWebACL.ExcludedRuleProperty(name="UserAgent_BadBots_HEADER")
                            ]
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="awsCommonRules",
                        sampled_requests_enabled=True
                    )
                )
            ]
        )
        
        # WAF WebACL Association
        wafv2.CfnWebACLAssociation(
            self,
            "web-acl-association",
            web_acl_arn=web_acl.attr_arn,
            resource_arn=lhcilb.load_balancer_arn
        )
        
        # Watchful monitoring
        wf = Watchful(
            self,
            "watchful",
            alarm_email=self.node.try_get_context("lhci_mon_email")
        )
        wf.watch_scope(alb_fargate_service)