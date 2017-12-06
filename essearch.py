


import time
import os

import boto3
import botocore
import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
from aws_requests_auth.boto_utils import AWSRequestsAuth


# import requests
import aws_requests_auth.aws_auth
# import AWSRequestsAuth

from elasticsearch import Connection
from elasticsearch import Elasticsearch

from elasticsearch import RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# from signer import ESConnection
from urllib.parse import urlparse

from boto.connection import AWSAuthConnection


class ESConnection(AWSAuthConnection):

    def __init__(self, region, **kwargs):
        super(ESConnection, self).__init__(**kwargs)
        self._set_auth_region_name(region)
        self._set_auth_service_name("es")

    def _required_auth_capability(self):
        return ['hmac-v4']



class AWSConnection(Connection):

    def __init__(self, host, region, **kwargs):
        super(AWSConnection, self).__init__(host, region, **kwargs)
        self.host = host
        self.region = region
        self.token = kwargs['session_token'] if 'session_token' in kwargs else os.environ.get('AWS_SESSION_TOKEN')
        self.secret = kwargs['secret_key'] if 'secret_key' in kwargs else os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.key = kwargs['access_key'] if 'access_key' in kwargs else os.environ.get('AWS_ACCESS_KEY_ID')
        self.kwargs = kwargs

    def perform_request(self, method, url, params=None,
                        body=None, headers=None, timeout=None, ignore=()):
        start = time.time()
        host = urlparse(self.host).netloc.split(':')[0]
        client = ESConnection(region=self.region,
                              host=self.host,
                              aws_access_key_id=self.key,
                              aws_secret_access_key=self.secret,
                              # security_token=self.token,
                              is_secure=False)

        if body:
            response = client.make_request(method, path=url, params=params, data=body)
        else:
            response = client.make_request(method, path=url, params=params)

        duration = time.time() - start
        raw_data = response.read().decode('utf-8')

        if not (200 <= response.status < 300) and response.status not in ignore:
            self.log_request_fail(method, host, body, duration, response.status)
            self._raise_error(response.status, raw_data)

        # return response.status, dict(response.getheaders()), raw_data


def test_aws_connection():
    '''Busted'''
    hostname = os.environ.get('AWS_ELASTICSEARCH_HOST')
    endpoint = os.environ.get('AWS_ELASTICSEARCH_ENDPOINT')
    region = os.environ.get('AWS_REGION')
    if region is None:
        region = 'us-east-1'
    es = Elasticsearch(connection_class=AWSConnection, host=hostname, region=region)
    print(dir(es))
    # es.search(index='git')
    print()
    import pdb; pdb.set_trace()
    res = es.info()
    print(dir(res))
    print(es.search())

class AwsEsClient:

    def __init__(self, region='us-east-1', **kwargs):
        '''create the Elasticsearch client'''
        self.region = kwargs['region'] if 'region' in kwargs else os.environ.get('AWS_REGION')
        if self.region is None:
            self.region = region

        # Use host, not endpoint:
        # self.endpoint = kwargs['endpoint'] if 'endpoint' in kwargs else os.environ.get('AWS_ELASTICSEARCH_ENDPOINT')
        access_key = kwargs['access_key'] if 'access_key' in kwargs else os.environ.get('AWS_ACCESS_KEY_ID')
        secret_key = kwargs['secret_key'] if 'secret_key' in kwargs else os.environ.get('AWS_SECRET_ACCESS_KEY')
        hostname = kwargs['host'] if 'host' in kwargs else os.environ.get('AWS_ELASTICSEARCH_HOST')
        aws_auth = AWS4Auth(access_key, secret_key, self.region, 'es')

        self.es_client = Elasticsearch(
            hosts=[{'host': hostname, 'port': 443}],
            http_auth=aws_auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

    def get_client(self):
        return self.es_client

def boto_aws_es(use_boto=False):
    # let's talk to our AWS Elasticsearch cluster
    hostname = os.environ.get('AWS_ELASTICSEARCH_HOST')
    if use_boto:
        auth = BotoAWSRequestsAuth(aws_host=hostname, aws_region='us-east-1', aws_service='es')
    else:
        access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        print("AWSRequestsAuth access_key: ", access_key, "  secret_key: ", secret_key)
        auth = AWSRequestsAuth(aws_access_key=access_key, aws_secret_access_key=secret_key, aws_host=hostname, aws_region='us-east-1', aws_service='es')

    print("AUTH: ", auth, "\n")
    response = requests.get(es_endpoint, auth=auth)
    print("RESPONSE:", response.content)

def main(**kwargs):
    boto_aws_es()
    test_aws_connection()
    print("DONE")


if __name__ == '__main__':
    main()
