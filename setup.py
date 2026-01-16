from setuptools import setup, find_packages

setup(
    name="lhci-fargate",
    version="1.70",
    description="Deployment of Lighthouse CI through AWS-CDK onto AWS Fargate",
    packages=find_packages(),
    install_requires=[
        "aws-cdk-lib==2.233.0",
        "constructs==10.4.5",
        "cdk-watchful>=0.6.233"
    ],
    python_requires=">=3.8",
)
