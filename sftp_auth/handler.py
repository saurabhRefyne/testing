import json

from s3_handler import get_file_from_s3

SFTP_AUTH_CONFIG = {"AWS_ROLE_ARN": "", "S3_BUCKET": ""}


def __get_aws_role_arn():
    return SFTP_AUTH_CONFIG['AWS_ROLE_ARN']


def __get_policy(home_directory: str):
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "ListingOfFilesInSpecificEmployerFolder",
                "Effect": "Allow",
                "Action": "s3:ListBucket",
                "Resource": f"arn:aws:s3:::{SFTP_AUTH_CONFIG['S3_BUCKET']}",
                "Condition": {"StringLike": {"s3:prefix": [f"sftp/attendance/{home_directory}/*"]}}
            },
            {
                "Sid": "FullAccessToSpecificEmployerFolder",
                "Effect": "Allow",
                "Action": ["s3:*"],
                "Resource": f"arn:aws:s3:::{SFTP_AUTH_CONFIG['S3_BUCKET']}/sftp/attendance/{home_directory}/*"
            }
        ]
    }


def __get_user_creds(user_name: str):
    user_creds_config_file = json.loads(get_file_from_s3(key=SFTP_AUTH_CONFIG['SFTP_CREDS_PATH']))
    return user_creds_config_file.get(user_name, None)


def main(events: dict, context: dict) -> dict:
    user_name = events['username']
    password = events['password']
    user_creds = __get_user_creds(user_name=user_name)
    if user_creds is None or ('password' in user_creds and password == ''):
        return {}

    if password != '' and password != user_creds['password']:
        return {}
    sftp_access_data = {
        'Role': __get_aws_role_arn(),
        'Policy': json.dumps(__get_policy(user_creds['homeDirectory'])),
        'HomeDirectory': f"/{SFTP_AUTH_CONFIG['S3_BUCKET']}/sftp/attendance/{user_creds['homeDirectory']}"
    }

    if 'publicKey' in user_creds:
        sftp_access_data['PublicKeys'] = [user_creds['publicKey']]

    return sftp_access_data
