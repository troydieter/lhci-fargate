import { Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';

import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2'
import * as ecs from 'aws-cdk-lib/aws-ecs'
import * as cdk from 'aws-cdk-lib'
import { FargateTaskDefinition, TaskDefinition } from 'aws-cdk-lib/aws-ecs';

export class LHCIStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, 'lhcivpc');

    const lb = new elbv2.ApplicationLoadBalancer(this, 'LB', {
      vpc: vpc,
      internetFacing: true,
      loadBalancerName: 'LHCIBalancer'
    });

    const cluster = new ecs.Cluster(this, 'LHCICluster', {
      vpc: vpc
    });

    const taskDefinition = new ecs.FargateTaskDefinition(this, 'TaskDefinition', {
      cpu: 512,
      memoryLimitMiB: 1024,
    });

    const volume = {
      name: "lhcidata",
      efsVolumeConfiguration: {
        fileSystemId: "EFS",
        rootDirectory: 'lhci-data'
      }
    }

    const port = 9001

    const container = taskDefinition.addContainer('Container', {
      image: ecs.ContainerImage.fromRegistry('patrickhulce/lhci-server'),
      portMappings: [{ containerPort: port }],
    })

    taskDefinition.addVolume(volume)
    
    const service = new ecs.FargateService(this, 'FargateService', {
      cluster: cluster,
      taskDefinition: taskDefinition,
      desiredCount: 1,
      serviceName: 'FargateService'
    })

    const tg1 = new elbv2.ApplicationTargetGroup(this, 'TargetGroup', {
      vpc: vpc,
      targets: [service],
      protocol: elbv2.ApplicationProtocol.HTTP,
      stickinessCookieDuration: cdk.Duration.days(1),
      port: port,
      healthCheck: {
        path: '/',
        port: `${port}`
      }
    })

    const listener = lb.addListener(`HTTPListener`, {
      port: 80,
      defaultAction: elbv2.ListenerAction.forward([tg1]) 
    })

    new cdk.CfnOutput(this, 'LoadBalancerDNSName', { value: lb.loadBalancerDnsName });
  }
}
