# LHCI-Fargate v2.0

### Python CDK Implementation

Deployment of Lighthouse CI through AWS-CDK onto AWS Fargate using AWS-CDK Python.

# Table of Contents

- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Infrastructure Deployment](#infrastructure-deployment)
- [Lighthouse CI Setup](#lighthouse-ci-setup)
- [Usage](#usage)
- [Diagram](#diagram)
- [Useful Commands](#useful-commands)

## Prerequisites

1. AWS CLI configured with appropriate permissions
2. Python 3.7+ installed
3. Node.js and npm (for Lighthouse CI CLI)
4. A Route 53 hosted zone for your domain

## Configuration

Configure the CDK stack by updating the context values in `cdk.json`:

```json
{
  "context": {
    "fargate_vpc_cidr": "172.16.16.0/24",
    "lhci_domain_name": "lhci.example.com",
    "lhci_domain_zone_name": "example.com.",
    "lhci_health_check_port": "302",
    "lhci_mon_email": "admin@example.com"
  }
}
```

Update these values according to your environment before deployment.

## Infrastructure Deployment

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Deploy the infrastructure:

   ```bash
   cdk deploy
   ```

3. Wait for deployment to complete. The LHCI server will be available at your configured domain.

## Lighthouse CI Setup

1. Install the Lighthouse CI CLI:

   ```bash
   npm install -g @lhci/cli
   ```

2. Run the wizard to set up your project:

   ```bash
   lhci wizard
   ```

   Example wizard session:

   ```
   ? Which wizard do you want to run? new-project
   ? What is the URL of your LHCI server? https://lhci.example.com
   ? What would you like to name the project? lhci-fargate
   ? Where is the project's code hosted? https://github.com/example/lhci-fargate
   ? What branch is considered the repo's trunk or main branch? main
   ```

3. Create your `lighthouserc.js` configuration file:

   ```javascript
   module.exports = {
     ci: {
       collect: {
         url: "https://www.example.com",
         maxAutodiscoverUrls: 3,
         numberOfRuns: 2,
         settings: {
           chromeFlags: "--no-sandbox",
           onlyCategories: [
             "performance",
             "best-practices",
             "accessibility",
             "seo",
           ],
           skipAudits: ["uses-http2", "uses-long-cache-ttl", "link-text"],
           // hostname: "127.0.0.1"
         },
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
         target: "lhci",
         serverBaseUrl: "https://lhci.example.com",
         token: "REPLACE-ME-WITH-LHCI-WIZARD-BUILD-TOKEN-VALUE",
         ignoreDuplicateBuildFailure: true,
         allowOverwriteOfLatestBranchBuild: true,
       },
     },
   };
   ```

4. Update the `token` value in your `lighthouserc.js` file with the build token provided by the wizard

5. (Optional) Browse to your LHCI server and configure the admin token in the project settings if needed

## Usage

Run Lighthouse CI against your configured URLs:

```bash
lhci autorun
```

Example output:

```
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
```

### Viewing Results

View your Lighthouse CI results at your deployed server: https://lhci.example.com

![results](https://i.imgur.com/coKUZbs.png)

## Diagram

![diagram](https://i.imgur.com/OcZkkr2.png)

## Useful Commands

### CDK Commands

- `pip install -r requirements.txt` - Install Python dependencies
- `cdk deploy` - Deploy this stack to your default AWS account/region
- `cdk diff` - Compare deployed stack with current state
- `cdk synth` - Emits the synthesized CloudFormation template
- `cdk destroy` - Remove the deployed stack

### Lighthouse CI Commands

- `npm install -g @lhci/cli` - Install Lighthouse CI CLI globally
- `lhci wizard` - Set up a new project configuration
- `lhci autorun` - Run Lighthouse CI with your configured settings
- `lhci collect` - Collect Lighthouse reports only
- `lhci upload` - Upload reports to your LHCI server

## Notes

This project uses Python CDK for infrastructure deployment. The Lighthouse CI functionality requires the separate `@lhci/cli` package for running audits.
