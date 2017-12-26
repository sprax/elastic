#!/usr/local/bin/bash
# See: https://stackoverflow.com/questions/17029902/using-curl-post-with-variables-defined-in-bash-script-functions

operations=analyze
query_text=${1:-"The YeLLoWing café beLLows slept FURIOUSly."}
prettytrue=${2:-true}
porterstem=${3:-true}
do_explain=${4:-false}
tokenizer1=${5:-standard}

gen_data()
{
cat <<EOF
{
    "tokenizer": "$tokenizer1",
    "filter": [ "lowercase", "asciifolding", "porter_stem",
                    {"type": "stop", "stopwords": ["a", "is", "the"]}
              ],
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
# curl "http://localhost:9200/get-together/_analyze?pretty=$prettytrue\&analyzer=english " -d "$(gen_text)"

# # supply a named analyzer without an index (observe the stemming)
# curl "http://localhost:9200/_analyze?pretty=$prettytrue\&analyzer=english " -d "$(gen_text)"

# # use the index's analyzer (observe lowercase)
# curl "http://localhost:9200/get-together/_analyze?pretty=$prettytrue" -d "$(gen_text)"

# supply analyzer and text in the data
curl -XPOST "localhost:9200/_analyze?pretty=$prettytrue" -H 'Content-Type: application/json' -d "$(gen_data)"

echo
echo "operations: $operations"
echo "query_text: $query_text"
echo "prettytrue: $prettytrue"
echo "porterstem: $porterstem"
echo "tokenizer1: $tokenizer1"
echo "do_explain: $do_explain"

