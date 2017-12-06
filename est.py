

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
    es_client = boto3.client('es')
    print("ES:", dir(es_client))
    print()
    result = es_client.list_domain_names()
    status = result['ResponseMetadata']['HTTPStatusCode']
    print("status: ", status)

    domain_names = [dom['DomainName'] for dom in result['DomainNames']]
    print("LIST:", domain_names)

    for name in domain_names:
        print("DOMAIN:", name, "\n", es_client.describe_elasticsearch_domain(DomainName=name), "\n")


    print("DONE")


if __name__ == '__main__':
    main()
