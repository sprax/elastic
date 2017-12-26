#!/usr/local/bin/bash
# See: https://stackoverflow.com/questions/17029902/using-curl-post-with-variables-defined-in-bash-script-functions

query_type=query_string
query_text=${1:-"YeLLoWing café beLLows slept FURIOUSly."}
prettybool=${2:-true}
def_field1=${3:-description}
def_field2=${4:-name}
def_operat=${5:-AND}
analyzer_1=${6:-standard}
do_explain=${7:-true}

gen_analyzer()
{
cat <<EOF
{
    "query": {
        "$query_type" : {
            "query"   : "+($query_text | search) -frittata",
            "fields"  : ["$def_field1", "$def_field2"],
            "analyzer": "$analyzer_1",
            "lenient" : "false",
            "default_operator": "and"
        }
    },
    "tokenizer": "standard",
    "filter":  [ "lowercase", "asciifolding" ],
    "text": "YeLLoWing café beLLows slept FURIOUSly.",
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

# override index's analyzer settings (observe the stemming):
# curl "http://localhost:9200/get-together/_analyze?pretty=$prettybool\&analyzer=english " -d "$(gen_text)"

# supply a named analyzer without an index (observe the stemming)
# curl "http://localhost:9200/_analyze?pretty=$prettybool\&analyzer=english " -d "$(gen_text)"

# use the index's analyzer (observe lowercase)
curl "http://localhost:9200/get-together/_analyze?pretty=$prettybool" -d "$(gen_text)"

# supply analyzer and text in the data
# curl -XPOST "localhost:9200/_analyze?pretty=$prettybool" -H 'Content-Type: application/json' -d "$(gen_data)"

echo
echo "query_type: $query_type"
echo "query_text: $query_text"
echo "def_field1: $def_field1"
echo "def_field2: $def_field2"
echo "analyzer_1: $analyzer_1"

