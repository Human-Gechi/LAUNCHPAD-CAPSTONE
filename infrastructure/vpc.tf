resource "aws_vpc" "main" {
  cidr_block       = "10.0.0.0/16"
  instance_tenancy = "default"

  tags = merge(local.common_tags,
    {
      Name = "${var.project_name}-vpc"
    })
}

# Subnet

resource "aws_subnet" "public_subnet_1" {
  vpc_id = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"

  tags = merge(local.common_tags,
    {
      Name = "${var.project_name}-pb-subnet-1"
    })
}

resource "aws_subnet" "public_subnet_2" {
  vpc_id = aws_vpc.main.id
  cidr_block = "10.0.2.0/24"

  tags = merge(local.common_tags,
    {
      Name = "${var.project_name}-pb-subnet-2"
    })
}
# Internet Gateway

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags,
    {
      Name = "${var.project_name}-igw"
  })
}


resource "aws_route_table" "main-rt" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }


  tags = merge(local.common_tags,
    {
      Name = "${var.project_name}-rt"
  })
}


# Route table associations
resource "aws_route_table_association" "rt-association-1" {
  subnet_id      = aws_subnet.public_subnet_1.id
  route_table_id = aws_route_table.main-rt.id
}


resource "aws_route_table_association" "rt-association-2" {
  subnet_id      = aws_subnet.public_subnet_2.id
  route_table_id = aws_route_table.main-rt.id
}

resource "aws_security_group" "ec2_sg" {
  name        = "${var.project_name}-ec2-sg"
  description = "Allow SSH and Airflow UI"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-ec2-sg"
  })
}

resource "aws_instance" "airflow" {
  ami                         = "ami-0bfa6d0ea0fe2c5a1"
  instance_type               = "m7i-flex.large"
  subnet_id                   = aws_subnet.public_subnet_1.id
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  associate_public_ip_address = true
  key_name                  = "airflow"

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-airflow"
  })
}