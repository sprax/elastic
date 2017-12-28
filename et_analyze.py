#!/usr/bin/env python3
'''pyton translation of es_analyze.sh'''

import json
import pprint
import requests
import urllib

DEFAULT_TEXT = "The YeLLoWing café beLLows MiCe were sleeping FURIOUSly."
HEADERS = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
PRETTY = "true"

def json_text_bytes(text_to_analyze=DEFAULT_TEXT, encoding='utf-8'):
    '''no comma after the text'''
    json_str = "{ \"text\": \"%s\" }" % text_to_analyze
    json_byt = bytes(json_str, encoding=encoding)
    return json_byt


# NOTES: filters are applied in the order listed, so stemming exceptions (keywords)
# and overrides must be listed before the stemmer, and overrides that convert other
# words into to stop words should precede stopword removal.
def json_data_bytes(text=DEFAULT_TEXT, tokenizer="standard", explain=False, encoding='utf-8'):
    '''data payload as JSON string'''
    explain = "true" if explain else "false"
    json_str = '''{
        "tokenizer": "%s",
        "filter": [ "lowercase", "asciifolding",
                    {"type": "keyword_marker", "keywords": ["sleeping"]},
                    {"type": "stemmer_override", "rules": [ "mice=>mouse", "were=>was"]},
                    {"type": "stop", "stopwords": ["a", "is", "the", "was"]},
                    "porter_stem"
                  ],
        "text": "%s",
        "explain": "%s"
    }
    ''' % (tokenizer, text, explain)
    json_byt = bytes(json_str, encoding=encoding)
    return json_byt


def urllib_request_urlopen_es(payload=None, pretty=PRETTY, text="fishing", verbose=0):
    '''Send request to Elasticsearch using urlopen and return bytes-array results converted to dict'''
    # esa_url = r"http://localhost:9200/_analyze?pretty=%s&analyzer=english&text=%s" % (pretty, text)
    esa_url = r"http://localhost:9200"
    res_byt = urllib.request.urlopen(esa_url).read()
    if verbose > 0:
        print("urllib_request_urlopen_es got results of type(%s): (%s)" % (type(res_byt).__name__, res_byt))
    res_str = res_byt.decode('utf-8')
    res_dct = json.loads(res_str)
    if verbose > 1:
        print("urllib_request_urlopen_es results after .decode('utf-8') and json.loads to dict:\n", res_dct)
    return res_dct


def requests_get_es(payload=None, text="fishing", verbose=0):
    '''post request to Elasticsearch and return JSON results as dict'''
    url = r"http://localhost:9200/_analyze?analyzer=english&text=%s" % text
    got = requests.get(url)
    if verbose > 0:
        print("requests_get_es got results of type(%s): (%s)" % (type(got).__name__, got))
    return got.json()


def requests_post_es(payload=None, url=r"http://localhost:9200/_analyze", headers=HEADERS, verbose=0):
    '''post analysis request to Elasticsearch and return JSON results as a dict'''
    payload = payload if payload else json_data_bytes()
    results = requests.post(url=url, headers=headers, data=payload)
    if verbose:
        print("requests_post_es got results of type(%s): (%s)" % (type(results).__name__, results))
    return results.json()

def main(verbose=1):
    '''test driver'''
    open_res = urllib_request_urlopen_es(verbose=verbose)
    print("urllib_request_urlopen_es results:")
    print(open_res)
    print()
    got_json = requests_get_es(verbose=verbose)
    print("requests_get_es got results with .json() -> dict:")
    print(got_json)
    print()
    post_res = requests_post_es(verbose=verbose)
    print("requests_post_es results:")
    pprint.pprint(post_res)
    print()

if __name__ == '__main__':
    main()
