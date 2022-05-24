import json
import requests
import shapely.geometry
from shapely.geometry import mapping, MultiLineString, Polygon, MultiPolygon
import sys
import numpy as np

# arguments
NLDI_URL = 'https://labs.waterdata.usgs.gov/api/nldi/linked-data/comid/'
NLDI_GEOSERVER_URL = 'https://labs.waterdata.usgs.gov/geoserver/wmadata/ows'


# functions
def geom_to_geojson(geom: shapely.geometry) -> dict:
    """Return a geojson from an OGR geom object"""

    geojson_dict: dict = mapping(geom)

    return geojson_dict


def parse_input(data: json) -> list:
    # Extract the individual polygons from the input geojson file
    coords: list = []   # This will be a list of polygons
    for d in data['features']:
        if d['geometry']['type'] == 'Polygon':              # If it is a polygon
            if len(d['geometry']['coordinates']) == 1:      # Confirm that it is a polygon
                rounded_coords = list(np.round_(np.array(d['geometry']['coordinates']),decimals=4))
                coords.append(rounded_coords) # And add it to the list of polygons
            if len(d['geometry']['coordinates']) > 1:       # If the polygon is actually a multipolygon
                for c in d['geometry']['coordinates']:      # Loop thru it
                    rounded_coords = np.round_(np.array(c),decimals=4)
                    coords.append([rounded_coords])           # And add each polygon (as a list) tp the list
        if d['geometry']['type'] == 'MultiPolygon':         # If it is a multipolygon
            for e in d['geometry']['coordinates']:          # Loop thru it 
                rounded_coords = list(np.round_(np.array(e),decimals=4))
                coords.append(rounded_coords)               # And add it to the list of polygons

    return coords


def get_local_catchments(coords: list) -> tuple:
    """Perform polygon intersect query to NLDI geoserver to get local catchments"""
    
    ## If there are more than 237 points, the catchment query will not work
    # Convert coords to shapely geom
    if len(coords) > 237:
        poly: shapely.Polygon = Polygon(coords)
        i = 0.000001
        while len(poly.exterior.coords) > 235:
            poly = poly.simplify(i, preserve_topology=True)
            i += 0.000001
        # while len(coords) > 235:
        #     coords.pop(random.randrange(len(coords)))
        # poly = Polygon(coords)

    else:
        poly: shapely.Polygon = Polygon(coords)
    
    cql_filter = f"INTERSECTS(the_geom, {poly.wkt})"   

    payload = {
        'service': 'wfs',
        'version': '1.0.0',
        'request': 'GetFeature',
        'typeName': 'wmadata:catchmentsp',
        'outputFormat': 'application/json',
        'srsName': 'EPSG:4326',
        'CQL_FILTER': cql_filter
    }

    # Try to request catchment geometry from polygon query from NLDI geoserver
    try:
        r = requests.get(NLDI_GEOSERVER_URL, params=payload)
        # Convert response to json
        resp = r.json()
        
    # If request fails or can't be converted to json, something's up
    except:
        if r.status_code == 200:
            print('Get local catchments request failed. Check to make sure query was submitted with lon, lat coords. Quiting nldi_flowtools query.')

        else:
            print('Quiting nldi_flowtools query. Error requesting catchment from Geoserver:', r.exceptions.HTTPError)

        # Kill program if request fails.
        sys.exit(1)

    features = resp['features']

    x = 0
    catchmentIdentifiers: list = []
    catchmentGeoms: list = []
    while x < len(features):    # Loop thru each catchment returned        
        catchmentIdentifiers.append(json.dumps(features[x]['properties']['featureid']))     # Add catchment IDs to list
        if len(features[x]["geometry"]['coordinates']) > 1:    # If the catchment is multipoly (I know this is SUPER annoying)
            r = 0
            while r < len(features[x]["geometry"]['coordinates']):
                catchmentGeoms.append(Polygon(features[x]["geometry"]['coordinates'][r][0]))
                r += 1
        else:       # Else, the catchment is a single polygon (as it should be)
            catchmentGeoms.append(Polygon(features[x]["geometry"]['coordinates'][0][0]))
        x += 1
    
    catchmentGeoms: shapely.MultiPolygon = MultiPolygon(catchmentGeoms)

    # Remove duplicates from list of catchment IDs
    catchmentIdentifiers: list = [x for x in catchmentIdentifiers if catchmentIdentifiers.count(x) == 1]

    
    return catchmentIdentifiers, catchmentGeoms


