from .utils import geom_to_geojson, parse_input
from .utils import get_catchments, get_flowlines, get_gages
from geojson import Feature, FeatureCollection
from shapely.geometry import MultiPolygon


class Poly_Query:
    '''Class that will take a geojson feature collection and query the NLDI for
     overlapping catchments and flowlines. Catchments will always be queried.
     Flowlines are optional. Downstream flowlines can also be returned.
    '''

    def __init__(self, data=str, get_flowlines=bool, get_gages=bool, downstream_dist=float):
        self.data = data
        self.get_flowlines = get_flowlines
        self.get_gages = get_gages
        self.downstream_dist = downstream_dist
        self.catchmentIDs = None
        self.catchmentGeom = None
        self.totalBasinGeoms = []
        self.upcatchmentGeom = None
        self.flowlinesGeom = None
        self.flowlineIDs = None
        self.outlet_headnodes = None
        self.gages = None

        self.run()

    def serialize(self):
        catchments: dict = geom_to_geojson(self.catchmentGeom)
        feature1 = Feature(
            geometry=catchments,
            id='catchment',
            properties={'catchmentIDs': self.catchmentIDs}
        )

        if self.get_flowlines is True:
            flowlines = geom_to_geojson(self.flowlinesGeom)
            feature3 = Feature(
                geometry=flowlines,
                id='flowlinesGeom',
                properties={'flowlineIDs': self.flowlineIDs})
            featurecollection = FeatureCollection([feature1, feature3])

        if self.get_flowlines is False:
            featurecollection = FeatureCollection([feature1])

        return featurecollection

    def run(self):

        coords: list = parse_input(self.data)

        # Get the catchments that are overlapped by the polygon
        # If there is only one polygon to query
        if len(coords) == 1:
            self.catchmentIDs, self.catchmentGeom = get_catchments(coords[0][0])

        # If there is more than one polygon to query
        if len(coords) > 1:
            self.catchmentIDs = []
            self.catchmentGeom = []
            for x in coords:
                if type(x[0][0][0]) is list:
                    for y in x:
                        result = get_catchments(y[0])
                        self.catchmentIDs.extend(result[0])
                        self.catchmentGeom.extend(result[1].geoms)
                        del result
                else:
                    result = get_catchments(x[0])
                    self.catchmentIDs.extend(result[0])
                    self.catchmentGeom.extend(result[1].geoms)
                    del result

            x = 0

            # Create a multipolygon geometry of all the catchments
            polygons: list = []
            while x < len(self.catchmentGeom):
                polygons.append(self.catchmentGeom[x])
                x += 1
            self.catchmentGeom = MultiPolygon(polygons)

        print('self.catchmentIDs', self.catchmentIDs)
        # Get flowlines
        if self.get_flowlines:
            self.flowlinesGeom, self.flowlineIDs, self.outlet_headnodes = get_flowlines(
                self.catchmentIDs, self.downstream_dist
            )

        # Get no flowlines
        if not self.get_flowlines:
            pass

        # If True, get gages
        if self.get_gages:
            self.gages = get_gages(self.catchmentIDs, self.outlet_headnodes, self.downstream_dist)
