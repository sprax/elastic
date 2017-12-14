#!/usr/bin/env python3
# Sprax Lines       2017.12      Written for Python 3.5
'''Elasticsearch with boto3'''

import argparse
from collections import namedtuple
import os
import pdb
import time
#from dateutil.parser import parse as parse_date

import boto3
import botocore
# import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
from requests_aws4auth import AWS4Auth

from elasticsearch import Elasticsearch
from elasticsearch import RequestsHttpConnection
from elasticsearch.exceptions import TransportError



def match_query(qstring):
    '''body for a simple match query'''
    return {
        "query" : {
            "match" : {
                "content" : qstring
            }
        }
    }

def most_fields_query(qstring, field_names=None):
    '''Prepare body for a most_fields query on the specified fields (e.g. "content")'''
    if field_names is None:
        field_names = ['content', 'content.raw']
    return {
        'query' : {
            'multi_match' : {
                'type' : 'most_fields',
                'query' : qstring,
                'fields' : field_names
            }
        }
    }

def match_phrase_query(qstring, field_names=None):
    '''Prepare a whole phrase only query on the specified fields'''
    if field_names is None:
        field_names = ['content', 'content.raw']
    return {
        'query' : {
            "multi_match" : {
                "type" : "phrase_prefix",
                "query" : qstring,
                "fields" : field_names
            }
        }
    }


def query_string_query(qstring, property_name='content'):
    '''Prepare a query_string query on the specified field (e.g. "content").
    NOTE: query_string may tacitly activate fuzzy matching and other features.
    NOTE: query_string is best used in conjunction with a normalizer
    NOTE: The qstring should contain at least one whole word for this to match; for
    example, "Soston Office" will be matched by "Boston", "office", "Boston off",
    and "ton office", and even "Boston ice" but not by "Bost", "ton", "off", "ton off",
    or "ice"
    '''
    return {
        "from" : 0,
        "size" : 6,
        "query" : {
            "query_string" : {
                "query" : qstring,
                "fields" : [property_name]
            }
        }
    }


def wildcard_query(qstring, property_name='content'):
    '''Prepare a wildcard query on the specified field (e.g. "content")
    NOTE: Wildcard query terms must already be lowercase to match pre-lowercased index terms.
    NOTE: Bigrams are not found; e.g. "boston" or "office" will be found, but not "boston office"
    '''
    return {
        'query' : {
            'wildcard' : {
                property_name : "*%s*" % qstring
            }
        }
    }

def get_aws_es_service_client(service_name='es'):
    '''Get client for the AWS Elasticsearch domain service'''
    return boto3.client(service_name)

def try_aws_es_service_client(args):
    '''Get client for the AWS Elasticsearch domain service'''
    aws_es_service_client = None
    try:
        aws_es_service_client = get_aws_es_service_client()
        result = aws_es_service_client.list_domain_names()
        status = result['ResponseMetadata']['HTTPStatusCode']
        print("HTTP status: ", status)
        domain_names = [dom['DomainName'] for dom in result['DomainNames']]
        print("DOMAIN NAMES:", domain_names)
        print()
        if args.dir:
            print("ES client dir:\n", dir(aws_es_service_client))
            print()
        if args.describe:
            for name in domain_names:
                print("DOMAIN:", name)
                print(aws_es_service_client.describe_elasticsearch_domain(DomainName=name), "\n")
            print()
    except botocore.exceptions.UnknownServiceError as ex:
        print("FAILURE:", ex)
    return aws_es_service_client


def get_aws_auth(hostname, region, use_boto=True):
    '''Get http_aoth for AWS clients'''
    if use_boto:
        try:
            return BotoAWSRequestsAuth(aws_host=hostname, aws_region=region, aws_service='es')
        except TypeError as ex:
            print("No AWS credentials in ~/.aws/credentials ?", ex)
    else:
        access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        try:
            return AWS4Auth(access_key, secret_key, region, 'es')
        except TypeError as ex:
            print("No AWS credentials exported to ENV ?", ex)
    return None

