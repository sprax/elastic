#!/usr/bin/env bash
# See https://dzone.com/articles/23-useful-elasticsearch-example-queries

ADDRESS=$1
BOOKS="bookdb_index"

if [ -z $ADDRESS ]; then
  ADDRESS="localhost:9200"
fi


curl -s -XPUT $ADDRESS/$BOOKS -d '{ "settings": { "number_of_shards": 1 }}'

# Wait for index to become yellow
curl -s "$ADDRESS/$BOOKS/_health?wait_for_status=yellow&timeout=10s" > /dev/null
echo
echo "Done creating '$BOOKS' index."

curl -s -XPOST $ADDRESS/$BOOKS/book/_bulk -d'
    { "index": { "_id": 1 }}
    { "title": "Elasticsearch: The Definitive Guide", "authors": ["clinton gormley", "zachary tong"], "summary" : "A distibuted real-time search and analytics engine", "publish_date" : "2015-02-07", "num_reviews": 20, "publisher": "oreilly" }
    { "index": { "_id": 2 }}
    { "title": "Taming Text: How to Find, Organize, and Manipulate It", "authors": ["grant ingersoll", "thomas morton", "drew farris"], "summary" : "organize text using approaches such as full-text search, proper name recognition, clustering, tagging, information extraction, and summarization", "publish_date" : "2013-01-24", "num_reviews": 12, "publisher": "manning" }
    { "index": { "_id": 3 }}
    { "title": "Elasticsearch in Action", "authors": ["radu gheorge", "matthew lee hinman", "roy russo"], "summary" : "build scalable search applications using Elasticsearch without having to do complex low-level programming or understand advanced data science algorithms", "publish_date" : "2015-12-03", "num_reviews": 18, "publisher": "manning" }
    { "index": { "_id": 4 }}
    { "title": "Solr in Action", "authors": ["trey grainger", "timothy potter"], "summary" : "Comprehensive guide to implementing a scalable search engine using Apache Solr", "publish_date" : "2014-04-05", "num_reviews": 23, "publisher": "manning" }
'

# TO SEE THE MAPPING FOR THIS INDEX:
curl -XGET http://localhost:9200/$BOOKS/book/_mapping?pretty

# GET /bookdb_index/book/_search?q=title:in action
# GET /bookdb_index/book/_search?q=guide =====>  http://localhost:9200/bookdb_index/book/_search/?pretty=true&q=guide
curl -s -XGET $ADDRESS/$BOOKS/book/_search?pretty -d '
{
    "query": {
        "multi_match" : {
            "query" : "guide",
            "fields" : ["_all"]
        }
    }
}
'

# Full body DSL
# Browser: http://localhost:9200/bookdb_index/book/_search/?pretty=true&q=title:in%20action
# URL = "http://$ADDRESS/$BOOKS/book/_search/?q=title:in%20action"
curl -s -XPOST $ADDRESS/$BOOKS/book/_search?pretty -d '
{
    "query": {
        "match" : {
            "title" : "in action"
        }
    },
    "size": 2,
    "from": 0,
    "_source": [ "title", "summary", "publish_date" ],
    "highlight": {
        "fields" : {
            "title" : {}
        }
    }
}
'

# Multi-field
curl -s -XPOST $ADDRESS/$BOOKS/book/_search?pretty -d '
{
    "query": {
        "multi_match" : {
            "query" : "elasticsearch guide",
            "fields": ["title", "summary"]
        }
    }
}
'

# Boosting
curl -s -XPOST $ADDRESS/$BOOKS/book/_search?pretty -d '
{
    "query": {
        "multi_match" : {
            "query" : "elasticsearch guide",
            "fields": ["title", "summary^3"]
        }
    },
    "_source": ["title", "summary", "publish_date"]
}
'

