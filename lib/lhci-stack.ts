import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as efs from 'aws-cdk-lib/aws-efs';
import { HostedZone } from 'aws-cdk-lib/aws-route53';
import * as cr from 'aws-cdk-lib/custom-resources';
import { FargateEfsCustomResource } from "./efs-mount-fargate-cr";


export class LHCIStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, 'lhcivpc');
    const ecsCluster = new ecs.Cluster(this, 'LHCIECSCluster', { vpc: vpc });

    const fileSystem = new efs.FileSystem(this, 'LHCIEfsFileSystem', {
      vpc: vpc,
      encrypted: true,
      lifecyclePolicy: efs.LifecyclePolicy.AFTER_14_DAYS,
      performanceMode: efs.PerformanceMode.GENERAL_PURPOSE,
      throughputMode: efs.ThroughputMode.BURSTING
    });


    const params = {
      FileSystemId: fileSystem.fileSystemId,
      PosixUser: {
        Gid: 1000,
        Uid: 1000
      },
      RootDirectory: {
        CreationInfo: {
          OwnerGid: 1000,
          OwnerUid: 1000,
          Permissions: '755'
        },
        Path: '/data'
      },
      Tags: [
        {
          Key: 'Name',
          Value: 'lhci-data'
        }
      ]
    };

    const efsAccessPoint = new cr.AwsCustomResource(this, 'EfsAccessPoint', {
      onUpdate: {
        service: 'EFS',
        action: 'createAccessPoint',
        parameters: params,
        physicalResourceId: cr.PhysicalResourceId.of('12121212121'),
      },
      policy: cr.AwsCustomResourcePolicy.fromSdkCalls({ resources: cr.AwsCustomResourcePolicy.ANY_RESOURCE })
    });

    efsAccessPoint.node.addDependency(fileSystem);

    const taskDef = new ecs.FargateTaskDefinition(this, "LHCITaskDef", {
      cpu: 512,
      memoryLimitMiB: 1024,
    });

    const containerDef = new ecs.ContainerDefinition(this, "LHCIContainerDef", {
      image: ecs.ContainerImage.fromRegistry("patrickhulce/lhci-server"),
      taskDefinition: taskDef
    });

    containerDef.addPortMappings({
      containerPort: 9001
    });

    const lhci_domain_zone_id = HostedZone.fromHostedZoneId(this, 'lhci_domain_zone_id', this.node.tryGetContext('lhci_domain_zone_id'));

    const albFargateService = new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'Service01', {
      cluster: ecsCluster,
      taskDefinition: taskDef,
      desiredCount: 2,
      listenerPort: 443,
      domainName: this.node.tryGetContext('lhci_domain_name'),
      domainZone: lhci_domain_zone_id
    });

    albFargateService.targetGroup.setAttribute('deregistration_delay.timeout_seconds', '30');

    // Override Platform version (until Latest = 1.4.0)
    const albFargateServiceResource = albFargateService.service.node.findChild('Service') as ecs.CfnService;
    albFargateServiceResource.addPropertyOverride('PlatformVersion', '1.4.0')

    // Allow access to EFS from Fargate ECS
    fileSystem.connections.allowDefaultPortFrom(albFargateService.service.connections);

    //Custom Resource to add EFS Mount to Task Definition
    const resource = new FargateEfsCustomResource(this, 'FargateEfsCustomResource', {
      TaskDefinition: taskDef.taskDefinitionArn,
      EcsService: albFargateService.service.serviceName,
      EcsCluster: ecsCluster.clusterName,
      EfsFileSystemId: fileSystem.fileSystemId,
      EfsMountName: 'data'
    });

    resource.node.addDependency(albFargateService);
  }
}
