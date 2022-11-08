from .utils import geom_to_geojson, parse_input
from .utils import get_catchments, get_flowlines, get_gages
from geojson import Feature, FeatureCollection
from shapely.geometry import MultiPolygon


class Poly_Query:
    '''Class that will take a geojson feature collection and query the NLDI for
     overlapping catchments and flowlines. Catchments will always be queried.
     Downstream flowlines and Gages can also be returned. 
    '''

    def __init__(self, data=str, get_flowlines=bool, get_gages=bool, downstream_dist=float):
        self.data = data
        self.get_flowlines = get_flowlines
        self.get_gages = get_gages
        self.downstream_dist = downstream_dist
        self.catchmentIDs = None
        self.catchments = None
        self.flowlinesGeom = None
        self.flowlineIDs = None
        self.outlet_headnodes = None
        self.gages = None

        self.run()

    def run(self):
        '''Run the Polygon Query.'''
        # coords: list = parse_input(self.data)

        # Get the catchments that are overlapped by the polygon
        # If there is only one polygon to query
        # if len(coords) == 1:
        self.catchments, self.catchmentIDs = get_catchments(self.data)

        # If there is more than one polygon to query
        # if len(coords) > 1:
        #     self.catchmentIDs = []
        #     self.catchmentGeom = []
        #     for x in coords:
        #         if type(x[0][0][0]) is list:
        #             for y in x:
        #                 result = get_catchments(y[0])
        #                 self.catchmentIDs.extend(result[0])
        #                 self.catchmentGeom.extend(result[1].geoms)
        #                 del result
        #         else:
        #             result = get_catchments(x[0])
        #             self.catchmentIDs.extend(result[0])
        #             self.catchmentGeom.extend(result[1].geoms)
        #             del result

        #     x = 0

        #     # Create a multipolygon geometry of all the catchments
        #     polygons: list = []
        #     while x < len(self.catchmentGeom):
        #         polygons.append(self.catchmentGeom[x])
        #         x += 1
        #     self.catchmentGeom = MultiPolygon(polygons)

        # Get flowlines
        if self.get_flowlines:
            self.flowlinesGeom, self.flowlineIDs, self.outlet_headnodes = get_flowlines(
                self.catchmentIDs, self.downstream_dist
            )

        # If True, get gages
        if self.get_gages:
            self.gages = get_gages(self.data, self.outlet_headnodes, self.downstream_dist)

    def serialize(self):
        '''Process the results and return a Json Feature Collection.'''
        catchments: dict = geom_to_geojson(self.catchmentGeom)
        feature1 = Feature(
            geometry=catchments,
            id='catchment',
            properties={'catchmentIDs': self.catchmentIDs}
        )

        if self.get_flowlines is True and self.get_gages is False:
            flowlines = geom_to_geojson(self.flowlinesGeom)
            feature2 = Feature(
                geometry=flowlines,
                id='flowlinesGeom',
                properties={'flowlineIDs': self.flowlineIDs})
            featurecollection = FeatureCollection([feature1, feature2])

        if self.get_flowlines is False and self.get_gages is False:
            featurecollection = FeatureCollection([feature1])

        if self.get_flowlines is True and self.get_gages is True:
            flowlines = geom_to_geojson(self.flowlinesGeom)
            feature2 = Feature(
                geometry=flowlines,
                id='flowlinesGeom',
                properties={'flowlineIDs': self.flowlineIDs})

            gages = geom_to_geojson(self.gages)
            feature3 = Feature(
                geometry=gages,
                id='gagesGeom',
                properties={'gageIDs': 'Ids'}) # self.gageIDs
            featurecollection = FeatureCollection([feature1, feature2, feature3])

        return featurecollection