def get_elasticsearch_client(use_boto=True):
    '''Get Elasticsearch client for one AWS ES domain (determined by hostname)'''
    hostname = os.environ.get('AWS_ELASTICSEARCH_HOST')
    region = os.environ.get('AWS_DEFAULT_REGION')
    if region is None:
        # import pdb; pdb.set_trace()
        region = 'us-east-1'
    aws_auth = get_aws_auth(hostname, region, use_boto)
    return Elasticsearch(
        hosts=[{'host': hostname, 'port': 443}],
        http_auth=aws_auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )


MAXLEN = 80

def print_search_stats(results, maxlen=MAXLEN):
    '''print number and latency of results'''
    if results and len(results['hits']['hits']) > 0:
        print('=' * maxlen)
        hit = results['hits']['hits'][0]
        print('Found %d total hits of type %s in index %s in %d ms'
              % (results['hits']['total'], hit['_type'], hit['_index'], results['took']))
        print('-' * maxlen)

def truncate(string, maxlen=MAXLEN):
    '''if string is longer than maxlen, truncate it and add ellipses'''
    if len(string) > maxlen:
        return string[:maxlen].replace("\n", " ") + "..."
    return string.replace("\n", " ")


ESResult = namedtuple('ESResult', 'hit_score doc_id entry_id')

def extract_scores_and_ids(index_name, qstring, results, min_score):
    '''
    Convert raw Elasticsearch results into simple tuples.
    '''
    es_results, max_score, sum_score = [], 0.0, 0.0
    if results:
        try:
            max_score = results['hits']['max_score']
            for hit in results['hits']['hits']:
                score = hit['_score']
                if score >= min_score:
                    sum_score += score
                    kb_entry_id = hit['_id']
                    source = hit['_source']
                    kb_document_id = source['kb_document_id']
                    es_results.append(ESResult(score, kb_document_id, kb_entry_id))
        except Exception as ex:
            print("Error parsing Elasticsearch results in index(%s): <%s>", index_name, ex)
    else:
        print("No Elasticsearch results in index(%s) for (%s)", index_name, qstring)
    return es_results, max_score, sum_score


def print_hits(results, min_score=0.0, maxlen=MAXLEN, verbose=1):
    '''Simple utility function to print results of a search query'''
    if results:
        print_search_stats(results)
        max_score = results['hits']['max_score']
        for hit in results['hits']['hits']:
            # get created date for a repo and fallback to authored_date for a commit
            hit_score = hit['_score']
            norm_score = hit_score / (1.0 + max_score)
            trunc_text = truncate(hit['_source']['content'], maxlen)
            if hit_score >= min_score:
                if verbose > 1:
                    print('%7.3f\t%8.4f\t%s\t%36s\t%36s' % (
                        hit_score,
                        norm_score,
                        trunc_text,
                        hit['_source']['kb_document_id'],
                        hit['_id']
                    ))
                else:
                    print('%7.3f\t%8.4f\t%s' % (hit_score, norm_score, trunc_text))
        print('=' * maxlen)
    else:
        print("---- NO RESULTS ----")


def zot_index_name(zoid):
    '''get Elasticsearch index name from zoid'''
    return "bot{}".format(zoid)


def kb_document_mappings():
    '''Default type mappings for kb_documents'''
    return {
        "kb_document" : {
            "properties" : {
                "content" : {
                    "type" : "text",
                    "index" : "analyzed",
                    "analyzer" : "standard",
                    "store" : True,
                    "term_vector" : "yes",
                    "boost" : 3,
                    "fields" : {
                        "raw" : {
                            "type" : "text",
                            "index" : "not_analyzed",
                            "analyzer" : "case_sensitive_text",
                            "store" : True,
                        }
                    },
                },
                "kb_document_id" : {
                    "store" : True,
                    "type" : "string"
                }
            }
        }
    }


