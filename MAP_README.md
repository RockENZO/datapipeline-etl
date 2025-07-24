# Sydney Building Complex Points Map

A comprehensive mapping solution for visualizing Sydney's building complex points data using Docker Compose for streamlined deployment.

## 🏗️ Architecture

This system consists of multiple containerized services:

- **Web Map** (Port 5000): Interactive Leaflet-based map interface
- **Elasticsearch** (Port 9200): Search engine for spatial data
- **PostgreSQL** (Port 5433): GNAF address database
- **Redis** (Port 6379): Cache and message broker
- **GNAF API** (Port 5001): Address search API
- **Elasticsearch Search API** (Port 5003): Building data search API
- **Data Indexer**: Automated data loading service

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Building complex points data file: `BuildingComplexPoint_EPSG4326.json`

### 1. Start the System

```bash
./start-map.sh
```

This script will:
- Build all Docker containers
- Start all services
- Index the building complex points data
- Verify system health

### 2. Access the Map

Open your browser and navigate to: **http://localhost:5000**

## 🗺️ Features

### Interactive Map
- **Search Buildings**: Search by building names (e.g., "Hospital", "School", "Centre")
- **Visual Differentiation**: Named buildings appear in red, others in gray
- **Popup Information**: Click on any point to see building details
- **Dynamic Loading**: Data loads based on current map view for performance
- **Responsive Design**: Works on desktop and mobile devices

### Search Capabilities
- Real-time search as you type
- Bounding box filtering for efficient data loading
- Building type categorization
- Coordinate display

### API Endpoints

#### Building Complex Points
```bash
# Search buildings in current map view
GET /api/search/building_complex_points?query=hospital&bbox=151.1,33.8,151.3,-33.9

# Get detailed building information
GET /api/building_complex_points/{topoid}
```

## 🔧 Development

### Project Structure
```
datapipeline-etl/
├── web_map/                 # Web mapping application
│   ├── app.py              # Flask application
│   ├── templates/          # HTML templates
│   ├── Dockerfile          # Web app container
│   └── requirements.txt    # Python dependencies
├── data/                   # Data files
│   └── BuildingComplexPoint_EPSG4326.json
├── docker-compose.yml      # Service orchestration
├── es_index_docker.py      # Data indexing script
├── GNAF_search_api.py      # Address search API
├── es_search_api.py        # Elasticsearch search API
└── start-map.sh           # Startup script
```

### Adding New Datasets

1. **Add data file** to the `data/` directory
2. **Update indexing script** (`es_index_docker.py`) to include new dataset mapping
3. **Add search endpoint** in `web_map/app.py`
4. **Update map interface** to display new data layer

### Environment Variables

- `ELASTICSEARCH_HOST`: Elasticsearch server hostname
- `POSTGRES_HOST`: PostgreSQL server hostname  
- `REDIS_HOST`: Redis server hostname
- `FLASK_ENV`: Flask environment (development/production)

## 🛠️ Management Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web_map
```

### Rebuild and Restart
```bash
docker-compose up --build -d
```

### Check Service Health
```bash
# Web Map health
curl http://localhost:5000/health

# Elasticsearch health
curl http://localhost:9200/_cluster/health

# Check indexed data count
curl http://localhost:9200/building_complex_points/_count
```

## 📊 Data Information

### Building Complex Points
- **Source**: NSW Spatial Services
- **Format**: GeoJSON with EPSG:4326 projection
- **Fields**: Building name, type, coordinates, administrative data
- **Index**: `building_complex_points`

### Search Fields
- `properties.generalname`: Primary building name
- `properties.alternativelabel`: Alternative building names
- `properties.buildingcomplextype`: Building type classification

## 🔍 API Usage Examples

### Search Buildings
```bash
# Search for hospitals
curl "http://localhost:5000/api/search/building_complex_points?query=hospital"

# Search within bounding box (Sydney CBD)
curl "http://localhost:5000/api/search/building_complex_points?bbox=151.195,-33.88,151.225,-33.86"

# Combined search and location filter
curl "http://localhost:5000/api/search/building_complex_points?query=school&bbox=151.1,-33.9,151.3,-33.8"
```

### Building Details
```bash
# Get specific building information
curl "http://localhost:5000/api/building_complex_points/123456"
```

## 🚨 Troubleshooting

### Services Not Starting
1. Check Docker is running: `docker ps`
2. Check port availability: `netstat -an | grep :5000`
3. View service logs: `docker-compose logs [service_name]`

### Data Not Loading
1. Verify data file exists: `ls -la data/`
2. Check indexer logs: `docker-compose logs data_indexer`
3. Test Elasticsearch: `curl http://localhost:9200/_cat/indices`

### Map Not Displaying Points
1. Check browser console for JavaScript errors
2. Verify API response: `curl http://localhost:5000/api/search/building_complex_points`
3. Check Elasticsearch data: `curl http://localhost:9200/building_complex_points/_search`

## 📈 Performance

### Optimization Features
- **Bounding box filtering**: Only loads data for visible map area
- **Result limiting**: Configurable maximum results per request
- **Elasticsearch indexing**: Fast spatial queries
- **Docker health checks**: Ensures service reliability

### Scaling Recommendations
- Use Elasticsearch cluster for large datasets
- Implement Redis caching for frequent queries
- Add CDN for static map tiles
- Use nginx reverse proxy for production

## 🔒 Security

### Production Considerations
- Enable Elasticsearch security features
- Use environment variables for sensitive data
- Implement API rate limiting
- Add HTTPS termination
- Regular security updates for Docker images

## 📝 Next Steps

To add more datasets to the map:

1. **Prepare data**: Ensure GeoJSON format with proper coordinates
2. **Update indexer**: Add mapping definitions in `es_index_docker.py`
3. **Add API endpoints**: Create search endpoints in `web_map/app.py`
4. **Update UI**: Add layer controls and styling in the map interface
5. **Test**: Verify data loads and displays correctly

This system provides a solid foundation for expanding to include all the datasets in your pipeline (stairs, recreation centres, parking, etc.).
