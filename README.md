# LHCI-Fargate

Deployment of Lighthouse CI through AWS-CDK onto AWS Fargate.

# Diagram
![diagram](https://i.imgur.com/OcZkkr2.png)

# Noted cleanup

1. You may need to clean up `EFS` filesystems when creating and destroying this CDK app (they may persist)
2. Check for any lingering `EIP`'s that may resided

## Useful commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk synth`       emits the synthesized CloudFormation template
