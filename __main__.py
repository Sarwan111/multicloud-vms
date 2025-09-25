"""
Main entry point for the multicloud-vm Pulumi program.
This file allows the package to be run directly with Pulumi.
"""

from multicloud_vm import EC2Instance

# Get configuration values
import pulumi
config = pulumi.Config()

instance_size = config.get("instance_size") or "t3.micro"
region = config.get("region") or "us-east-1"
os_image = config.get("os_image")  # No default - will use latest Amazon Linux 2
instance_name = config.get("instance_name")

# Create the EC2 instance
ec2_instance = EC2Instance(
    name=instance_name,
    instance_size=instance_size,
    region=region,
    os_image=os_image
)
