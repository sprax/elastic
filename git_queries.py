#!/usr/bin/env python
from __future__ import print_function

import logging
from dateutil.parser import parse as parse_date

from elasticsearch import Elasticsearch

def print_search_stats(results):
    print('=' * 80)
    print('Total %d found in %dms' % (results['hits']['total'], results['took']))
    print('-' * 80)

def print_hits(results):
    " Simple utility function to print results of a search query. "
    print_search_stats(results)
    for hit in results['hits']['hits']:
        # get created date for a repo and fallback to authored_date for a commit
        created_at = parse_date(hit['_source'].get('created_at', hit['_source']['authored_date']))
        print('/%s/%s/%s (%s): %s' % (
                hit['_index'], hit['_type'], hit['_id'],
                created_at.strftime('%Y-%m-%d'),
                hit['_source']['description'].split('\n')[0]))

    print('=' * 80)
    print()

def empty_search(es):
    print('Empty search:')
    print_hits(es.search(index='git'))


def find_term(es, term):
    print('Find commits that contain term="%s" without touching tests:' % term)
    result = es.search(
        index='git',
        doc_type='doc',
        body={
          'query': {
            'bool': {
              'must': {
                'match': {'description': term}
              },
              'must_not': {
                'term': {'files': 'test_elasticsearch'}
              }
            }
          }
        }
    )
    print_hits(result)

def latest_commits(es, count):
    print('Last %d Commits for elasticsearch-py:' % count)
    result = es.search(
        index='git',
        doc_type='doc',
        body={
          'query': {
            'term': {
                'repository': 'elasticsearch-py'
            }
          },
          'sort': [
            {'committed_date': {'order': 'desc'}}
          ],
          'size': count
        }
    )
    print_hits(result)

def last_committer_stats(es, count):
    '''FIXME: using default size'''
    print('Stats for top %d committers:' % count)
    result = es.search(
        index='git',
        doc_type='doc',
        body={
          'size': 0,
          'aggs': {
            'committers': {
              'terms': {
                'field': 'committer.name.keyword',
              },
              'aggs': {
                'line_stats': {
                  'stats': {'field': 'stats.lines'}
                }
              }
            }
          }
        }
    )
    print_search_stats(result)
    for committer in result['aggregations']['committers']['buckets']:
        print('%15s: %3d commits changing %6d lines' % (
            committer['key'], committer['doc_count'], committer['line_stats']['sum']))
    print('=' * 80)

def main():
    # get trace logger and set level
    tracer = logging.getLogger('elasticsearch.trace')
    tracer.setLevel(logging.INFO)
    tracer.addHandler(logging.FileHandler('/tmp/es_trace.log'))
    # instantiate es client, connects to localhost:9200 by default
    es = Elasticsearch()

    empty_search(es)
    find_term(es, 'fix')
    latest_commits(es, 5)
    last_committer_stats(es, 10)

if __name__ == '__main__':
    main()
