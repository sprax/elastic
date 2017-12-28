#!/usr/bin/env python3
'''pyton translation of es_analyze.sh'''

import json
import requests
import urllib

# operations=analyze
# query_text=${1:-"The YeLLoWing café beLLows MiCe were sleeping FURIOUSly."}
# prettytrue=${2:-true}
# porterstem=${3:-true}
# do_explain=${4:-false}
# tokenizer1=${5:-standard}
def show_vars():
    print("operations: $operations")
    print("query_text: $query_text")
    print("prettytrue: $prettytrue")
    print("porterstem: $porterstem")
    print("tokenizer1: $tokenizer1")
    print("do_explain: $do_explain")

DEFAULT_TEXT = "The YeLLoWing café beLLows MiCe were sleeping FURIOUSly."

# NOTES: filters are applied in the order listed, so stemming exceptions (keywords)
# and overrides must be listed before the stemmer, and overrides that convert other
# words into to stop words should precede stopword removal.
def json_data(query_text=DEFAULT_TEXT, tokenizer="standard", do_explain=False):
    '''data payload as JSON string'''
    explain = "true" if do_explain else "false"
    return '''{
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
    ''' % (query_text, tokenizer, explain)

def json_text(text_to_analyze=DEFAULT_TEXT):
    '''no comma after the text'''
    return "{ \"text\": \"%s\" }" % text_to_analyze


# # supply a named analyzer without an index (observe the stemming)
# curl "http://localhost:9200/_analyze?pretty=$prettytrue\&analyzer=english " -d "$(gen_text)"

# # override index's analyzer settings (observe the stemming):
# curl "http://localhost:9200/get-together/_analyze?pretty=$prettytrue\&analyzer=english " -d "$(gen_text)"

# # use the index's analyzer (observe lowercase)
# curl "http://localhost:9200/get-together/_analyze?pretty=$prettytrue" -d "$(gen_text)"

# # supply analyzer and text in the data
# def get_out():
#     '''
#     curl -XPOST "localhost:9200/_analyze?pretty=$prettytrue" -H 'Content-Type: application/json' -d "$(gen_data)"
#     '''
#     output = urllib.request.urlopen('http://www.somewebsite.com').read()
#
#
# '''https://stackoverflow.com/questions/25491090/how-to-use-python-to-execute-a-curl-command'''
# import requests
# r = requests.get('https://github.com/timeline.json')
# r.json()
# If you look for further information, in the Quickstart section, they have lots of working examples.
#
# EDIT:
#
# For your specific curl translation:

PRETTY = "true"
url = "http://localhost:9200/_analyze?pretty=%s" % PRETTY
payload = json_text()   # json_data()
headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
results = requests.post(url, data=payload, headers=headers)

print(results)
