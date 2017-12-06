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

from urllib.parse import urlparse

def main(**kwargs):
    '''get args and try stuff'''

    parser = argparse.ArgumentParser(description="Drive boto3 Elasticsearch client")
    parser.add_argument('-describe', action='store_true', help='describe available ES clients')
    parser.add_argument('-dir', action='store_true', help='show directory of client methods')
    parser.add_argument('-verbose', type=int, nargs='?', const=1, default=1,
                        help='verbosity of output (default: 1)')
    args = parser.parse_args()

    try:
        es_client = boto3.client('es')

        if args.dir:
            print("ES client dir:\n", dir(es_client))
            print()

        if args.describe:
            result = es_client.list_domain_names()
            status = result['ResponseMetadata']['HTTPStatusCode']
            print("HTTP status: ", status)
            domain_names = [dom['DomainName'] for dom in result['DomainNames']]
            print("DOMAIN NAMES:", domain_names)
            for name in domain_names:
                print("DOMAIN:", name, "\n", es_client.describe_elasticsearch_domain(DomainName=name), "\n")

        print("SUCCESS")
    except botocore.exceptions.UnknownServiceError as ex:
        print("FAILURE:", ex)


if __name__ == '__main__':
    main()
