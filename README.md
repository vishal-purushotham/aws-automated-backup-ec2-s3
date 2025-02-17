# EC2 to S3 Automated Backup

Automates file backups from an EC2 instance to an S3 bucket using AWS Lambda and CloudWatch Events.

## Services

*   EC2, S3, Lambda, CloudWatch Events (EventBridge), IAM, SSM

## Setup

1.  **EC2:** Create instance (Amazon Linux 2) with IAM role (`AmazonS3FullAccess`, `AmazonEC2FullAccess`, `AmazonSSMFullAccess`, trust both `lambda.amazonaws.com` and `ec2.amazonaws.com`). Create test file (e.g., `/opt/backup/test_file.txt`).
2.  **S3:** Create bucket.
3.  **Lambda:** Create function (Python 3.9), upload `lambda_function.zip`, handler: `backup_script.lambda_handler`, `INSTANCE_ID` env var, set IAM role, enable function URL.
4.  **CloudWatch Events:** Create rule, schedule (cron), target: Lambda.

## Deployment Package

```bash
mkdir package
cp backup_script.py package/
pip install --platform manylinux2014_x86_64 --target ./package --python-version 3.9 -r requirements.txt --upgrade --only-binary=:all:
cd package
zip -r ../lambda_function.zip .
cd ..
```

## Files

- **`backup_script.py`**: The Python script for the Lambda function. Remember to replace `your-s3-bucket-name` with your actual S3 bucket name.
- **`requirements.txt`**: Lists the `boto3` dependency.
- **`lambda_function.zip`**: The deployment package (created by the commands above).

## Testing

1. Manually invoke the Lambda function.
2. Create a temporary EventBridge rule to trigger the Lambda function in a few minutes.
3. Verify that a backup file appears in your S3 bucket.
4. Delete the temporary rule.

## Notes

- Ensure the EC2's IAM role is attached during creation.
- Ensure the IAM role contains the correct trust relationship.
