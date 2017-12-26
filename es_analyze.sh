#!/usr/local/bin/bash
# See: https://stackoverflow.com/questions/17029902/using-curl-post-with-variables-defined-in-bash-script-functions

query_type=analyze
query_text=${1:-"The YeLLoWing café beLLows slept FURIOUSly."}
prettybool=${2:-true}
do_explain=${3:-false}
def_field1=${4:-description}
def_field2=${5:-name}
tokenizer1=${6:-standard}

gen_data()
{
cat <<EOF
{
    "tokenizer": "$tokenizer1",
    "filter":  [ "lowercase", "asciifolding", {"type": "stop", "stopwords": ["a", "is", "the"]}],
    "text": "$query_text",
    "explain" : "$do_explain"
}
EOF
} 

gen_text()  # no comma after the text
{
cat <<EOF
{
    "text": "$query_text"
}
EOF
} 

# # override index's analyzer settings (observe the stemming):
# curl "http://localhost:9200/get-together/_analyze?pretty=$prettybool\&analyzer=english " -d "$(gen_text)"

# # supply a named analyzer without an index (observe the stemming)
# curl "http://localhost:9200/_analyze?pretty=$prettybool\&analyzer=english " -d "$(gen_text)"

# # use the index's analyzer (observe lowercase)
# curl "http://localhost:9200/get-together/_analyze?pretty=$prettybool" -d "$(gen_text)"

# supply analyzer and text in the data
curl -XPOST "localhost:9200/_analyze?pretty=$prettybool" -H 'Content-Type: application/json' -d "$(gen_data)"

echo
echo "query_type: $query_type"
echo "query_text: $query_text"
echo "prettybool: $prettybool"
# echo "def_field1: $def_field1"
# echo "def_field2: $def_field2"
# echo "analyzer_1: $analyzer_1"

