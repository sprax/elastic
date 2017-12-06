#!/usr/bin/env python3
# Sprax Lines       2017.12      Written for Python 3.5
'''Elasticsearch with boto3'''

import argparse
import time
import os

import boto3
import botocore
import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
# from aws_requests_auth.boto_utils import AWSRequestsAuth

from elasticsearch import Connection
from elasticsearch import Elasticsearch
from elasticsearch import RequestsHttpConnection

from requests_aws4auth import AWS4Auth

from urllib.parse import urlparse

def get_aws_es_service_client(args):
    '''Get client for the AWS Elasticsearch domain service'''
    aws_es_service_client = boto3.client('es')

    if args.dir:
        print("ES client dir:\n", dir(aws_es_service_client))
        print()

    if args.describe:
        result = aws_es_service_client.list_domain_names()
        status = result['ResponseMetadata']['HTTPStatusCode']
        print("HTTP status: ", status)
        domain_names = [dom['DomainName'] for dom in result['DomainNames']]
        print("DOMAIN NAMES:", domain_names)
        for name in domain_names:
            print("DOMAIN:", name, "\n", aws_es_service_client.describe_elasticsearch_domain(DomainName=name), "\n")
    return aws_es_service_client


def get_elasticsearch_client(use_boto=True):
    '''Get Elasticsearch client for one AWS ES domain'''
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_region = os.environ.get('AWS_REGION')
    hostname = os.environ.get('AWS_ELASTICSEARCH_HOST')

    if use_boto:
        aws_auth = BotoAWSRequestsAuth(aws_host=hostname, aws_region=aws_region, aws_service='es')
    else:
        aws_auth = AWS4Auth(access_key, secret_key, aws_region, 'es')

    es = Elasticsearch(
        hosts=[{'host': hostname, 'port': 443}],
        http_auth=aws_auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    print(es.info())


def main(**kwargs):
    '''get args and try stuff'''

    parser = argparse.ArgumentParser(description="Drive boto3 Elasticsearch client")
    parser.add_argument('-boto', action='store_true', help='use boto3 (read AWS credentials from file)')
    parser.add_argument('-describe', action='store_true', help='describe available ES clients')
    parser.add_argument('-dir', action='store_true', help='show directory of client methods')
    parser.add_argument('-verbose', type=int, nargs='?', const=1, default=1,
                        help='verbosity of output (default: 1)')
    args = parser.parse_args()

    try:
        service = get_aws_es_service_client(args)
        esearch = get_elasticsearch_client(args.boto)
        print("SUCCESS")
    except botocore.exceptions.UnknownServiceError as ex:
        print("FAILURE:", ex)

if __name__ == '__main__':
    main()
