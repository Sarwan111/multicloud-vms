import pulumi
import pulumi_aws as aws
import pulumi_azure as azure
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

class AzureConfig:
    """Configuration class for Azure Virtual Machines."""
    def __init__(self, 
                 vm_size: str = "Standard_B1s",
                 location: str = "East US", 
                 os_image: Optional[str] = None,
                 admin_username: str = "azureuser",
                 admin_password: Optional[str] = None,
                 resource_group_name: Optional[str] = None,
                 tags: Optional[Dict[str, str]] = None):
        self.vm_size = vm_size
        self.location = location
        self.os_image = os_image
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.resource_group_name = resource_group_name
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

class AzureVM:
    def __init__(self, 
                 name: Optional[str] = None,
                 config: Optional[AzureConfig] = None,
                 vm_size: Optional[str] = None,
                 location: Optional[str] = None,
                 os_image: Optional[str] = None,
                 admin_username: Optional[str] = None,
                 admin_password: Optional[str] = None,
                 resource_group_name: Optional[str] = None,
                 azure_provider: Optional[azure.Provider] = None,
                 resource_prefix: str = "multicloud-vm"):
        """
        Create an Azure Virtual Machine with configurable parameters.
        
        Args:
            name: Name for the VM
            config: AzureConfig object with configuration parameters
            vm_size: The VM size (e.g., Standard_B1s, Standard_B2s, etc.) - overrides config
            location: The Azure location/region - overrides config
            os_image: The OS image reference - overrides config
            admin_username: Admin username - overrides config
            admin_password: Admin password - overrides config
            resource_group_name: Resource group name - overrides config
            azure_provider: Optional Azure provider (if not provided, creates one)
            resource_prefix: Prefix for resource names to avoid conflicts
        """
        
        # Use config object if provided, otherwise use individual parameters
        if config:
            vm_size = vm_size or config.vm_size
            location = location or config.location
            os_image = os_image or config.os_image
            admin_username = admin_username or config.admin_username
            admin_password = admin_password or config.admin_password
            resource_group_name = resource_group_name or config.resource_group_name
            tags = config.tags
        else:
            vm_size = vm_size or "Standard_B1s"
            location = location or "East US"
            admin_username = admin_username or "azureuser"
            resource_group_name = resource_group_name or f"{resource_prefix}-rg"
            tags = {}
        
        # Use provided provider or create a new one
        if azure_provider is None:
            azure_provider = azure.Provider(f"{resource_prefix}-azure-provider")
        
        # Create resource group if not provided
        if not resource_group_name:
            resource_group_name = f"{resource_prefix}-rg"
        
        resource_group = azure.core.ResourceGroup(
            f"{resource_prefix}-rg",
            name=resource_group_name,
            location=location,
            tags=tags,
            opts=pulumi.ResourceOptions(provider=azure_provider)
        )
        
        # Create virtual network
        virtual_network = azure.network.VirtualNetwork(
            f"{resource_prefix}-vnet",
            name=f"{resource_prefix}-vnet",
            address_spaces=["10.0.0.0/16"],
            location=location,
            resource_group_name=resource_group.name,
            tags=tags,
            opts=pulumi.ResourceOptions(provider=azure_provider)
        )
        
        # Create subnet
        subnet = azure.network.Subnet(
            f"{resource_prefix}-subnet",
            name=f"{resource_prefix}-subnet",
            resource_group_name=resource_group.name,
            virtual_network_name=virtual_network.name,
            address_prefixes=["10.0.1.0/24"],
            opts=pulumi.ResourceOptions(provider=azure_provider)
        )
        
        # Create network security group
        nsg = azure.network.NetworkSecurityGroup(
            f"{resource_prefix}-nsg",
            name=f"{resource_prefix}-nsg",
            location=location,
            resource_group_name=resource_group.name,
            security_rules=[
                azure.network.NetworkSecurityGroupSecurityRuleArgs(
                    name="SSH",
                    priority=1001,
                    direction="Inbound",
                    access="Allow",
                    protocol="Tcp",
                    source_port_range="*",
                    destination_port_range="22",
                    source_address_prefix="*",
                    destination_address_prefix="*",
                ),
                azure.network.NetworkSecurityGroupSecurityRuleArgs(
                    name="HTTP",
                    priority=1002,
                    direction="Inbound",
                    access="Allow",
                    protocol="Tcp",
                    source_port_range="*",
                    destination_port_range="80",
                    source_address_prefix="*",
                    destination_address_prefix="*",
                ),
                azure.network.NetworkSecurityGroupSecurityRuleArgs(
                    name="HTTPS",
                    priority=1003,
                    direction="Inbound",
                    access="Allow",
                    protocol="Tcp",
                    source_port_range="*",
                    destination_port_range="443",
                    source_address_prefix="*",
                    destination_address_prefix="*",
                ),
            ],
            tags=tags,
            opts=pulumi.ResourceOptions(provider=azure_provider)
        )
        
        # Create public IP
        public_ip = azure.network.PublicIp(
            f"{resource_prefix}-publicip",
            name=f"{resource_prefix}-publicip",
            location=location,
            resource_group_name=resource_group.name,
            allocation_method="Dynamic",
            tags=tags,
            opts=pulumi.ResourceOptions(provider=azure_provider)
        )
        
        # Create network interface
        network_interface = azure.network.NetworkInterface(
            f"{resource_prefix}-nic",
            name=f"{resource_prefix}-nic",
            location=location,
            resource_group_name=resource_group.name,
            ip_configurations=[azure.network.NetworkInterfaceIpConfigurationArgs(
                name=f"{resource_prefix}-ipconfig",
                private_ip_address_allocation="Dynamic",
                subnet_id=subnet.id,
                public_ip_address_id=public_ip.id,
            )],
            tags=tags,
            opts=pulumi.ResourceOptions(provider=azure_provider)
        )
        
        # Associate network security group with subnet
        azure.network.SubnetNetworkSecurityGroupAssociation(
            f"{resource_prefix}-subnet-nsg-association",
            subnet_id=subnet.id,
            network_security_group_id=nsg.id,
            opts=pulumi.ResourceOptions(provider=azure_provider)
        )
        
        # Create the VM
        vm_name = name or f"{resource_prefix}-{pulumi.get_stack()}"
        
        # Merge tags from config with default tags
        vm_tags = {
            "Name": vm_name,
            "Project": resource_prefix,
            "Environment": pulumi.get_stack()
        }
        vm_tags.update(tags)
        
        # Use default Ubuntu image if none provided
        if os_image is None:
            os_image = "Canonical:0001-com-ubuntu-server-focal:20_04-lts-gen2:latest"
        
        self.vm = azure.compute.VirtualMachine(
            f"{resource_prefix}-vm",
            name=vm_name,
            location=location,
            resource_group_name=resource_group.name,
            network_interface_ids=[network_interface.id],
            vm_size=vm_size,
            storage_image_reference=azure.compute.VirtualMachineStorageImageReferenceArgs(
                publisher="Canonical",
                offer="0001-com-ubuntu-server-focal",
                sku="20_04-lts-gen2",
                version="latest",
            ),
                storage_os_disk=azure.compute.VirtualMachineStorageOsDiskArgs(
                name=f"{vm_name}-osdisk",
                caching="ReadWrite",
                create_option="FromImage",
                managed_disk_type="Standard_LRS",
            ),
            os_profile=azure.compute.VirtualMachineOsProfileArgs(
                computer_name=vm_name,
                admin_username=admin_username,
                admin_password=admin_password,
            ),
            os_profile_linux_config=azure.compute.VirtualMachineOsProfileLinuxConfigArgs(
                disable_password_authentication=False,
            ),
            tags=vm_tags,
            opts=pulumi.ResourceOptions(provider=azure_provider)
        )
        
        # Export useful outputs
        pulumi.export("vm_id", self.vm.id)
        pulumi.export("vm_public_ip", public_ip.ip_address)
        pulumi.export("vm_private_ip", network_interface.private_ip_address)
        pulumi.export("vm_location", location)
        pulumi.export("vm_size", vm_size)
        pulumi.export("vm_name", vm_name)
        pulumi.export("resource_group_name", resource_group.name)

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
