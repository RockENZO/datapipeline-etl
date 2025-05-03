## Project Overview

This project is designed to manage and process data related to pedestrian counts and address searches using various technologies including Flask, Elasticsearch, PostgreSQL, and Celery. The project is structured to facilitate easy deployment and scaling using Docker containers.

### Project Structure

- **api_data_index.py**: Contains functions to fetch, transform, and index API data into Elasticsearch. Utilizes the `apscheduler` library for periodic updates.
  
- **GNAF_search_api.py**: Sets up a Flask application that provides an API for searching addresses. It uses Celery for asynchronous task processing and connects to a PostgreSQL database.

- **es_search_api.py**: Establishes a Flask application with endpoints for searching data in Elasticsearch indices, specifically for building complex points and pedestrian counts.

- **es_index.py**: Initializes an Elasticsearch index for building complex points, defines the index mapping, and bulk indexes data from a JSON file.

- **celery_config.py**: Contains a function to create and configure a Celery instance for task management.

- **docker-compose.yml**: Defines the services for the application, including Elasticsearch, PostgreSQL, and Redis, along with their configurations.

### Setup Instructions

1. **Clone the Repository**: 
   Clone this repository to your local machine.

2. **Install Docker**: 
   Ensure that Docker and Docker Compose are installed on your machine.

3. **Build Docker Images**: 
   Navigate to the project directory and build the Docker images using the following command:
   ```
   docker-compose build
   ```

4. **Start Services**: 
   Start all services defined in the `docker-compose.yml` file:
   ```
   docker-compose up -d
   ```

5. **Access Services**: 
   - The GNAF search API will be available at `http://localhost:5001/search`.
   - The Elasticsearch search API will be available at `http://localhost:5003/es_search`.

6. **Stop and Clean Up**: 
   To stop and remove all containers, run:
   ```
   docker-compose down
   ```

## Gnaf loader
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

<!-- ### Example Usage(GNAF):
To search with only the street number: `curl "http://localhost:5001/search?address=95"`
To search with street number and name: `curl "http://localhost:5001/search?address=95%20Balo"`
To search with full address: `curl "http://localhost:5001/search?address=95%20Balo%20Street"`
To search with state: `curl "http://localhost:5001/search?address=95%20Balo%20Street&state=NSW"` -->

## Elastic Search Engine
### Pull elasticsearch docker image
`docker pull docker.elastic.co/elasticsearch/elasticsearch:7.17.4`
### Run elasticsearch in docker
`docker run -d --name elasticsearch -p 9200:9200 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.17.4`
### Delete existing index
`curl -X DELETE "http://localhost:9200/building_complex_points"`
### Verify the data indexed
`curl -X GET "http://localhost:9200/building_complex_points/_search?pretty"`
`curl -X GET "http://localhost:9200/pedestrian_counts/_search?pretty"`
`curl -X GET "http://localhost:9200/stairs/_search?pretty"`
### List all indices in Elasticsearch
`curl -X GET "http://localhost:9200/_cat/indices?v"`
### Stop elasticsearch docker container
`docker stop elasticsearch`
### Remove stopped es container
`docker rm elasticsearch`

<!-- ### ES data query usage:
To search in Elasticsearch;
`curl "http://localhost:5003/es_search/building_complex_points?query=GREENWICH%20HOSPITAL"`
`curl "http://localhost:5003/es_search/pedestrian_counts?query=Park%20Street"` -->


### Usage Examples

- **GNAF Search API**:
  - To search with only the street number: 
    ```
    curl "http://localhost:5001/search?address=95"
    ```
  - To search with street number and name: 
    ```
    curl "http://localhost:5001/search?address=95%20Balo"
    ```
  - To search with full address: 
    ```
    curl "http://localhost:5001/search?address=95%20Balo%20Street"
    ```
  - To search with state: 
    ```
    curl "http://localhost:5001/search?address=95%20Balo%20Street&state=NSW"
    ```

- **Elasticsearch Queries**:
  - To search in Elasticsearch for building complex points:
    ```
    curl "http://localhost:5003/es_search/building_complex_points?query=GREENWICH%20HOSPITAL"
    ```
  - To search for pedestrian counts:
    ```
    curl "http://localhost:5003/es_search/pedestrian_counts?query=Park%20Street"
    ```
  - To search for height of building:
    ```
    curl "http://localhost:5003/es_search/height_of_building?query=Liverpool"
    ```
  - To search for stairs data:
    ```
    curl "http://localhost:5003/es_search/stairs?query=Billyard"
    ```
  - To search for recreation centres:
    ```
    curl "http://localhost:5003/es_search/recreation_centres?query=Redfern"
    ```
  - To search for information kiosks:
  ```
  curl "http://localhost:5003/es_search/information_kiosks?query=Customs"
  ```
  - To search for ambulance station:
  ```
  curl "http://localhost:5003/es_search/ambulance_stations?query=CALVARY"
  ```
  - To search for bicycle network data:
  ```
  curl "http://localhost:5003/es_search/bicycle_network?query=Carrington"
  ```
  - To search for free 15 mins parking:
  ```
  curl "http://localhost:5003/es_search/free_15_minute_parking?query=King"
  ```
  - To search for residential waste recovery data:
  ```
  curl "http://localhost:5003/es_search/residential_waste_recovery?query=All"
  ```
  - To search for business rate category shape data:
  ```
  curl "http://localhost:5003/es_search/business_rate_category?query=Business"
  ```
  - To search for urban centres and localities:
  ```
  curl "http://localhost:5003/es_search/ucl?query=Sydney"
  ```
  - To search for ticket parking rates data:
  ```
  curl "http://localhost:5003/es_search/ticket_parking_rates?query=2022"
  ```



### Conclusion

This project provides a robust framework for managing pedestrian count data and address searches using modern technologies. By leveraging Docker, the application can be easily deployed and scaled, ensuring efficient data processing and retrieval.