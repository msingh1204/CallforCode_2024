import os
from datetime import datetime

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import geopandas as gpd

import xarray as xr
import pandas as pd
import numpy as np 

from geopy.exc import GeocoderServiceError

from utils import (
    get_shortest_safe_route,
    query_IDA_calls,
    return_sensor_coords,
    return_exclusions,
    get_geocode_address,
    translate_to_english,
    convert_to_address,
    is_english
)

app = Flask(__name__)
CORS(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.abspath(__file__)


@app.route("/geojson", methods=["GET"])
def get_all_points():
    geoData = gpd.read_file("311_services.geojson")
    return jsonify(geoData.to_json())


@app.route("/shortest_path", methods=["GET"])
def shortest_path() -> str:
    """Returns a GeoJSON string representing the shortest path that avoids flooded areas.

    Args:
        orig (str): The coordinates of the origin as a comma separated lat/lon string. Ex. "40.7484,73.9857".
        dest (str): The coordinates of the destination as a comma separated lat/lon string.

    Returns:
        str: The GeoJSON string.
    """
    orig_str = request.args.get("orig", type=str)
    dest_str = request.args.get("dest", type=str)

    orig = tuple(map(float, orig_str.split(",")))
    dest = tuple(map(float, dest_str.split(",")))

    ds_sensor = xr.open_dataset(
        os.path.join(script_path, "../../", "data/ALL_SITES.nc"), engine="netcdf4"
    )
    results_df = query_IDA_calls()
    coords_dict = return_sensor_coords(ds_sensor)
    # Pass the exlusions to shortest_path() as an argument
    exclusions = return_exclusions(results_df.iloc[:10], ds_sensor, coords_dict)

    edges_gdf = get_shortest_safe_route(orig, dest, exclusions)
    edges_geojson = edges_gdf.to_json()
    return edges_geojson




@app.route("/geocode_address", methods=["GET"])
def geocode_address() -> str:
    """Geocodes and address to lat, lon  coordinates

    Args:
        address (str): The address as a string. Ex: "20 W 34th St., New York, NY 10001"

    Returns:
        str: lat, lon as a comma separated string: ex: "40.7484,-73.9857, 2024/09/15 13:26:07"
    """
    address_phrase = request.args.get("address", type=str)

    def try_translate(address):
        # If it is in English, just return it. 
        try:
            if is_english(address):
                return "english", address

            return translate_to_english(address)
        except Exception:
            return "english", address

    address_english = try_translate(address_phrase)
    english_to_address = convert_to_address(address_english[1])

    # Output from english_to_address should be input for get_geocode_address() in line 83

    try:
        coords_origin = get_geocode_address(english_to_address[0])
        coords_dest = get_geocode_address(english_to_address[1])
        ct_string = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        return ({"Origin" : coords_origin, "Destination" : coords_dest, "Time_Str" : ct_string})
    except GeocoderServiceError as e:
        # Return the error message to the front end in the response
        return make_response(str(e), 422)


if __name__ == "__main__":
    app.run(debug=True, port=8100)
