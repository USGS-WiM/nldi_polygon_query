import requests
from shapely.geometry import Point, Polygon, shape, MultiPolygon
import sys
import xmltodict
# import warnings
# warnings.simplefilter(action='ignore', category=FutureWarning)


# API urls
NLDI_URL = 'https://labs.waterdata.usgs.gov/api/nldi/linked-data/comid/'
NLDI_GEOSERVER_URL = 'https://labs.waterdata.usgs.gov/geoserver/wmadata/ows'
SS_NAV_SERVICE_URL = 'https://streamstats.usgs.gov/navigationservices/navigation/networktrace/route'
GAGE_STATS_URL = 'https://streamstats.usgs.gov/gagestatsservices/stations/Bounds?'


# functions
def find_out_flowline(tonode_dict: dict, fromnode_list: list) -> tuple:
    '''
    Finds all the flowlines that are outlets from the poly_query

    Inputs:
        tonode_dict: dict of  Comids and their downstream Comids
        fromnode_list: list of all the fromnode Comids

    Returns:
        outlet_ids: tuple of the Comids of outlet flowlines

    '''

    outlets: list = []
    for key in tonode_dict:
        if not int(tonode_dict[key]) in fromnode_list:
            outlets.append(int(key))

    outlet_ids: tuple = tuple(outlets)
    return outlet_ids


def get_catchments(data: dict) -> tuple:
    """
    Perform polygon intersect query to NLDI geoserver to get local catchments.

    The get_catchments function queries the NLDI for all NHD catchments within
    the bounding box of the fire polygon. Then the function returns any 
    catchments that overlap with the fire polygon. The cacthment Comids are
    also returned.

    Input:
        data: A geojson FeatureCollection of the area of interest

    Returns:
        catchmentIdentifiers: list of catchment COMIDs
        catchment: Geojson FeatureCollection of NHD catchments
    """

    # Pull the coordinates from the fire polygon geojson object
    coords = []
    for d in data['features']:
        s = shape(d['geometry'])
        if type(s) is Polygon:
            coords.append(s)

        elif type(s) is MultiPolygon:
            for g in s.geoms:
                coords.append(g)
    # Convert to a shapely polygon
    fire_poly = MultiPolygon(coords)

    # Get the bbox
    xmin, ymin, xmax, ymax = fire_poly.bounds

    # Create a polygon from the bbox of the fire polygon
    poly = Polygon([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)])

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

    # Request catchment geometry from polygon query from NLDI geoserver
    r = requests.get(NLDI_GEOSERVER_URL, params=payload)

    try:
        # Try to  convert response to json
        all_catchments = r.json()

    # If request fails or can't be converted to json, something's up
    except Exception:
        if r.status_code == 200:
            print('Get local catchments request failed. Check to make sure \
            query was submitted with lon, lat coords. Quiting nldi polygon \
            query.')

        else:
            print('Quiting nldi polygon query. Error requesting catchment \
                from Geoserver:', r.exceptions.HTTPError)

        # Kill program if request fails.
        sys.exit(1)

    # Loop thru the catchments returned and select the ones
    # which overlap with the fire polygon
    catchments_list = []
    for g in all_catchments['features']:
        for h, i in enumerate(fire_poly.geoms):
            if shape(g['geometry']).intersects(i):
                catchments_list.append(g)

    # Loop thru the remain catchments and grab the Comids
    catchmentIdentifiers = []
    for c in catchments_list:
        catchmentIdentifiers.append(
            int(c['properties']['featureid'])
        )

    # Put the catchments back in a FeatureCollection object
    catchments = {'type': 'FeatureCollection', 'features': catchments_list}

    # clean up
    del catchments_list, all_catchments, fire_poly, poly, coords, r

    return catchments, catchmentIdentifiers


