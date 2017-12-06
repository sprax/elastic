#!/usr/bin/env python3
# Sprax Lines       2017.12      Written for Python 3.5
'''Elasticsearch with boto3'''

import argparse
import time
import os
#from dateutil.parser import parse as parse_date

import boto3
import botocore
# import requests

# from aws_requests_auth.exceptions import NoSecretKeyError
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
from aws_requests_auth.boto_utils import AWSRequestsAuth

# from elasticsearch import Connection
from elasticsearch import Elasticsearch
from elasticsearch import RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# from urllib.parse import urlparse

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

def print_search_stats(results, maxlen=100):
    '''print number and latency of results'''
    print('=' * maxlen)
    print('Total %d found in %dms' % (results['hits']['total'], results['took']))
    print('-' * maxlen)

def truncate(string, maxlen=100):
    '''truncate string to be <= maxlen, plus ellipses'''
    if len(string) <= maxlen:
        return string
    return string[:maxlen] + "..."

def print_hits(results, maxlen=100):
    '''Simple utility function to print results of a search query'''
    print_search_stats(results)
    hit = results['hits']['hits'][0]
    print("index: %s    type: %s" % (hit['_index'], hit['_type']))
    for hit in results['hits']['hits']:
        # get created date for a repo and fallback to authored_date for a commit
        print('%s\t%s\t%s' % (
            hit['_source']['kb_document_id'],
            hit['_id'],
            truncate(hit['_source']['content'], maxlen)
            ))
    print('=' * maxlen)
    print()

def match_query(term):
    '''body for a simple match query'''
    return {
        "query" : {
            "match" : {
                "content" : term
            }
        }
    }

def search_bot(esearch, index='bot2', term='points', count=5):
    '''FIXME: using default size'''

    print('Search results, max %d:' % count)
    try:
        results = esearch.search(index=index, doc_type='kb_document', body=match_query(term))
    except Exception as ex:
        print("ERROR:", ex)
    print_hits(results)

def get_elasticsearch_client(use_boto=True):
    '''Get Elasticsearch client for one AWS ES domain'''
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_region = os.environ.get('AWS_REGION')
    hostname = os.environ.get('AWS_ELASTICSEARCH_HOST')

    if use_boto:
        try:
            aws_auth = BotoAWSRequestsAuth(aws_host=hostname, aws_region=aws_region, aws_service='es')
        except Exception as ex:
            print("No AWS credentials in ~/.aws/credentials ?", ex)
    else:
        try:
            aws_auth = AWS4Auth(access_key, secret_key, aws_region, 'es')
        except Exception as ex:
            print("No AWS credentials exported to ENV ?", ex)

    if aws_auth:
        return Elasticsearch(
            hosts=[{'host': hostname, 'port': 443}],
            http_auth=aws_auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
    return None

def main():
    '''get args and try stuff'''
    parser = argparse.ArgumentParser(description="Drive boto3 Elasticsearch client")
    parser.add_argument('index', type=str, nargs='?', default='bot2', help='Elasticsearch index to use')
    parser.add_argument('-environment', action='store_true',
                        help='Use ENV variables instead of reading AWS credentials from file (boto)')
    parser.add_argument('-describe', action='store_true', help='Describe available ES clients')
    parser.add_argument('-dir', action='store_true', help='Show directory of client methods')
    parser.add_argument('-domains', action='store_true', help='Show ES domain descriptions')
    parser.add_argument('-verbose', type=int, nargs='?', const=1, default=1,
                        help='Verbosity of output (default: 1)')
    args = parser.parse_args()
    beg_time = time.time()
    try:
        if args.domains:
            _ = get_aws_es_service_client(args)

        esearch = get_elasticsearch_client(args.boto)
        if esearch:
            print(esearch.info(), "\n")
            search_bot(esearch)

        print("SUCCESS")
    except botocore.exceptions.UnknownServiceError as ex:
        print("FAILURE:", ex)
    end_time = time.time()
    print("Elapsed time: %d seconds" % (end_time - beg_time))

if __name__ == '__main__':
    main()
