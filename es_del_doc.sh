#!/usr/local/bin/bash

query_type=query_string
query_term=${1:-opportunity}
def_field1=${2:-description}
def_field2=${3:-name}
def_operat=${4:-AND}
analyzer_1=${5:-standard}
do_explain=${6:-true}

gen_data()
{
cat <<EOF
{
    "query": {
        "$query_type" : {
            "query"   : "+($query_term | search) -frittata",
            "fields"  : ["$def_field1", "$def_field2"],
            "analyzer": "$analyzer_1",
            "lenient" : "false",
            "default_operator": "and"
        }
    },
    "explain" : "$do_explain"
}
EOF
} 

curl "http://localhost:9200/get-together/_search?pretty" -d "$(gen_data)"

echo
echo "query_type: $query_type"
echo "query_term: $query_term"
echo "def_field1: $def_field1"
echo "def_field2: $def_field2"
echo "analyzer_1: $analyzer_1"