def get_flowlines(catchmentIdentifiers: list, dist: float) -> tuple:
    """Request NHD Flowlines from NLDI with Catchment ID.

    Get all the NHD Flowlines from the input list of COMIDs,
    and retrieve all the flowlines downstream to the specified distance.

    Inputs:
        catchmentIdentifiers: list of integers COMIDs
        dist: float

    Returns:
        flowlines: Geojson FeatureCollection
        flowlineIDs: List of integer COMIDs
        outlet_headnodes: List of coordinate pairs
    """

    nhdGeom: list = []
    fromnode_list: list = []
    tonode_dict: dict = {}
    flowlineIDs: list = []

    # Request flowlines 100 or less at a time
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
        # Request flowlines geometry from catchment ID from NLDI geoserver
        r = requests.get(NLDI_GEOSERVER_URL, params=payload)

        try:
            # Try to convert response to json
            result: dict = r.json()

            nhdGeom += result['features']

        # If request fails or can't be converted to json, something's up
        except Exception:
            if r.status_code == 200:
                print('Get local flowlines request failed with status code \
                    200. Quiting nldi polygon query.')

            else:
                print('Quiting nldi polygon query. Error requesting \
                    flowlines from Geoserver:', r.exceptions.HTTPError)

            # Kill program if request fails.
            sys.exit(1)

        for feature in result['features']:
            # Get from and to nodes
            fromnode_list.append(feature['properties']['fromnode'])
            tonode_dict[feature['properties']['comid']] = feature['properties']['tonode']
            # Get comids
            flowlineIDs.append(feature['properties']['comid'])

        del result

    # Get the comids of flowlines that drain the fire polygon
    outlet_ids: tuple = find_out_flowline(tonode_dict, fromnode_list)
    # Get headnode coords of outlet flowlines
    outlet_headnodes = []
    for n in nhdGeom:
        if n['properties']['comid'] in outlet_ids:
            outlet_headnodes.append(n['geometry']['coordinates'][0][0])

    if dist > 0:
        payload = {'f': 'json', 'distance': dist}

        for id in outlet_ids:
            # request downstream flowlines geometry NLDI
            r = requests.get(
                NLDI_URL + str(id) + '/navigation/DM/flowlines', params=payload
            )

            try:
                downstreamflowlines: dict = r.json()

            except Exception:
                if r.status_code == 200:
                    print('Get downstream flowlines request failed with status \
                        code 200. Quiting nldi polygon query.')

                else:
                    print('Quiting nldi polygon query. Error requesting \
                        flowlines from the NLDI:', r.exceptions.HTTPError)

                # Kill program if request fails.
                sys.exit(1)

            nhdGeom += downstreamflowlines['features']
            for feature in downstreamflowlines['features']:
                # Get comids
                flowlineIDs.append(int(feature['properties']['nhdplus_comid']))

            del downstreamflowlines

    # Filter nhdGeoms for duplicates
    m = []
    [m.append(x) for x in nhdGeom if x not in m]

    flowlines = {'type': 'FeatureCollection', 'features': m}

    # Clean up variables
    del nhdGeom, fromnode_list, tonode_dict, outlet_ids, m, r

    return flowlines, flowlineIDs, outlet_headnodes


