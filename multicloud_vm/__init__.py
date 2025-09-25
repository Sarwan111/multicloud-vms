import pulumi
import pulumi_aws as aws
from typing import Optional, Dict, Any

class AWSConfig:
    """Configuration class for AWS EC2 instances."""
    def __init__(self, 
                 instance_size: str = "t3.micro",
                 region: str = "us-east-1", 
                 os_image: Optional[str] = None,
                 tags: Optional[Dict[str, str]] = None):
        self.instance_size = instance_size
        self.region = region
        self.os_image = os_image
        self.tags = tags or {}

class EC2Instance:
    def __init__(self, 
                 name: Optional[str] = None,
                 config: Optional[AWSConfig] = None,
                 instance_size: Optional[str] = None,
                 region: Optional[str] = None,
                 os_image: Optional[str] = None,
                 aws_provider: Optional[aws.Provider] = None,
                 resource_prefix: str = "multicloud-vm"):
        """
        Create an EC2 instance with configurable parameters.
        
        Args:
            name: Name for the instance
            config: AWSConfig object with configuration parameters
            instance_size: The EC2 instance type (e.g., t3.micro, t3.small, etc.) - overrides config
            region: The AWS region to deploy the instance - overrides config
            os_image: The AMI ID for the operating system - overrides config
            aws_provider: Optional AWS provider (if not provided, creates one)
            resource_prefix: Prefix for resource names to avoid conflicts
        """
        
        # Use config object if provided, otherwise use individual parameters
        if config:
            instance_size = instance_size or config.instance_size
            region = region or config.region
            os_image = os_image or config.os_image
            tags = config.tags
        else:
            instance_size = instance_size or "t3.micro"
            region = region or "us-east-1"
            tags = {}
        
        # Use provided provider or create a new one
        if aws_provider is None:
            aws_provider = aws.Provider(f"{resource_prefix}-aws-provider", region=region)
        
        # Get the latest Amazon Linux 2 AMI if no specific AMI is provided
        if os_image is None:
            ami = aws.ec2.get_ami(
                most_recent=True,
                owners=["amazon"],
                filters=[
                    aws.ec2.GetAmiFilterArgs(
                        name="name",
                        values=["amzn2-ami-hvm-*-x86_64-gp2"]
                    )
                ],
                opts=pulumi.InvokeOptions(provider=aws_provider)
            )
            os_image = ami.id
        
        # Create a security group with unique name
        security_group = aws.ec2.SecurityGroup(
            f"{resource_prefix}-sg",
            description=f"Security group for {resource_prefix} EC2 instance",
            ingress=[
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="tcp",
                    from_port=22,
                    to_port=22,
                    cidr_blocks=["0.0.0.0/0"],
                    description="SSH access"
                ),
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="tcp",
                    from_port=80,
                    to_port=80,
                    cidr_blocks=["0.0.0.0/0"],
                    description="HTTP access"
                ),
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="tcp",
                    from_port=443,
                    to_port=443,
                    cidr_blocks=["0.0.0.0/0"],
                    description="HTTPS access"
                )
            ],
            egress=[
                aws.ec2.SecurityGroupEgressArgs(
                    protocol="-1",
                    from_port=0,
                    to_port=0,
                    cidr_blocks=["0.0.0.0/0"],
                    description="All outbound traffic"
                )
            ],
            opts=pulumi.ResourceOptions(provider=aws_provider)
        )
        
        # Create the EC2 instance with unique name
        instance_name = name or f"{resource_prefix}-{pulumi.get_stack()}"
        
        # Merge tags from config with default tags
        instance_tags = {
            "Name": instance_name,
            "Project": resource_prefix,
            "Environment": pulumi.get_stack()
        }
        instance_tags.update(tags)
        
        self.instance = aws.ec2.Instance(
            f"{resource_prefix}-instance",
            ami=os_image,
            instance_type=instance_size,
            vpc_security_group_ids=[security_group.id],
            tags=instance_tags,
            opts=pulumi.ResourceOptions(provider=aws_provider)
        )
        
        # Export useful outputs
        pulumi.export("instance_id", self.instance.id)
        pulumi.export("instance_public_ip", self.instance.public_ip)
        pulumi.export("instance_private_ip", self.instance.private_ip)
        pulumi.export("instance_public_dns", self.instance.public_dns)
        pulumi.export("region", region)
        pulumi.export("instance_type", instance_size)
        pulumi.export("ami_id", os_image)

# Only create resources when this module is run directly, not when imported
if __name__ == "__main__":
    # Get configuration values
    config = pulumi.Config()
    instance_size = config.get("instance_size") or "t3.micro"
    region = config.get("region") or "us-east-1"
    os_image = config.get("os_image")  # No default - will use latest Amazon Linux 2
    instance_name = config.get("instance_name")

    # Create the EC2 instance
    ec2_instance = EC2Instance(
        instance_size=instance_size,
        region=region,
        os_image=os_image,
        name=instance_name
    )
