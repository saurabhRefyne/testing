import datetime
import json
import logging
from urllib.parse import unquote

import boto3
import requests

SCHEDULER_CONFIG = {"AWS_ROLE_ARN": "", "S3_BUCKET": ""}
logger = logging.getLogger('main')


def __read_file_from_s3(s3_template_path: str) -> bytes:
    try:
        return boto3.client("s3").get_object(
            Bucket=SCHEDULER_CONFIG["S3_BUCKET"],
            Key=unquote(s3_template_path)
        )["Body"].read()
    except Exception as e:
        logger.warning("Failed to fetch document, template path invalid: {}/{}".format(
            SCHEDULER_CONFIG["S3_BUCKET"], s3_template_path))
        logger.error(e)
        raise ValueError("Template path Invalid: {}/{}".format(SCHEDULER_CONFIG["S3_BUCKET"], s3_template_path))


def __get_config_path() -> str:
    return 'config/scheduler_config.json'


def __get_config():
    return json.loads(__read_file_from_s3(__get_config_path()))


def __get_req(url: str, params: dict = {}, headers: dict = {}):
    response = requests.get(url=url, params=params, headers=headers)
    if response.status_code // 100 != 2:
        logger.error(f'invalid status code errors: {response.text}')
        raise Exception('')
    return response


def __post_req(url: str, payload: dict = {}, headers: dict = {}):
    response = requests.get(url=url, data=payload, headers=headers)
    if response.status_code // 100 != 2:
        logger.error(f'invalid status code error: {response.text}')
        raise Exception('')
    return response


def __validate_resource(resource: dict):
    required_fields = ['url', 'method']
    missing_fields = set(required_fields) - set(resource.keys())
    if len(missing_fields) > 0:
        logger.error(f'invalid resource structure missing keys: {missing_fields}')
        raise KeyError(f'invalid resource structure missing keys: {missing_fields}')

    if resource['method'] not in ['GET', 'POST']:
        logger.error(f'invalid resource method: {resource["method"]}')
        raise KeyError(f'invalid resource method: {resource["method"]}')


def __process_cloudwatch_event(cloudwatch_event_name: str):
    config = __get_config()
    if cloudwatch_event_name not in config:
        raise KeyError(f'{cloudwatch_event_name} key not found')
    for resource_name in config[cloudwatch_event_name]:
        resource_details = config[cloudwatch_event_name][resource_name]
        try:
            __validate_resource(resource=resource_details)
            if resource_details['method'] == 'GET':
                __get_req(url=resource_details['url'], params=resource_details.get('params', {}),
                          headers=resource_details.get('headers', {}))
            if resource_details['method'] == 'POST':
                __post_req(url=resource_details['url'], payload=resource_details.get('payload', {}),
                           headers=resource_details.get('headers', {}))
        except Exception as e:
            logger.error(f'error occurred while running the resource: {resource_details}, error: {e}')


def main(event: dict, context: dict):
    logger.info(f'time: {datetime.datetime.now()} event: {event}')
    if 'detail-type' in event and event['source'] == 'aws.events':
        cloudwatch_event_name = event['resources'][0].split("/")[-1]
        __process_cloudwatch_event(cloudwatch_event_name=cloudwatch_event_name)
