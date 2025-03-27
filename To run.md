### Process
- Using docker-compose to start Elasticsearch, Postgres, and Redis:
`docker-compose up -d`
- To stop and clean up all containers:
`docker-compose down`

### Gnaf loader
1. Pull the image using `docker pull minus34/gnafloader:latest`
2. Run using `docker run --publish=5433:5432 minus34/gnafloader:latest`
3. Access Postgres in the container via port `5433`. Default login is - user: `postgres`, password: `password`
### To check the search path
`psql -h localhost -p 5433 -U postgres -d postgres`
### Changing search path
`SET search_path TO gnaf_202502, public;`
### Start Redis server
`brew services start redis`
### Check if Redis is running
`redis-cli ping`
### Run Celery Worker
`celery -A search_api.celery worker --loglevel=info`
### Stop Redis server
`brew services stop redis`

### Example Usage(GNAF):
To search with only the street number: `curl "http://localhost:5001/search?address=95"`
To search with street number and name: `curl "http://localhost:5001/search?address=95%20Balo"`
To search with full address: `curl "http://localhost:5001/search?address=95%20Balo%20Street"`
To search with state: `curl "http://localhost:5001/search?address=95%20Balo%20Street&state=NSW"`

### Pull elasticsearch docker image
`docker pull docker.elastic.co/elasticsearch/elasticsearch:7.17.4`
### Run elasticsearch in docker
`docker run -d --name elasticsearch -p 9200:9200 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.17.4`
### Delete existing index
`curl -X DELETE "http://localhost:9200/building_complex_points"`
### Verify the data indexed
`curl -X GET "http://localhost:9200/building_complex_points/_search?pretty"`
### Stop elasticsearch docker container
`docker stop elasticsearch`
### Remove stopped es container
`docker rm elasticsearch`
### ES data query usage:
To search in Elasticsearch;
`curl "http://localhost:5003/es_search?query=GREENWICH%20HOSPITAL"`