def create_index(elastic_search, index_name, type_mappings=None):
    '''
    1)  For keywords: case-insensitive keywords with default AND operators (intersection),
        light stemming. (query analyzed the same way).
    2)  For phrases: with default semantic fuzziness of 1, not_analyzed,
        and possibly with n-grams (query also not_analyzed).
    '''
    if type_mappings is None:
        type_mappings = kb_document_mappings()
    return elastic_search.indices.create(
        index=index_name,
        body={
            "settings" : {
                "analysis" : {
                    "analyzer" : {
                        "case_sensitive_text" : {
                            "kb_document" : "custom",
                            "tokenizer" : "standard",
                            "filter" : ["my_english_stemmer"] # ["standard", "my_stemmer"]
                        }
                    },
                    "normalizer": {
                        "lower_ascii_normalizer": {
                            "type": "custom",
                            "filter":  ["lowercase", "asciifolding"]
                        }
                    },
                    "filter" : {
                        "my_english_stemmer" : {
                            "type" : "stemmer",
                            "name" : "light_english"
                        }
                    }
                }
            },
            "mappings" : kb_document_mappings(),
        }
    )


class ElasticsearchClient:
    '''Client for searching one Elasticsearch index and type'''

    def __init__(self, zoid, use_boto=True, doc_type='kb_document'):
        '''Save the client, index, and type'''
        self.use_boto = use_boto
        self.client = get_elasticsearch_client(use_boto)
        self.index_name = zot_index_name(zoid)
        self.doc_type = doc_type

    def show_info(self):
        '''Print info about the Elasticsearch client'''
        print("Elasticsearch client from %s credentials" % ['ENV', 'BOTO'][self.use_boto])
        print("Elasticsearch client info:", self.client.info(), "\n")

    def search_index(self, qstring, offset=0, max_size=10):
        '''Search the index using all the parameters.'''
        print('Searching index %s, type %s (offset %d, max_size %d) for: "%s"'
              % (self.index_name, self.doc_type, offset, max_size, qstring))
        try:
            results = self.client.search(index=self.index_name,
                                         doc_type=self.doc_type,
                                         from_=offset,
                                         size=max_size,
                                         body=most_fields_query(qstring)
                                        )
        except (TypeError, TransportError) as ex:
            # Log index_already_exists_exception
            if 'index_not_found_exception' in ex.error:
                print("ElasticsearchClient.search_index: Ignoring index_not_found_exception")
            else:
                print("ElasticsearchClient.search_index: Unexpected exception:", ex)
            return None
        return results


    def create_index(self, index_name=None, type_mappings=None):
        '''Create an index (self.index_name by default)'''
        if index_name is None:
            index_name = self.index_name
        try:
            result = create_index(self.client, index_name, type_mappings)
            return result['acknowledged'] and result['shards_acknowledged']
        except TransportError as ex:
            # ignore index_already_exists_exception
            if "index_already_exists_exception" in ex.error:
                print("ElasticsearchClient.create_index: Ignoring index_already_exists_exception")
            else:
                print("ElasticsearchClient.create_index: exception:", ex)
        return False

    def delete_index(self, index_name=None, **kwargs):
        '''Delete an index (self.index_name by default)'''
        if index_name is None:
            index_name = self.index_name
        try:
            result = self.client.indices.delete(index=index_name, **kwargs)
            return result['acknowledged']
        except TransportError as ex:
            # ignore index_already_exists_exception
            if "index_not_found_exception" in ex.error:
                print("ElasticsearchClient.create_index: Ignoring index_not_found_exception")
            else:
                print("ElasticsearchClient.create_index: exception:", ex)
        return False

    def index_all_kb_documents(self, index_name=None, **kwargs):
        '''Fully reindexes a bot's kb_documents, where a kb_document may contain knowledge tags
        NOTE: if we change the indexing scheme, old indices should be deleted, not updated in place.
        Inconsistent indices may cause strange search results.
        @param bot [Bot] The bot to re-index
        '''
        if index_name is None:
            index_name = self.index_name
        try:
            self.create_index(index_name)
            entry_hashes = []
            for doc in bot.kb_documents:
                entry_hashes += make_entry_hashes(index_name, doc)
            result = self.client.bulk(body=entry_hashes)
            pdb.set_trace()
            return result['acknowledged']
        except TransportError as ex:
            # ignore index_already_exists_exception
            if "index_not_found_exception" in ex.error:
                print("ElasticsearchClient.create_index: Ignoring index_not_found_exception")
            else:
                print("ElasticsearchClient.create_index: exception:", ex)
        return False