def get_local_flowlines(catchmentIdentifiers: list, dist: float) -> tuple:
    """Request NDH Flowlines from NLDI with Catchment ID"""

    nhdGeom: list = []
    fromnode_list: list = []
    tonode_dict: dict = {}

    # Request catchments 100 or less at a time
    for i in range(0, len(catchmentIdentifiers), 100):
        chunk = catchmentIdentifiers[i:i + 100]
                
        catchmentids = tuple(chunk)

        cql_filter = f"comid IN {catchmentids}" 
        # If there is only one feature
        if len(catchmentIdentifiers) == 1:
            cql_filter = f"comid IN ({catchmentIdentifiers})"
        
        payload = {
            'service': 'wfs',
            'version': '1.0.0',
            'request': 'GetFeature',
            'typeName': 'wmadata:nhdflowline_network',
            'maxFeatures': '5000',
            'outputFormat': 'application/json',
            'srsName': 'EPSG:4326',
            'CQL_FILTER': cql_filter
        }
        # Try to request flowlines geometry from catchment ID from NLDI geoserver
        try:
            r = requests.get(NLDI_GEOSERVER_URL, params=payload)
            # Convert response to json
            flowlines: dict = r.json()

        # If request fails or can't be converted to json, something's up
        except:
            if r.status_code == 200:
                print('Get local flowlines request failed with status code 200. Quiting nldi_flowtools query.')

            else:
                print('Quiting nldi_flowtools query. Error requesting flowlines from Geoserver:', r.exceptions.HTTPError)

            # Kill program if request fails.
            sys.exit(1)


        for feature in flowlines['features']:
            # Get from and to nodes
            fromnode_list.append(feature['properties']['fromnode'])
            tonode_dict[feature['properties']['comid']] = feature['properties']['tonode']
            # Convert the flowline to a geometry collection to be exported
            for coords in feature['geometry']['coordinates']:
                nhdGeom.append([coord[0:2] for coord in coords])

    outlets: tuple = find_out_flowline(tonode_dict, fromnode_list)

    if not dist:
        flowlinesGeom: shapely.MultiLineString = MultiLineString(nhdGeom)

    if dist:
        payload = {'f': 'json', 'distance': dist}

        flowlines: dict = {'type': 'FeatureCollection', 'features': []}
        for id in outlets:
            # request downstream flowlines geometry NLDI
            try:
                r = requests.get(NLDI_URL  + str(id) + '/navigation/DM/flowlines', params=payload)
                downstreamflowlines: dict = r.json()
                for feature in downstreamflowlines['features']:
                    nhdGeom.append(feature['geometry']['coordinates'])
            except:
                if r.status_code == 200:
                    print('Get downstream flowlines request failed with status code 200. Quiting nldi_flowtools query.')

                else:
                    print('Quiting nldi_flowtools query. Error requesting flowlines from Geoserver:', r.exceptions.HTTPError)

                # Kill program if request fails.
                sys.exit(1)


        flowlinesGeom: shapely.MultiLineString = MultiLineString(nhdGeom)

    return flowlines, downstreamflowlines, flowlinesGeom
    


def find_out_flowline(tonode_dict: dict, fromnode_list: list) -> tuple:
    # Find all the flowlines that are outlets from the poly_query
    outlets: list = []
    for key in tonode_dict:
        if not int(tonode_dict[key]) in fromnode_list:
            outlets.append(int(key))
    
    outlet_flowlines: tuple = tuple(outlets)
    return outlet_flowlines
        
