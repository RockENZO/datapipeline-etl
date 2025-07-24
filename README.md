## Project Overview

This project is designed to manage and process spatial data for Sydney, including building complex points, stairs, recreation centres, and other urban infrastructure. The system provides an interactive web map interface and API endpoints for searching across multiple datasets using technologies including Flask, Elasticsearch, PostgreSQL, and Celery. The project is structured to facilitate easy deployment and scaling using Docker containers.

## 🗺️ Sydney Multi-Dataset Interactive Map

The enhanced map application provides a comprehensive visualization platform for Sydney's spatial data, supporting multiple dataset types including points, polygons, and complex geometries.

### Project Structure

- **es_index_multi_docker.py**: Enhanced multi-dataset indexing script that processes 10+ different spatial datasets with support for both point and polygon geometries.

- **web_map/app.py**: Flask web application serving the interactive map interface with multi-dataset support, search functionality, and dynamic layer controls.

- **web_map/templates/index.html**: Interactive map interface with dataset selector, layer controls, search functionality, and responsive design.

- **start-map.sh**: Automated startup script that handles data verification, service orchestration, health checks, and data indexing.

- **api_data_index.py**: Contains functions to fetch, transform, and index API data into Elasticsearch. Utilizes the `apscheduler` library for periodic updates.
  
- **GNAF_search_api.py**: Sets up a Flask application that provides an API for searching addresses. It uses Celery for asynchronous task processing and connects to a PostgreSQL database.

- **es_search_api.py**: Establishes a Flask application with endpoints for searching data in Elasticsearch indices, supporting multiple dataset types.

- **es_index.py**: Legacy single-dataset indexing script for building complex points (superseded by es_index_multi_docker.py).

- **celery_config.py**: Contains a function to create and configure a Celery instance for task management.

- **docker-compose.yml**: Defines the multi-service architecture including Elasticsearch, PostgreSQL, Redis, web map, data indexer, and API services.

## 🚀 Quick Start - Interactive Map Application

### **One-Command Startup**
```bash
./start-map.sh
```

This automated script will:
1. **Verify Data Files** - Check all 10+ dataset files are present
2. **Build & Start Services** - Launch Elasticsearch, web map, and supporting services
3. **Index Datasets** - Process and index 76,000+ spatial data points
4. **Health Checks** - Ensure all services are ready
5. **Launch Map** - Interactive map available at http://localhost:5002

### **Shutdown Process**
```bash
# Stop all services
docker-compose down

# Stop services and remove data volumes (complete cleanup)
docker-compose down -v
```

### **Available Datasets**
The map includes the following Sydney datasets:
- **Building Complex Points** (76,200 records) - Major buildings and complexes
- **Stairs** (523 records) - Public stairways and steps
- **Recreation Centres** (6 records) - Community recreation facilities
- **Information Kiosks** (2 records) - Public information displays
- **Business Rate Categories** (3 records) - Commercial zone classifications
- **Free 15-Minute Parking** - Short-term parking zones
- **Ticket Parking Rates** - Paid parking areas
- **NSW Ambulance Stations** - Emergency service locations
- **Height of Building** - Building height data
- **Library Details** - Public library information

### **Map Features**
- **Interactive Map Interface** - Pan, zoom, and explore Sydney
- **Dataset Selector** - Switch between different data types
- **Search Functionality** - Find specific locations or features
- **Layer Controls** - Toggle dataset visibility
- **Responsive Design** - Works on desktop and mobile devices

### **Service Management**
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f web_map
docker-compose logs data_indexer

# Restart services
docker-compose restart

# Access map
open http://localhost:5002
```

## Setup Instructions (Legacy/Development)

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
   - **Interactive Map**: `http://localhost:5002` (Main application)
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
  - **Web Map Search**: Access the interactive map at http://localhost:5002 and use the built-in search interface
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
  - To search for parking permits areas data:
    ```
    curl "http://localhost:5003/es_search/parking_permits_areas?query=Pyrmont"
    ```
  - To search for Natural Disaster Declaration data:
    ```
    curl "http://localhost:5003/es_search/lga_ndd_total?type=Polygon"
    ```
  - To search for Destination Zones data:
    ```
    curl "http://localhost:5003/es_search/dzn?query=Bombala"
    ```
  - To search for Library Accessibility Information:
    ```
    curl "http://localhost:5003/es_search/library_details/has_feature?field=Toilet_Accessible"
    ```

### Conclusion

This project provides a comprehensive spatial data visualization platform for Sydney, featuring an interactive web map interface and robust API framework for managing multiple datasets. The enhanced multi-dataset architecture supports various geometry types (points, polygons, multipolygons) and provides both visual exploration through the web interface and programmatic access through REST APIs. By leveraging Docker, the application can be easily deployed and scaled, ensuring efficient data processing, indexing, and retrieval across 76,000+ spatial data points.