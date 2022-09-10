import * as cdk from 'aws-cdk-lib';
import { RemovalPolicy, Stack, StackProps } from 'aws-cdk-lib';
import { Certificate, CertificateValidation } from 'aws-cdk-lib/aws-certificatemanager';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as efs from 'aws-cdk-lib/aws-efs';
import { HostedZone } from 'aws-cdk-lib/aws-route53';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import { Watchful } from 'cdk-watchful'
export class LHCIStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, 'lhcivpc', {
      cidr: this.node.tryGetContext('fargate_vpc_cidr')
    });
    const ecsCluster = new ecs.Cluster(this, 'LHCIECSCluster', { vpc: vpc });

    const fileSystem = new efs.FileSystem(this, 'LHCIEfsFileSystem', {
      vpc: vpc,
      encrypted: true,
      lifecyclePolicy: efs.LifecyclePolicy.AFTER_14_DAYS,
      performanceMode: efs.PerformanceMode.GENERAL_PURPOSE,
      throughputMode: efs.ThroughputMode.BURSTING,
      removalPolicy: RemovalPolicy.DESTROY
    });

    const accessPoint = new efs.AccessPoint(this, 'AccessPoint', {
      fileSystem: fileSystem
    });
    const volumeName = 'efs-volume';

    const taskDef = new ecs.FargateTaskDefinition(this, "LHCITaskDef", {
      cpu: 512,
      memoryLimitMiB: 1024,
    });

    taskDef.addVolume({
      name: volumeName,
      efsVolumeConfiguration: {
        fileSystemId: fileSystem.fileSystemId,
        transitEncryption: 'ENABLED',
        authorizationConfig:{
          accessPointId: accessPoint.accessPointId,
          iam: 'ENABLED'
        }
      }
    });

    const containerDef = new ecs.ContainerDefinition(this, "LHCIContainerDef", {
      image: ecs.ContainerImage.fromRegistry("patrickhulce/lhci-server:latest"),
      taskDefinition: taskDef
    });

    containerDef.addMountPoints({
      containerPath: '/data',
      sourceVolume: volumeName,
      readOnly: false
    });

    containerDef.addPortMappings({
      containerPort: 9001
    });

    const lhci_domain_zone_name = HostedZone.fromLookup(this, "lhci_domain_zone_name", { domainName: this.node.tryGetContext('lhci_domain_zone_name') })

    const cert = new Certificate(
      this,
      "certificate",
      {
        domainName: this.node.tryGetContext('lhci_domain_name'),
        validation: CertificateValidation.fromDns(lhci_domain_zone_name),
      }
    );

    const albFargateService = new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'Service01', {
      cluster: ecsCluster,
      taskDefinition: taskDef,
      desiredCount: 2,
      listenerPort: 443,
      certificate: cert,
      redirectHTTP: true,
      domainName: this.node.tryGetContext('lhci_domain_name'),
      domainZone: lhci_domain_zone_name
    });

    const lhcilb = albFargateService.loadBalancer

    const scalableTarget = albFargateService.service.autoScaleTaskCount({
      minCapacity: 2,
      maxCapacity: 4,
    });

    scalableTarget.scaleOnCpuUtilization('CpuScaling', {
      targetUtilizationPercent: 75,
    });

    albFargateService.targetGroup.setAttribute('deregistration_delay.timeout_seconds', '30');
    albFargateService.targetGroup.configureHealthCheck({
      healthyHttpCodes: this.node.tryGetContext('lhci_health_check_port')
    })

    // Override Platform version (until Latest = 1.4.0)
    const albFargateServiceResource = albFargateService.service.node.findChild('Service') as ecs.CfnService;
    albFargateServiceResource.addPropertyOverride('PlatformVersion', '1.4.0')

    // Allow access to EFS from Fargate ECS
    fileSystem.connections.allowDefaultPortFrom(albFargateService.service.connections);

    taskDef.addToTaskRolePolicy(
      new iam.PolicyStatement({
        actions: [
          'elasticfilesystem:ClientRootAccess',
          'elasticfilesystem:ClientWrite',
          'elasticfilesystem:ClientMount',
          'elasticfilesystem:DescribeMountTargets'
        ],
        resources: [`arn:aws:elasticfilesystem:${process.env.CDK_DEFAULT_REGION}:${process.env.CDK_DEFAULT_ACCOUNT}:file-system/${fileSystem.fileSystemId}`]
      })
    );
    
    taskDef.addToTaskRolePolicy(
      new iam.PolicyStatement({
        actions: ['ec2:DescribeAvailabilityZones'],
        resources: ['*']
      })
    );


    const wf = new Watchful(this, 'watchful', {
      alarmEmail: this.node.tryGetContext('lhci_mon_email')
    });
    wf.watchScope(albFargateService)
}
}