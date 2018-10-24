#!/usr/bin/sh
# See: https://stackoverflow.com/questions/17029902/using-curl-post-with-variables-defined-in-bash-script-functions

query_type=${1:-query_string}
query_term=${2:-knowledge}
def_fields=${3:-description}

gen_data()
{
cat <<EOF
{
    "query": {
        "$query_type": {
            "query": "$query_term",
            "default_field": "$def_fields"
        }
    }
}
EOF
} 

# curl "http://localhost:9200/get-together/_search" -d "$(gen_data)"

req_body=$(cat <<EOF
{
    "query": {
        "$query_type": {
            "query": "$query_term",
            "default_field": "$def_fields"
        }
    }
}
EOF
)

curl -i -X POST "http://localhost:9200/get-together/_search" -d "$req_body"

echo
echo "query_type: $query_type"
echo "query_term: $query_term"
echo "def_fields: $def_fields"

