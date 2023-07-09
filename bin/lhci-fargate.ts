#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { LHCIStack } from '../lib/lhci-stack';

const app = new cdk.App();
new LHCIStack(app, 'LHCIStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});