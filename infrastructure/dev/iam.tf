resource "aws_iam_user" "DE-Supply-Chain" {
    name = "DE-Supply-Chain"
    tags = {
        profile = var.profile
        role = "Contract-DE"
    }

}
resource "aws_iam_policy" "DE-policy" {
  name   = "DE-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "arn:aws:s3:::SupplyChain360",
          "arn:aws:s3:::SupplyChain360/*"
        ]
      },
      {
        Sid    = "NetworkingAndInfrastructure"
        Effect = "Allow"
        Action = [
          "ec2:CreateVpc", "ec2:DescribeVpcs", "ec2:CreateSubnet", "ec2:DescribeSubnets",
          "ec2:CreateInternetGateway", "ec2:AttachInternetGateway", "ec2:DescribeInternetGateways",
          "ec2:CreateNatGateway", "ec2:DescribeNatGateways", "ec2:AllocateAddress",
          "ec2:DescribeAddresses", "ec2:CreateRouteTable", "ec2:AssociateRouteTable",
          "ec2:CreateRoute", "ec2:DescribeRouteTables", "ec2:CreateSecurityGroup",
          "ec2:AuthorizeSecurityGroupIngress", "ec2:AuthorizeSecurityGroupEgress",
          "ec2:DescribeSecurityGroups", "ec2:DescribeAccountAttributes",
          "ec2:DescribeNetworkInterfaces", "ec2:RunInstances", "ec2:TerminateInstances"
        ]
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_user_policy_attachment" "attach_policy" {
  user       = "DE-Supply-Chain"
  policy_arn = aws_iam_policy.DE-policy.arn
}