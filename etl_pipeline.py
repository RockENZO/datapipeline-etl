# handles the Extract, Transform, Load (ETL) process. The ETL process reads the GNAF dataset, transforms it into a JSON format, and loads it into a MongoDB database. The ETL process is executed once to load the data into the database.
import pandas as pd
from pymongo import MongoClient
import os

# MongoDB connection setup
client = MongoClient('mongodb://mongodb:27017/')
db = client['geospatial_data']
collection = db['processed_data']

def read_psv(file_path):
    return pd.read_csv(file_path, sep='|')

def transform_data(df):
    # Transformation: Convert to JSON format
    return df.to_dict(orient='records')

def load_to_mongo(data):
    collection.insert_many(data)

def etl_process(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.psv'):
            file_path = os.path.join(directory, filename)
            df = read_psv(file_path)
            transformed_data = transform_data(df)
            load_to_mongo(transformed_data)
            print(f"Processed {filename}")

if __name__ == "__main__":
    data_directory = 'g-naf_nov24_allstates_gda2020_psv_1017/G-NAF/G-NAF NOVEMBER 2024/Standard'
    etl_process(data_directory)