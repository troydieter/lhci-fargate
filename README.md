# LHCI-Fargate

Deployment of Lighthouse CI through AWS-CDK onto AWS Fargate.

# Setup
1. Configure cdk.json with your Route 53 forward zone and desired CNAME record name
2. `cdk deploy`
3. `lhci wizard` will yield something similar to:

> troy:/mnt/c/coderepo/lhci-fargate$ lhci wizard
>
> ? Which wizard do you want to run? new-project
>
> ? What is the URL of your LHCI server? https://lhci.example.com
>
> ? What would you like to name the project? tf-fargate
>
> ? Where is the project's code hosted? https://github.com/example/tf-fargate
>
> ? What branch is considered the repo's trunk or main branch? main
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
