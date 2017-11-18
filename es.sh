#!/usr/bin/sh
# See: https://stackoverflow.com/questions/17029902/using-curl-post-with-variables-defined-in-bash-script-functions

query_type=${1:-query_string}
query_term=${2:-"Group of Clojure"}
def_fields=${3:-description}

gen_fields()
{
  if $query_type = "query_string"; then
      ", default_field: ${def_fields}"
  else
      ""
  fi
}

gen_data()
{
cat <<EOF
{
    "query": {
        "$query_type": {
            "query": "$query_term"
            $(gen_fields)
        }
    }
}
EOF
} 

curl "http://localhost:9200/get-together/_search" -d "$(gen_data)"

echo
echo "query_type: $query_type"
echo "query_term: $query_term"
echo "def_fields: $def_fields"

