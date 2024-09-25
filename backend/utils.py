import re
import json
from typing import List, Tuple
import osmnx as ox
import networkx as nx
from shapely.geometry import Point
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError
from ibm_watsonx_ai.foundation_models import Model
import requests

import os
import xarray as xr
import pandas as pd
import numpy as np
from geopy.distance import geodesic

from prompts import TRANSLATE_TO_ENGLISH
from prompts import prompt_to_address
from prompts import IS_ENGLISH

def query_IDA_calls():
    
    # This function queries the 311 calls for a specific time range ('2021-09-01T22:00:00', '2021-09-02T02:00:00')
    endpoint = "https://data.cityofnewyork.us/resource/erm2-nwe9.json?&$where=created_date between '{}' and '{}' &complaint_type='Sewer'".format('2021-09-01T22:00:00', '2021-09-02T02:00:00')
    response = requests.get(endpoint)
    results = pd.DataFrame.from_dict(response.json())
    results_df = results.drop(labels = [index for index in results.columns if index not in ['closed_date', 'created_date', 'descriptor', 'latitude', 'longitude']], axis = 1)
    
    return(results_df)

def return_sensor_coords(ds_sensor): 
    
    # Return dictionary with coordinates (lat, lon) of the sensor points 
    # Ensure input argument is an Xarray Dataset with dimension 'site'; output is a dictionary 
    
    site_dict = {}
    for site_name in ds_sensor['site'].values:
        da = ds_sensor.sel(site = site_name)
        site_dict[site_name] = (np.unique(da['latitude'].values[~np.isnan(da['latitude'].values)]),
                                np.unique(da['longitude'].values[~np.isnan(da['longitude'].values)]))
    
    return(site_dict)

def return_exclusions(results_df, ds_sensor, coords_dict):

    # For inputs, results_df comes from query_IDA_calls() and coords_dict comes from return_sensor_coords()

    exclusion_points = []
    for index in np.arange(len(results_df)):
    
        # Compute distances between the 311 lat/lon and sensor lat/lon
        dist_dict = {}
        if float(results_df['latitude'].iloc[index]) == float(results_df['latitude'].iloc[index]):
            if float(results_df['longitude'].iloc[index]) == float(results_df['longitude'].iloc[index]):  
                for site_name in coords_dict.keys():
                    dist_dict[(site_name)] =  geodesic((float(results_df['latitude'].iloc[index]), float(results_df['longitude'].iloc[index])), 
                                                       (coords_dict[site_name][0][0], coords_dict[site_name][1][0])).m
            else:
                continue
                
        # Note: Even if lat/lon is not provided there can be a way to use the address if provided
        else:
            continue 
      
        # Return sensor lat/lon with shortest distance
        index_date = pd.to_datetime(' '.join(results_df['created_date'].iloc[index].split('T')))    
        sensor_index = ds_sensor.sel(time = slice(index_date - pd.Timedelta(hours = 4), index_date + pd.Timedelta(hours = 4))).sel(site = min(dist_dict, key = dist_dict.get))
        
        precip_values = sm_values = []
        for value in np.arange(len(sensor_index.coords['time'])):
        
            if sensor_index.isel(time = value)['precip_max_intensity'].values > 0.2:
                precip_values.append(sensor_index.isel(time = value)['precip_max_intensity'].values)
                if len(precip_values) == 6:
                    # Conditional currently set to 6 for 30min period
                    exclusion_points.append((float(results_df['latitude'].iloc[index]), float(results_df['longitude'].iloc[index])))
                    precip_values = []
                    break
        
            elif sensor_index.isel(time = value)['soil_moisture_05cm'].values > 0.5:
                sm_values.append(sensor_index.isel(time = value)['soil_moisture_05cm'].values)
                if len(sm_values) == 6:
                    # Conditional currently set to 6 for 30min period
                    exclusion_points.append((float(results_df['latitude'].iloc[index]), float(results_df['longitude'].iloc[index])))
                    sm_values = []
                    break
        
            else:
                precip_values = sm_values = []
                continue 
            
    return(exclusion_points)

def get_shortest_safe_route(
    orig: Tuple[float, float],
    dest: Tuple[float, float],
    flooded_coords: List[Tuple[float, float]],
    radius=300,
) -> gpd.GeoDataFrame:
    """
    Computes the shortest safe route between orig and dest that avoids
    coordinates at flooded_coords.

    Args:
        orig (Tuple[float, float]): The start of the route
        dest (Tuple[float, float]): The destination of the route
        flooded_coords (List[Tuple[float, float]]): A list of locations the route can not go through representing flooding
        radius (int, optional):  Defaults to 300.

    Returns:
        gpd.GeoDataFrame: A Geo Dataframe with the edges of the shortest safe route.
    """
    G = ox.graph_from_place("New York City, New York, USA", network_type="drive")

    orig_idx = ox.nearest_nodes(G, orig[1], orig[0])
    dest_idx = ox.nearest_nodes(G, dest[1], dest[0])

    # Create a union of all the exlusion areas.
    centers_geom = [Point(coord[::-1]) for coord in flooded_coords]
    buffers = [geom.buffer(radius / 111_111) for geom in centers_geom]
    union_buffer = gpd.GeoSeries(buffers).unary_union

    # Remove these nodes to create a safe set of nodes that we can do path planning on - G_safe
    nodes = ox.graph_to_gdfs(G, nodes=True, edges=False)
    safe_nodes = nodes[~nodes["geometry"].within(union_buffer)]
    G_safe = nx.MultiDiGraph(G.subgraph(safe_nodes.index))

    # Use the safe Graph and find the safest path.
    safe_paths = ox.routing.shortest_path(G_safe, orig_idx, dest_idx, weight="length")
    G_safe_paths = nx.MultiDiGraph(G.subgraph(safe_paths))

    edges_gdf = ox.graph_to_gdfs(G_safe_paths, nodes=False, edges=True)
    return edges_gdf


