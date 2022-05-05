# LHCI-Fargate

Deployment of Lighthouse CI through AWS-CDK onto AWS Fargate.

# Documentation
📚 [Read the docs, here!](https://troydieter.github.io/lhci-fargate/) 📚

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

4. Create a `.lighthouserc.js` file:

        module.exports = {
            ci: {
            collect: {
                url: "https://www.example.com",
                maxAutodiscoverUrls: 3,
                numberOfRuns: 2,
                settings: {
                    chromeFlags: "--no-sandbox",
                    onlyCategories: ["performance", "best-practices", "accessibility", "seo"],
                    skipAudits: ['uses-http2', 'uses-long-cache-ttl', 'link-text']
                }
            },
            upload: {
                target: 'lhci',
                serverBaseUrl: 'https://lhci.example.com',
                token: 'example-000-example',
                ignoreDuplicateBuildFailure: true,
                allowOverwriteOfLatestBranchBuild: true
            },
            },
        };
    5. Add the `buildToken` to the `.lighthouserc.js` file to the `token` value
    6. Browse to the LHCI server (for example, https://lhci.example.com and click the `gear` in the upper-hand left corner)
    7. Add in the `adminToken` to the field in the settings for the LH project
    8. Run `lhci autorun` to run the `lh-cli` with the settings defined in the `.lighthouserc.js` file

            PS C:\coderepo\lhci-fargate> lhci autorun
            ✅  .lighthouseci/ directory writable
            ✅  Configuration file found
            ✅  Chrome installation found
            ⚠️   GitHub token not set
            ✅  Ancestor hash determinable
            ✅  LHCI server reachable
            ✅  LHCI server API-compatible
            ✅  LHCI server token valid
            ✅  LHCI server can accept a build for this commit hash
            Healthcheck passed!

            Running Lighthouse 2 time(s) on https://www.troydieter.com
            Run #1...done.
            Run #2...done.
            Done running Lighthouse!

            Saving CI project tf-fargate (780548b4-d479-4403-9500-e57f87b64d8d)
            Saving CI build (9e77cb40-546e-4c64-b7b1-0ad538255d9b)
            Saved LHR to https://lhci.troydieter.com (2d027171-faf1-40af-bbdb-a4cc8a04a4d5)
            Saved LHR to https://lhci.troydieter.com (eef82c8e-cf94-4b3d-a76e-b4e7044e2096)
            Done saving build results to Lighthouse CI
            View build diff at https://lhci.troydieter.com/app/projects/tf-fargate/compare/9e77cb40-546e-4c64-b7b1-0ad538255d9b
            No GitHub token set, skipping GitHub status check.

            Done running autorun.
    
    9. Observe the results on the `lhci` server: https://lhci.example.com

        ![results](https://i.imgur.com/coKUZbs.png)
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