def get_gages(data, outlet_headnodes: list, dist: float) -> dict:
    '''Query the input polygon and donwstream flowlines for stream gages.
    The polygon query for gages requests gages from NLDI.
    The flowline query pulls gages from the StreamStats Navigation Services.

    Input:
        data: A geojson FeatureCollection of the area of interest
        outlet_headnodes: list of coordinates
        dist: float of diatance values for tracing downstream

    Returns:
        unique_gages: Geojson FeatureCollection of stream gages
    '''

    # Rough list of gages
    ss_gages = []

    # Get gages from the fire polygon
    # Pull the coordinates from the fire polygon geojson object
    coords = []
    for d in data['features']:
        s = shape(d['geometry'])
        if type(s) is Polygon:
            coords.append(s)

        elif type(s) is MultiPolygon:
            for g in s.geoms:
                coords.append(g)
    # Convert to a shapely polygon
    fire_poly = MultiPolygon(coords)

    # Use the bounding box of the fire polygon for the Gage Stats request
    xmin, ymin, xmax, ymax = fire_poly.bounds
    payload = f"xmin={xmin}&ymin={ymin}&xmax={xmax}&ymax={ymax}&geojson=true&includeStats=false"

    r = requests.request("GET", GAGE_STATS_URL, params=payload)

    try:
        fire_bounds_gages = r.json()

    except Exception:
        if r.status_code == 200:
            print('Get gages request failed with status \
                code 200. Quiting nldi polygon query.')

        else:
            print('Quiting nldi polygon query. Error requesting \
                gages from SS Gage Services:', r.exceptions.HTTPError)

        # Kill program if request fails.
        sys.exit(1)

    # Loop thru returned gages and make sure they fall within the fire polygon
    for g in fire_bounds_gages['features']:
        for h, i in enumerate(fire_poly.geoms):
            if Point(g['geometry']['coordinates']).within(i):
                ss_gages.append(g)

    # Loop thru the outlet_headnodes and request gages downstream at dist
    for coords in outlet_headnodes:
        payload = [
            {
                "id": 1,
                "name": "Start point location",
                "required": True,
                "description": "Specified lat/long/crs  navigation start location",
                "valueType": "geojson point geometry",
                "value": {
                    "type": "Point",
                    "coordinates": coords,
                    "crs": {
                        "properties": {"name": "EPSG:4326"},
                        "type": "name"
                    }
                }
            },
            {
                "id": 0,
                "name": "Limit",
                "required": False,
                "description": "Limits network operations to within specified option",
                "valueType": "exclusiveOption",
                "value": {
                    "id": 3,
                    "name": "Distance (km)",
                    "description": "Limiting distance in kilometers from starting point",
                    "valueType": "numeric",
                    "value": dist
                }
            },
            {
                "id": 5,
                "name": "Direction",
                "required": True,
                "description": "Network operation direction",
                "valueType": "exclusiveOption",
                "value": "downstream"
            },
            {
                "id": 6,
                "name": "Query Source",
                "required": True,
                "description": "Specified data source to query",
                "valueType": "option",
                "value": ["nwisgage"]
            }
        ]
        # send request
        r = requests.request("POST", SS_NAV_SERVICE_URL, json=payload)
        try:
            # Convert response to json
            results = r.json()

        except Exception:
            if r.status_code == 200:
                print('Get downstream gages request failed with status \
                    code 200. Quiting nldi polygon query.')

            else:
                print('Quiting nldi polygon query. Error requesting \
                    gages from SS Navigation Service:', r.url)  # exceptions.HTTPError

            # Kill program if request fails.
            sys.exit(1)

        # Exclude first point since its the query point
        ss_gages += results['features'][1:]
        del results

    # Filter duplicates
    unique_gages = []
    [unique_gages.append(x) for x in ss_gages if x not in unique_gages]

    # Clean up
    del ss_gages, payload, fire_bounds_gages, fire_poly, coords, r

    return unique_gages


def find_active_gages(gages):

    updated_gages = []
    codes = ''
    for g in gages:
        try:
            codes = codes+',' + g['properties']['Code']
        except:
            codes = codes+',' + g['properties']['identifier'][5:]

    url = f"https://waterservices.usgs.gov/nwis/site/?format=mapper&sites={(codes)[1:]}&siteStatus=active"
    r = requests.get(url)

    r_dict = xmltodict.parse(r.text)
    active_codes = []
    if r.status_code == 200:
        if type(r_dict['mapper']['sites']['site']) is list:
            for i in r_dict['mapper']['sites']['site']:
                active_codes.append(i['@sno'])
        elif type(r_dict['mapper']['sites']['site']) is dict:
            active_codes.append(r_dict['mapper']['sites']['site']['@sno'])

    for g in gages:

        if 'Code' in g['properties']:
            if g['properties']['Code'] in active_codes:
                g['properties']['active'] = True
            else:
                g['properties']['active'] = False
        elif 'identifier' in g['properties']:
            if g['properties']['identifier'][5:] in active_codes:
                g['properties']['active'] = True
            else:
                g['properties']['active'] = False

        updated_gages.append(g)

    return updated_gages
