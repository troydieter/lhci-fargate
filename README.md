# LHCI-Fargate

Deployment of Lighthouse CI through AWS-CDK onto AWS Fargate.

# Table of Contents
- [Documentation](#documentation)
- [Setup](#setup)
- [Diagram](#diagram)
- [Noted cleanup](#noted-cleanup)
- [Useful commands](#useful-commands)

## Documentation
📚 [Read the docs, here!](https://troydieter.github.io/lhci-fargate/) 📚

## Setup
1. Configure cdk.json with your Route 53 forward zone and desired CNAME record name
2. `npm i`
3. `npm run build`
4. `cdk deploy`
5. `lhci wizard` will yield something similar to:

> troy:/mnt/c/coderepo/lhci-fargate$ lhci wizard
>
> ? Which wizard do you want to run? new-project
>
> ? What is the URL of your LHCI server? https://lhci.example.com
>
> ? What would you like to name the project? lhci-fargate
>
> ? Where is the project's code hosted? https://github.com/example/lhci-fargate
>
> ? What branch is considered the repo's trunk or main branch? main

6. Modify your `lighthouserc.js` file accordingly:

```json
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
            // hostname: "127.0.0.1"
        }
    },
    // assert: {
    //     assertions: {
    //       'categories:performance': [
    //         'error',
    //         { minScore: 0.9, aggregationMethod: 'median-run' },
    //       ],
    //       'categories:accessibility': [
    //         'error',
    //         { minScore: 1, aggregationMethod: 'pessimistic' },
    //       ],
    //       'categories:best-practices': [
    //         'error',
    //         { minScore: 1, aggregationMethod: 'pessimistic' },
    //       ],
    //       'categories:seo': [
    //         'error',
    //         { minScore: 1, aggregationMethod: 'pessimistic' },
    //       ],
    //     },
    //   },
    upload: {
        target: 'lhci',
        serverBaseUrl: 'https://lhci.example.com',
        token: 'REPLACE-ME-WITH-LHCI-WIZARD-BUILD-TOKEN-VALUE',
        ignoreDuplicateBuildFailure: true,
        allowOverwriteOfLatestBranchBuild: true
    },
    },
};
```

7. Replace the `buildToken` value provided by `lhci-wizard` in the `lighthouserc.js` file with the `token` value as seen above (shown under `upload`)
8. Browse to the LHCI server (for example, https://lhci.example.com , click the left navigational\drop down pane (looking for the value set previously and click the `gear` in the upper-hand left corner)
9. Add in the `adminToken` to the field in the settings for the LH project
10. Run `lhci autorun` to run the `lh-cli` with the settings defined in the `.lighthouserc.js` file

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

        Running Lighthouse 2 time(s) on https://www.example.com
        Run #1...done.
        Run #2...done.
        Done running Lighthouse!

        Saving CI project lhci-fargate (780548b4-d479-4403-9500-e57f87b64d8d)
        Saving CI build (9e77cb40-546e-4c64-b7b1-0ad538255d9b)
        Saved LHR to https://lhci.example.com (2d027171-faf1-40af-bbdb-a4cc8a04a4d5)
        Saved LHR to https://lhci.example.com (eef82c8e-cf94-4b3d-a76e-b4e7044e2096)
        Done saving build results to Lighthouse CI
        View build diff at https://lhci.example.com/app/projects/lhci-fargate/compare/9e77cb40-546e-4c64-b7b1-0ad538255d9b
        No GitHub token set, skipping GitHub status check.

        Done running autorun.

11. Observe the results on the `lhci` server. Browse to: https://lhci.example.com

    ![results](https://i.imgur.com/coKUZbs.png)

## Diagram (example)
![diagram](https://i.imgur.com/OcZkkr2.png)

## Useful commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk synth`       emits the synthesized CloudFormation template
