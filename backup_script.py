import boto3
import datetime
import os

def lambda_handler(event, context):
    """
    Copies a file from an EC2 instance to an S3 bucket using SSM.

    Args:
        event: The event data passed by CloudWatch Events (not used).
        context: The Lambda context object (not used).

    Returns:
        A dictionary indicating success or failure.
    """
    try:
        s3_bucket_name = 'vishalp-ec2-backups-2025'  
        source_file_path = '/opt/backup/test_file.txt'  # Path on the EC2 instance
        # --- End Configuration ---

        # Create S3 and SSM clients (using the IAM role)
        s3_client = boto3.client('s3')
        ssm_client = boto3.client('ssm')

        # Get the instance ID from the environment variable
        instance_id = os.environ['INSTANCE_ID']

        # Construct the backup file name with a timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        backup_file_name = f"backup-{timestamp}.txt"  # Name in the S3 bucket

        # Construct the command to read the file content
        command = f'sudo cat {source_file_path}' # Use sudo to ensure read permissions

        # Use SSM to remotely execute the command and capture output
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',  # Built-in AWS document
            Parameters={'commands': [command]},
            CloudWatchOutputConfig={
                'CloudWatchLogGroupName': '/aws/ssm/AWS-RunShellScript',
                'CloudWatchOutputEnabled': True
                }
        )

        command_id = response['Command']['CommandId']

        # Wait for the command to complete (with a waiter)
        waiter = ssm_client.get_waiter('command_executed')
        try:
            waiter.wait(
                CommandId=command_id,
                InstanceId=instance_id,
                WaiterConfig={
                    'Delay': 5,  # Check every 5 seconds
                    'MaxAttempts': 12 # Try for a maximum of 60 seconds (5 * 12)
                }
            )
        except Exception as e:
            print(f"SSM command failed to complete: {e}")
            raise

        # Get the command output
        output = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )

        # Check if the command was successful
        if output['Status'] != 'Success':
            print(f"SSM command failed: {output['StandardErrorContent']}")
            raise Exception('SSM command failed.')

        file_content = output['StandardOutputContent']

        # Upload the file content to S3
        s3_client.put_object(
            Bucket=s3_bucket_name,
            Key=backup_file_name,
            Body=file_content
        )
        print(f"Successfully backed up {source_file_path} to s3://{s3_bucket_name}/{backup_file_name}")

        return {
            'statusCode': 200,
            'body': f'Successfully backed up {source_file_path} to s3://{s3_bucket_name}/{backup_file_name}'
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': f'Error: {e}'
        }