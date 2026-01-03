import os
import aws_cdk as cdk
from aws_cdk import RemovalPolicy
from aws_cdk.aws_certificatemanager import Certificate, CertificateValidation
from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
    aws_logs as logs,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
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
        cdk.Tags.of(self).add("Environment", "dev")
        cdk.Tags.of(self).add("Owner", self.node.try_get_context(
            "lhci_mon_email") or "admin")
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
                raise ValueError(
                    f"Required context value '{key}' is missing from cdk.json")

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

        # Database credentials secret
        db_credentials = rds.DatabaseSecret(
            self,
            "LHCIDBCredentials",
            username=config.DB_USERNAME
        )

        # Aurora Serverless v2 Cluster
        aurora_cluster = rds.DatabaseCluster(
            self,
            "LHCIAuroraCluster",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_7
            ),
            credentials=rds.Credentials.from_secret(db_credentials),
            default_database_name=config.DB_NAME,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            storage_encrypted=True,
            removal_policy=RemovalPolicy.DESTROY,
            writer=rds.ClusterInstance.serverless_v2("writer",
                                                     scale_with_writer=True
                                                     ),
            serverless_v2_min_capacity=config.AURORA_MIN_CAPACITY,
            serverless_v2_max_capacity=config.AURORA_MAX_CAPACITY
        )

        # Security group for Aurora cluster
        aurora_sg = ec2.SecurityGroup(
            self,
            "AuroraSecurityGroup",
            vpc=vpc,
            description="Security group for Aurora PostgreSQL cluster",
            allow_all_outbound=False
        )

        # Fargate Task Definition
        task_def = ecs.FargateTaskDefinition(
            self,
            "LHCITaskDef",
            cpu=config.FARGATE_CPU,
            memory_limit_mib=config.FARGATE_MEMORY_MB
        )

        # Grant task access to database secret
        db_credentials.grant_read(task_def.task_role)

        # Container Definition
        container_def = ecs.ContainerDefinition(
            self,
            "LHCIContainerDef",
            image=ecs.ContainerImage.from_registry(
                config.LHCI_CONTAINER_IMAGE),
            task_definition=task_def,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="lhci",
                log_retention=logs.RetentionDays.ONE_MONTH
            ),
            environment={
                **config.CONTAINER_ENVIRONMENT_BASE,
                # We'll construct the connection URL in the container startup
                "DB_HOST": aurora_cluster.cluster_endpoint.hostname,
                "DB_PORT": str(config.DB_PORT),
                "DB_NAME": config.DB_NAME,
                "DB_USER": config.DB_USERNAME
            },
            secrets={
                # Get password from the database secret
                "DB_PASSWORD": ecs.Secret.from_secrets_manager(
                    db_credentials,
                    field="password"
                )
            },
            # Add startup command to construct connection URL
            command=[
                "/bin/sh", "-c",
                "export LHCI_STORAGE__SQL_CONNECTION_URL=\"postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME\" && exec lhci server"
            ],
            user=config.LHCI_CONTAINER_USER,
            readonly_root_filesystem=False  # Required for LHCI to write temp files
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

        # Allow Fargate service to connect to Aurora
        aurora_cluster.connections.allow_from(
            alb_fargate_service.service.connections,
            ec2.Port.tcp(config.DB_PORT),
            "Allow LHCI Fargate service to connect to Aurora PostgreSQL"
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
            scale_in_cooldown=cdk.Duration.minutes(
                config.SCALE_IN_COOLDOWN_MINUTES),
            scale_out_cooldown=cdk.Duration.minutes(
                config.SCALE_OUT_COOLDOWN_MINUTES)
        )

        # Memory-based auto-scaling
        scalable_target.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=config.MEMORY_TARGET_UTILIZATION,
            scale_in_cooldown=cdk.Duration.minutes(
                config.SCALE_IN_COOLDOWN_MINUTES),
            scale_out_cooldown=cdk.Duration.minutes(
                config.SCALE_OUT_COOLDOWN_MINUTES)
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
            interval=cdk.Duration.seconds(
                config.HEALTH_CHECK_INTERVAL_SECONDS),
            timeout=cdk.Duration.seconds(config.HEALTH_CHECK_TIMEOUT_SECONDS),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3
        )

        # Override Platform version (until Latest = 1.4.0)
        alb_fargate_service_resource = alb_fargate_service.service.node.find_child(
            "Service")
        alb_fargate_service_resource.add_property_override(
            "PlatformVersion", "1.4.0")

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
                                wafv2.CfnWebACL.ExcludedRuleProperty(
                                    name="CrossSiteScripting_BODY"),
                                wafv2.CfnWebACL.ExcludedRuleProperty(
                                    name="NoUserAgent_HEADER"),
                                wafv2.CfnWebACL.ExcludedRuleProperty(
                                    name="SizeRestrictions_BODY"),
                                wafv2.CfnWebACL.ExcludedRuleProperty(
                                    name="UserAgent_BadBots_HEADER")
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

        # Output the database endpoint for reference
        cdk.CfnOutput(
            self,
            "DatabaseEndpoint",
            value=aurora_cluster.cluster_endpoint.hostname,
            description="Aurora PostgreSQL cluster endpoint"
        )

        # Output the secret ARN for reference
        cdk.CfnOutput(
            self,
            "DatabaseSecretArn",
            value=db_credentials.secret_arn,
            description="ARN of the database credentials secret"
        )
