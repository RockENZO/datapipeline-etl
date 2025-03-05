### Process
1. In your docker environment pull the image using `docker pull minus34/gnafloader:latest`
2. Run using `docker run --publish=5433:5432 minus34/gnafloader:latest`
3. Access Postgres in the container via port `5433`. Default login is - user: `postgres`, password: `password`
### To check the search path
`psql -h localhost -p 5433 -U postgres -d postgres`
### Changing search path
`SET search_path TO gnaf_202502, public;`
### Start Redis server
`brew services start redis`
### Run Celery Worker
`celery -A search_api.celery worker --loglevel=info`
### Stop Redis server
`brew services stop redis`

### Example Usage:
To search with only the street number: `curl "http://localhost:5001/search?address=95"`
To search with street number and name: `curl "http://localhost:5001/search?address=95%20Balo"`
To search with full address: `curl "http://localhost:5001/search?address=95%20Balo%20Street"`
To search with state: `curl "http://localhost:5001/search?address=95%20Balo%20Street&state=NSW"`