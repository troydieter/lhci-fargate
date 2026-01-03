#!/usr/bin/env python3
import os
import aws_cdk as cdk
from lhci_stack import LHCIStack

app = cdk.App()
LHCIStack(app, "LHCIStack", 
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION")
    )
)

app.synth()
