#!/bin/bash

# Sydney Multi-Dataset Map - Startup Script
echo "🗺️ Starting Sydney Multi-Dataset Interactive Map System..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if data files exist
echo "📁 Checking data files..."
data_files=(
    "BuildingComplexPoint_EPSG4326.json"
    "Stairs.geojson"
    "Recreation_centres.geojson"
    "Library_details.geojson"
    "Information_kiosks.geojson"
    "NSW Ambulance Station_EPSG4326.json"
    "Business_rate_category.geojson"
    "Free_15_minute_parking.geojson"
    "Residential_waste_recovery.geojson"
    "Ticket_parking_rates.geojson"
)

missing_files=()
for file in "${data_files[@]}"; do
    if [ ! -f "./data/$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "⚠️  Some data files are missing:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo "The system will still start, but some datasets won't be available."
fi

echo "📋 Building and starting services..."

# Build and start all services
docker-compose up --build -d

echo "⏳ Waiting for services to be ready..."

# Wait for Elasticsearch to be healthy
echo "🔍 Waiting for Elasticsearch..."
until curl -s http://localhost:9200/_cluster/health | grep -q '"status":"green"\|"status":"yellow"'; do
    echo "   Still waiting for Elasticsearch..."
    sleep 5
done
echo "✅ Elasticsearch is ready!"

# Wait for the web map to be healthy
echo "🗺️  Waiting for Web Map service..."
until curl -s http://localhost:5002/health | grep -q '"status":"healthy"'; do
    echo "   Still waiting for Web Map..."
    sleep 3
done
echo "✅ Web Map is ready!"

# Check indexing status
echo "📊 Checking data indexing status..."
sleep 15  # Give indexer time to start

# Wait for data to be indexed
echo "⏳ Indexing multiple datasets..."
datasets=(
    "building_complex_points"
    "stairs"
    "recreation_centres"
    "library_details"
    "information_kiosks"
    "nsw_ambulance_stations"
    "business_rate_category"
    "free_15_minute_parking"
    "residential_waste_recovery"
    "ticket_parking_rates"
)

total_indexed=0
for dataset in "${datasets[@]}"; do
    for i in {1..30}; do
        count=$(curl -s "http://localhost:9200/${dataset}/_count" 2>/dev/null | grep -o '"count":[0-9]*' | cut -d':' -f2 2>/dev/null || echo "0")
        if [ ! -z "$count" ] && [ "$count" -gt 0 ]; then
            echo "✅ $dataset: $count documents indexed"
            total_indexed=$((total_indexed + count))
            break
        fi
        if [ $i -eq 30 ]; then
            echo "⚠️  $dataset: No data found (file may be missing)"
        fi
        sleep 2
    done
done

echo ""
echo "🎉 Multi-Dataset Map System is ready!"
echo ""
echo "� Total documents indexed: $total_indexed"
echo ""
echo "🌐 Access the interactive map at: http://localhost:5002"
echo "🔍 Search API at: http://localhost:5003"
echo "🏠 GNAF Address API at: http://localhost:5001"
echo "📊 Elasticsearch at: http://localhost:9200"
echo ""
echo "📋 Available Datasets:"
echo "   🏢 Building Complex Points"
echo "   🚶 Stairs & Steps"
echo "   🏃 Recreation Centres"
echo "   📚 Libraries"
echo "   ℹ️  Information Kiosks"
echo "   🚑 Ambulance Stations"
echo "   🏪 Business Rate Categories"
echo "   🅿️  Free 15 Minute Parking"
echo "   ♻️  Waste Recovery Points"
echo "   🎫 Ticket Parking"
echo ""
echo "🛑 To stop the system, run: docker-compose down"
echo "🔄 To view logs, run: docker-compose logs -f"
echo ""
