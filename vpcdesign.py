import boto3

aws_management_console = boto3.session.Session(profile_name="default",region_name="eu-north-1")
ec2 = aws_management_console.resource("ec2")

try:
    # Create VPC
    vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
    print("VPC created successfully with ID:", vpc.id)

except Exception as e:
    print("An error occurred while creating VPC:", e)

vpc.create_tags(Tags=[{"Key": "Name", "Value": "MyVPC"}])
vpc.wait_until_available()

# Create public subnets
subnet1 = ec2.create_subnet(CidrBlock='10.0.1.0/24', VpcId=vpc.id, AvailabilityZone='eu-north-1a')
subnet2 = ec2.create_subnet(CidrBlock='10.0.2.0/24', VpcId=vpc.id, AvailabilityZone='eu-north-1b')

# Create internet gateway
ig = ec2.create_internet_gateway()
vpc.attach_internet_gateway(InternetGatewayId=ig.id)

# Create route table for public subnets
route_table = vpc.create_route_table()
route = route_table.create_route(DestinationCidrBlock='0.0.0.0/0', GatewayId=ig.id)
route_table.associate_with_subnet(SubnetId=subnet1.id)
route_table.associate_with_subnet(SubnetId=subnet2.id)

# Create private subnet
subnet3 = ec2.create_subnet(CidrBlock='10.0.3.0/24', VpcId=vpc.id, AvailabilityZone='eu-north-1b')



ec2 = aws_management_console.client('ec2')

# Allocate an Elastic IP address
allocation = ec2.allocate_address(Domain='vpc')




# Create a NAT Gateway
nat_gateway = ec2.create_nat_gateway(SubnetId=subnet2.id, AllocationId=allocation['AllocationId'])
nat_gateway_id = nat_gateway['NatGateway']['NatGatewayId']



# Create a private route table
ec2 = aws_management_console.client('ec2')
route_table_private = list(vpc.route_tables.all())[1]
route_private = ec2.create_route(RouteTableId=route_table_private.id, DestinationCidrBlock='0.0.0.0/0', NatGatewayId=nat_gateway_id)
route_table_private.associate_with_subnet(SubnetId=subnet3.id)


# Create security group for EC2 instances
security_group_public = ec2.create_security_group(GroupName='publicSG', Description='Security group for public subnet', VpcId=vpc.id)
security_group_private = ec2.create_security_group(GroupName='privateSG', Description='Security group for private subnet', VpcId=vpc.id)

# Authorize security group ingress

security_group_public.authorize_ingress(
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }
    ]
)
security_group_private.authorize_ingress(
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }
    ]
)


# Launch EC2 instances
instances_pub = ec2.create_instances(
    ImageId='ami-0014ce3e52359afbd',
    MinCount=1,
    MaxCount=1,
    InstanceType='t3.micro',
    SubnetId=subnet1.id,
    SecurityGroups=[security_group_public.group_id]
)

instances_priv = ec2.create_instances(
    ImageId='ami-0d0b75c8c47ed0edf',
    MinCount=1,
    MaxCount=1,
    InstanceType='t3.micro',
    SubnetId=subnet3.id,
    SecurityGroups=[security_group_private.group_id]
)