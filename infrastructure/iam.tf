resource "aws_iam_user" "DE-Supply-Chain" {
  name = "DE-Supply-Chain-360-HEAD"

  tags = merge(local.common_tags, {
    Role = "Contract-DE-SUPPLYCHAIN360"
  })
}

resource "random_password" "dynamic_password" {
  length  = var.password_lenght
  special = true
  upper   = true
  lower   = true
  numeric = true
}

resource "aws_iam_access_key" "DE_access_key" {
  user = aws_iam_user.DE-Supply-Chain.name
}

resource "aws_iam_user_login_profile" "DE-SC-LoginProfile" {
  user                    = aws_iam_user.DE-Supply-Chain.name
  password_reset_required = true
}

resource "aws_ssm_parameter" "access_key_security" {
  name      = "/${var.project_name}/access_key_id"
  type      = "SecureString"
  value     = aws_iam_access_key.DE_access_key.id
  overwrite = true

  tags = merge(local.common_tags,
    {
      Name = "${var.project_name}-ssm"
  })
}

resource "aws_ssm_parameter" "secret_access_key" {
  name      = "/${var.project_name}/secre_access_key"
  type      = "SecureString"
  value     = aws_iam_access_key.DE_access_key.secret
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

resource "aws_iam_user_policy" "s3_object_access" {
  name = "S3ObjectAccess"
  user = aws_iam_user.DE-Supply-Chain.name

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:ListBucket",
          "s3:PutBucketTagging",
          "s3:ListAllMyBuckets"
        ],
        Resource = [
          "arn:aws:s3:::${module.s3.bucket_name}"
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObjectTagging"
        ],
        Resource = [
          "arn:aws:s3:::${module.s3.bucket_name}/*"
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

resource "aws_iam_user_policy" "ecr_access" {
  name = "ECRAccess"
  user = aws_iam_user.DE-Supply-Chain.name

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ecr:GetAuthorizationToken"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ],
        Resource = "arn:aws:ecr:${var.region}:601955859589:repository/*"
      },
      {
        Effect = "Allow",
        Action = [
          "ecr:CreateRepository"
        ],
        Resource = "arn:aws:ecr:${var.region}:601955859589:repository/*"
      }
    ]
  })
}

resource "aws_iam_policy" "ssm_parameter_access" {
  name   = "SSMParameterAccess"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParameterHistory",
        "ssm:PutParameter",
        "ssm:DeleteParameter",
        "ssm:DescribeParameters"
      ],
      "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_iam_user_policy_attachment" "ssm_parameter_access" {
  user       = aws_iam_user.DE-Supply-Chain.name
  policy_arn = aws_iam_policy.ssm_parameter_access.arn
}

resource "aws_iam_policy" "ec2_access" {
  name   = "EC2Access"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
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
}
EOF
}

resource "aws_iam_user_policy_attachment" "ec2_access" {
  user       = aws_iam_user.DE-Supply-Chain.name
  policy_arn = aws_iam_policy.ec2_access.arn
}