#!/usr/local/bin/bash
# See: https://stackoverflow.com/questions/17029902/using-curl-post-with-variables-defined-in-bash-script-functions

query_type="match"
query_term=${1:-Mike}
user_term1=${2:-Mick}
def_field1=${3:-members}
def_field2=${4:-organizer}


gen_data()
{
cat <<EOF
{
    "query" : {
        "$query_type": {
            "$def_field1" : "$query_term"
        }
    },
    "suggest" : {
        "my-suggest-1" : {
            "text" : "$user_term1",
            "term" : {
                "field" : "$def_field1"
            }
        }
    },
    "suggest" : {
        "my-suggest-2" : {
            "text" : "$user_term1",
            "term" : {
                "field" : "$def_field2"
            }
        }
    }
}
EOF
} 

curl "http://localhost:9200/get-together/_search" -d "$(gen_data)"

echo
echo "query_type: $query_type"
echo "query_term: $query_term"
echo "user term1: $user_term1"
echo "def_field1: $def_field1"
echo "def_field2: $def_field2"

