from setuptools import setup, find_packages

setup(
    name="lhci-fargate",
    version="1.70",
    description="Deployment of Lighthouse CI through AWS-CDK onto AWS Fargate",
    packages=find_packages(),
    install_requires=[
        "aws-cdk-lib==2.261.0",
        "constructs==10.6.0",
        "cdk-watchful==0.6.458"
    ],
    python_requires=">=3.9",
)
