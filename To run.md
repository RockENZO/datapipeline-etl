### Process
1. In your docker environment pull the image using `docker pull minus34/gnafloader:latest`
2. Run using `docker run --publish=5433:5432 minus34/gnafloader:latest`
3. Access Postgres in the container via port `5433`. Default login is - user: `postgres`, password: `password`
### To check the search path
`psql -h localhost -p 5433 -U postgres -d postgres`
### Changing search path
`SET search_path TO gnaf_202411, public;`
### Example usage
`curl "http://localhost:5001/search?address=95%20Balo%20Street"`