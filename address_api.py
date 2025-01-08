# sets up a Flask API to query the data. The API will accept a POST request with an address alias PID and return the coordinates of the address. The API will use the GNAF dataset loaded in memory to find the coordinates.
from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Load GNAF dataset
gnaf_data = pd.read_csv('g-naf_nov24_allstates_gda2020_psv_1017/G-NAF/G-NAF NOVEMBER 2024/Standard/VIC_ADDRESS_ALIAS_psv.psv', sep='|')

@app.route('/get_coordinates', methods=['POST'])
def get_coordinates():
    address = request.json.get('address')
    # Logic to find coordinates
    result = gnaf_data[gnaf_data['ADDRESS_ALIAS_PID'] == address]
    if not result.empty:
        coordinates = {
            'latitude': result.iloc[0]['LATITUDE'],
            'longitude': result.iloc[0]['LONGITUDE']
        }
        return jsonify(coordinates)
    else:
        return jsonify({'error': 'Address not found'}), 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)