def get_geocode_address(address: str) -> Tuple[float, float] | None:
    """Given an address, return the lat and long as a Tuple

    Args:
        address (str): The address string. e.g.: "20 West 34th Street, New York, NY 10001"

    Returns:
        Tuple[float, float]: The coordinates of the address e.g.: (40.7484, -73.9857)
    """
    try:
        geolocator = Nominatim(user_agent="flood_app")
        location = geolocator.geocode(address)
        if location is None:
            raise GeocoderServiceError("Address not found")
        return (location.latitude, location.longitude)
    except Exception as e:
        raise GeocoderServiceError(f"Geocoding failed on address {address}: {str(e)}")


def translate_to_english(prompt: str) -> Tuple[str, str]:
    """Translates the users prompt into English and returns the translation and detected language

    Args:
        prompt (str): The prompt the users entered

    Returns:
        Tuple[str, str]: The translated prompt and the detected language
    """

    def get_credentials():
        return {
            "url": "https://us-south.ml.cloud.ibm.com",
            "apikey": 'GcIVluc4n_68GXXy3AgZAeyKXyjGoIqOOLyvrJmxwRAu',
        }

    model_id = "ibm/granite-20b-multilingual"

    parameters = {
        "decoding_method": "greedy",
        "max_new_tokens": 4096,
        "repetition_penalty": 1,
    }

    project_id = '52007346-29cf-40eb-9b7b-96a604bc7285'

    model = Model(
        model_id=model_id,
        params=parameters,
        credentials=get_credentials(),
        project_id=project_id,
    )

    prompt = TRANSLATE_TO_ENGLISH.format(prompt=prompt)
    generated_response = model.generate_text(prompt=prompt)
    print("-----------prompt and response------")
    # print(prompt)
    print(generated_response)
    data = json.loads(generated_response)

    return data["language"], data["translation"]


def convert_to_address(prompt: str):

    # Converts translated text into origin and destination addresses. The input is the output from translate_to_english
    # Output is tuple in format origin address, destination address
    
    def get_credentials():
        return {"url" : "https://us-south.ml.cloud.ibm.com", 
                "apikey" : 'GcIVluc4n_68GXXy3AgZAeyKXyjGoIqOOLyvrJmxwRAu'}

    model_id = "ibm/granite-13b-instruct-v2"
    parameters = {"decoding_method": "greedy", "max_new_tokens": 8191, "repetition_penalty": 1}
    project_id = '52007346-29cf-40eb-9b7b-96a604bc7285'
    model = Model(model_id = model_id, params = parameters,
                  credentials = get_credentials(), project_id = project_id)
    
    prompt_in = prompt_to_address.format(text_in = prompt)
    generated_response = model.generate_text(prompt = prompt_in)
    data = json.loads(generated_response[:-2])

    return data['Origin Address'], data['Destination Address']

def is_english(prompt: str) -> bool:    
    def get_credentials():
        return {"url": "https://us-south.ml.cloud.ibm.com",
                "apikey": 'GcIVluc4n_68GXXy3AgZAeyKXyjGoIqOOLyvrJmxwRAu'}

    model_id = "ibm/granite-20b-multilingual"

    parameters = {"decoding_method": "greedy", "max_new_tokens": 10, "repetition_penalty": 1.0, 'temperature': 0.0}
    project_id = '52007346-29cf-40eb-9b7b-96a604bc7285'

    model = Model(
        model_id=model_id,
        params=parameters,
        credentials=get_credentials(),
        project_id=project_id)

    prompt = IS_ENGLISH.format(text_in = prompt)
    generated_response = model.generate_text(prompt=prompt)
    
    json_string = re.search(r'\{.*\}', generated_response).group(0)
    try:
        json_dict = json.loads(json_string)
        return json_dict['english']
    except Exception:
        return True


if __name__ == "__main__":
    ex_orig = (40.70925, -73.99657)  # Random Location in lower Manhattan near coast
    ex_dest = (40.82668, -73.94509)  # Random spot in upper Manhattan

    ex_flooded_coords = [
        (40.748817, -73.985428),  # Empire State Building
        (40.751621, -73.975502),  # Chrysler Building
        (40.779437, -73.963244),  # The Metropolitan Museum of Art
    ]

    edges_gdf = get_shortest_safe_route(ex_orig, ex_dest, ex_flooded_coords)
    edges_json = edges_gdf.to_json()
