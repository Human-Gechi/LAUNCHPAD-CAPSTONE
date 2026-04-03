resource "aws_iam_user" "DE-Supply-Chain" {
  name = "DE-Supply-Chain-360"

  tags = merge(local.common_tags, {
    Role = "Contract-DE"
  })
}

resource "random_password" "dynamic_password" {
    length = var.password_lenght
    special = true
    upper = true
    lower = true
    numeric = true
}

resource "aws_iam_access_key" "DE_access_key" {
    user = aws_iam_user.DE-Supply-Chain.name
}

resource "aws_iam_user_login_profile" "DE-LoginProfile" {
    user = aws_iam_user.DE-Supply-Chain.name
    password_reset_required = true
}

resource "aws_ssm_parameter" "access_key_security" {
  name  = "/${var.project_name}/access_key_id"
  type  = "String"
  value = aws_iam_access_key.DE_access_key.id
  overwrite = true

  tags = merge(local.common_tags,
    {
      Name = "${var.project_name}-ssm"
  })
}

resource "aws_iam_user_policy" "allow_change_password" {
  name = "AllowChangeOwnPassword"
  user = aws_iam_user.DE-Supply-Chain.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "iam:ChangePassword"
        Resource = "arn:aws:iam::*:user/${aws_iam_user.DE-Supply-Chain.name}"
      }
    ]
  })
}
resource "aws_iam_user_policy" "s3_global_list" {
  name = "S3GlobalList"
  user = aws_iam_user.DE-Supply-Chain.name

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "S3GlobalList",
        Effect = "Allow",
        Action = [
          "s3:ListAllMyBuckets",
          "s3:GetBucketLocation",
          "s3:GetBucketAcl",
          "s3:GetBucketWebsite",
          "s3:GetBucketLogging",
          "s3:GetBucketTagging",
          "s3:GetAccountPublicAccessBlock"
        ],
        Resource = "*"
      }
    ]
  })
}
resource "aws_iam_user_policy" "s3_specific_bucket_access" {
  name = "S3SpecificBucketAccess"
  user = aws_iam_user.DE-Supply-Chain.name

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "S3SpecificBucketAccess",
        Effect = "Allow",
        Action = [
          "s3:ListBucket",
          "s3:ListAccessPoints",
          "s3:GetBucketMetadataTableConfiguration",
          "s3:GetBucketVersioning",
          "s3:GetLifecycleConfiguration",
          "s3:GetReplicationConfiguration",
          "s3:GetInventoryConfiguration",
          "s3:GetBucketPublicAccessBlock",
          "s3:GetBucketPolicy",
          "s3:PutBucketVersioning",
          "s3:GetEncryptionConfiguration",
          "s3:GetBucketObjectLockConfiguration",
          "s3:PutBucketTagging"
        ],
        Resource = [
          "arn:aws:s3:::${aws_s3_bucket.SupplyChain360.id}"
        ]
      }
    ]
  })
}

resource "aws_iam_user_policy" "s3_object_access" {
  name = "S3ObjectAccess"
  user = aws_iam_user.DE-Supply-Chain.name

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObjectTagging"
        ],
        Resource = [
          "arn:aws:s3:::${aws_s3_bucket.SupplyChain360.id}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_user_policy" "iam_access" {
  name = "IAMAccess"
  user = aws_iam_user.DE-Supply-Chain.name

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "iamaccess",
        Effect = "Allow",
        Action = [
          "iam:ListAccessKeys",
          "iam:GetUser",
          "iam:CreateAccessKey",
          "iam:DeleteAccessKey",
          "iam:UpdateAccessKey",
          "iam:GetUserPolicy",
          "iam:GetAccessKeyLastUsed",
          "iam:GetLoginProfile",
          "iam:ListUserTags"
        ],
        Resource = "arn:aws:iam::*:user/${aws_iam_user.DE-Supply-Chain.name}"
      }
    ]
  })
}

resource "aws_iam_user_policy" "vpc_ec2" {
  name = "Vpc-EC2"
  user = aws_iam_user.DE-Supply-Chain.name

  policy = jsonencode({
    Version = "2012-10-17",
    Statement =[
          {
           "Sid": "NetworkingAndInfrastructure",
          "Effect": "Allow",
          "Action": [
            "ec2:CreateVpc",
            "ec2:DescribeVpcs",
            "ec2:DescribeVpcAttribute",
            "ec2:CreateSubnet",
            "ec2:DescribeSubnets",
            "ec2:CreateInternetGateway",
            "ec2:AttachInternetGateway",
            "ec2:DescribeInternetGateways",
            "ec2:CreateRouteTable",
            "ec2:AssociateRouteTable",
            "ec2:CreateRoute",
            "ec2:DescribeRouteTables",
            "ec2:CreateSecurityGroup",
            "ec2:AuthorizeSecurityGroupIngress",
            "ec2:AuthorizeSecurityGroupEgress",
            "ec2:DescribeSecurityGroups",
            "ec2:CreateTags",
            "ec2:DescribeNetworkInterfaces"

          ],
          "Resource": "*"
        }
    ]
  })
}