###############################################################################
def do_es_command(es_client, args):
    '''Execute an Elasticsearch command'''
    if args.version:
        es_client.show_info()
    elif args.create_index:
        index_name = None if args.create_index == dummy_index else args.create_index
        print("======> create_index(%s)" % index_name)
        es_client.create_index(index_name)
    elif args.delete_index:
        index_name = None if args.delete_index == dummy_index else args.delete_index
        print("======> delete_index(%s)" % index_name)
        es_client.delete_index(index_name)
    else:
        print("======> search_index(%s, %s)" % (es_client.index_name, args.query))
        results = es_client.search_index(args.query, offset=args.offset, max_size=args.size)
        print_hits(results, min_score=args.min_score)


def main():
    '''get args and try stuff'''
    dummy_index = 'SelfIndex'
    default_id = 2
    const_zoid = 7777777
    parser = argparse.ArgumentParser(description="Drive boto3 Elasticsearch client")
    parser.add_argument('query', type=str, nargs='?', default='IT', help='query string for search')
    parser.add_argument('-boto', action='store_false',
                        help='Use ENV variables instead of reading AWS credentials from file (boto)')
    parser.add_argument('-create_index', metavar='NAME', type=str, nargs='?', const=dummy_index, help='create named index')
    parser.add_argument('-delete_index', metavar='NAME', type=str, nargs='?', const=dummy_index, help='delete named index')
    parser.add_argument('-describe', action='store_true', help='Describe available ES clients')
    parser.add_argument('-dir', action='store_true', help='Show directory of client methods')
    parser.add_argument('-domains', action='store_true', help='List available ES domains (boto)')
    parser.add_argument('-index', metavar='ID', type=int, nargs='?', const=const_zoid, default=default_id,
                        help='index all docs for ID (const: %d, default: %d)'
                        % (const_zoid, default_id))
    parser.add_argument('-min_score', metavar='MIN', type=float, nargs='?', const=1.0, default=0.0,
                        help='Minimum score for result hits (default: 0.0)')
    parser.add_argument('-offset', type=int, nargs='?', const=1, default=0,
                        help='Offset into results list (default: 0)')
    parser.add_argument('-size', type=int, nargs='?', const=5, default=6,
                        help='Maximum number of results (default: 6)')
    parser.add_argument('-type', type=str, nargs='?', default='most_fields_query', help='query type for search')
    parser.add_argument('-verbose', type=int, nargs='?', const=1, default=1,
                        help='Verbosity of output (default: 1)')
    parser.add_argument('-version', '-V', action='store_true', help='Show info on ES services')
    parser.add_argument('-zoid', metavar='ID', type=int, nargs='?', const=const_zoid, default=default_id,
                        help='Zoastrian ID (const: %d, default: %d)' % (const_zoid, default_id))
    args = parser.parse_args()
    if args.verbose > 7:
        print("Type(args): ", type(args))
        print(args)
        exit(0)

    if args.domains:
        try_aws_es_service_client(args)

    beg_time = time.time()
    es_client = ElasticsearchClient(args.zoid, args.boto)
    do_es_command(es_client, args)
    end_time = time.time()
    print("Elapsed time: %d seconds" % (end_time - beg_time))

if __name__ == '__main__':
    main()
