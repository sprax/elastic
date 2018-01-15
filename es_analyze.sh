#!/usr/local/bin/bash
# See: https://stackoverflow.com/questions/17029902/using-curl-post-with-variables-defined-in-bash-script-functions

operations=analyze
query_text=${1:-"Ye Olde YeLLoWing café beLLows MiCe were sleeping FURIOUSly."}
prettytrue=${2:-true}
porterstem=${3:-true}
do_explain=${4:-false}
tokenizer1=${5:-standard}

# NOTES: filters are applied in the order listed, so stemming exceptions (keywords)
# and overrides must be listed before the stemmer, and overrides that convert other
# words into to stop words should precede stopword removal.
gen_data()
{
cat <<EOF
{
    "tokenizer": "$tokenizer1",
    "filter": [ "lowercase", "asciifolding",
                {"type": "keyword_marker", "keywords": ["sleeping"]},
                {"type": "stemmer_override", "rules": [ "mice=>mouse", "were=>was"]},
                {"type": "stop", "stopwords": ["a", "is", "the", "was"]},
                "porter_stem"
              ],
    "text": "$query_text",
    "explain": "$do_explain"
}
EOF
}

gen_text()  # no comma after the text
{
    echo "{ \"text\": \"$query_text\" }"
}

# # supply a named analyzer without an index (observe the stemming)
# curl "http://localhost:9200/_analyze?pretty=$prettytrue\&analyzer=english " -d "$(gen_text)"

# # override index's analyzer settings (observe the stemming):
# curl "http://localhost:9200/get-together/_analyze?pretty=$prettytrue\&analyzer=english " -d "$(gen_text)"

# use the index's analyzer (observe lowercase)
curl "http://localhost:9200/kbdl/_analyze?pretty=$prettytrue" -d "$(gen_text)"

# # supply analyzer and text in the data
# curl -XPOST "localhost:9200/_analyze?pretty=$prettytrue" -H 'Content-Type: application/json' -d "$(gen_data)"

echo
echo "operations: $operations"
echo "query_text: $query_text"
echo "prettytrue: $prettytrue"
echo "porterstem: $porterstem"
echo "tokenizer1: $tokenizer1"
echo "do_explain: $do_explain"
