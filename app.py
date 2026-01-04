#!/usr/bin/env python
import os
import aws_cdk as cdk
from lhci_stack import LHCIStack

app = cdk.App()
LHCIStack(app, "LHCIStack", description="Lighthouse CI",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION")
    )
)

app.synth()
