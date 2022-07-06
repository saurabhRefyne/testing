import boto3

s3_client = boto3.client("s3")


def get_file_from_s3(key: str) -> bytes:
    return s3_client.get_object(Bucket="S3_BUCKET", Key=key)["Body"].read()
