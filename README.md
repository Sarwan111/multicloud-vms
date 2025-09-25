# Multicloud VM Package

A reusable Pulumi package for creating EC2 instances and Azure VMs with configurable parameters.

## Features

- **AWS EC2 Support**: Create EC2 instances with configurable parameters
- **Azure VM Support**: Create Azure Virtual Machines with full networking setup
- **Configuration Classes**: Use `AWSConfig` and `AzureConfig` for easy parameter management
- **Flexible API**: Support both config-based and parameter-based instantiation
- **Security**: Automatic security group/NSG creation with common ports (SSH, HTTP, HTTPS)

## Installation

```bash
pip install multicloud-vm
```

## Dependencies

- `pulumi>=3.0.0,<4.0.0`
- `pulumi-aws>=6.0.0,<7.0.0`
- `pulumi-azure>=5.0.0,<6.0.0`

## Usage

### AWS EC2 Instance

```python
from multicloud_vm import EC2Instance, AWSConfig

# Using configuration class
aws_config = AWSConfig(
    instance_size="t3.small",
    region="us-west-2",
    os_image="ami-0c02fb55956c7d316",
    tags={"Environment": "dev"}
)

ec2_instance = EC2Instance(name="my-project", config=aws_config)

# Or using individual parameters
ec2_instance = EC2Instance(
    name="my-project",
    instance_size="t3.micro",
    region="us-east-1"
)
```

### Azure Virtual Machine

```python
from multicloud_vm import AzureVM, AzureConfig

# Using configuration class
azure_config = AzureConfig(
    vm_size="Standard_B2s",
    location="East US",
    admin_username="azureuser",
    admin_password="MySecurePassword123!",
    tags={"Environment": "dev"}
)

azure_vm = AzureVM(name="my-project", config=azure_config)

# Or using individual parameters
azure_vm = AzureVM(
    name="my-project",
    vm_size="Standard_B1s",
    location="West US 2"
)
```

### Multicloud Deployment

```python
from multicloud_vm import EC2Instance, AWSConfig, AzureVM, AzureConfig

# Create both AWS and Azure infrastructure
aws_config = AWSConfig(instance_size="t3.small", region="us-east-1")
azure_config = AzureConfig(vm_size="Standard_B1s", location="East US")

aws_instance = EC2Instance(name="aws-demo", config=aws_config)
azure_vm = AzureVM(name="azure-demo", config=azure_config)
```

## Configuration Classes

### AWSConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `instance_size` | str | "t3.micro" | EC2 instance type |
| `region` | str | "us-east-1" | AWS region |
| `os_image` | str | None | AMI ID (uses latest Amazon Linux 2 if None) |
| `tags` | dict | {} | Tags to apply to resources |

### AzureConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vm_size` | str | "Standard_B1s" | Azure VM size |
| `location` | str | "East US" | Azure location/region |
| `os_image` | str | None | OS image reference (uses Ubuntu 20.04 LTS if None) |
| `admin_username` | str | "azureuser" | Admin username |
| `admin_password` | str | None | Admin password |
| `resource_group_name` | str | None | Resource group name (auto-generated if None) |
| `tags` | dict | {} | Tags to apply to resources |

## Outputs

### AWS EC2 Instance
- `instance_id`: EC2 instance ID
- `instance_public_ip`: Public IP address
- `instance_private_ip`: Private IP address
- `instance_public_dns`: Public DNS name
- `region`: AWS region
- `instance_type`: Instance type
- `ami_id`: AMI ID used

### Azure VM
- `vm_id`: Azure VM ID
- `vm_public_ip`: Public IP address
- `vm_private_ip`: Private IP address
- `vm_location`: Azure location
- `vm_size`: VM size
- `vm_name`: VM name
- `resource_group_name`: Resource group name

## Security

Both AWS and Azure implementations automatically create security configurations:

### AWS
- Security group with rules for SSH (22), HTTP (80), and HTTPS (443)
- All outbound traffic allowed

### Azure
- Network Security Group with rules for SSH (22), HTTP (80), and HTTPS (443)
- Virtual network and subnet creation
- Public IP assignment


