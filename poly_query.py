from utils import get_catchments, get_flowlines, get_gages


class Poly_Query:
    '''Class that will take a geojson feature collection and query the NLDI for
     overlapping catchments and flowlines. Catchments will always be queried.
     Downstream flowlines and Gages queries are optional.
    '''

    def __init__(self, data=str, return_flowlines=bool, return_gages=bool, downstream_dist=float):
        self.data = data
        self.return_flowlines = return_flowlines
        self.return_gages = return_gages
        self.downstream_dist = downstream_dist
        self.catchmentIDs = None
        self.catchments = None
        self.flowlines = None
        self.flowlineIDs = None
        self.outlet_headnodes = None
        self.gages = None

        self.run()

    def run(self):
        '''Run the Polygon Query.'''

        # Get the catchments that are overlapped by the polygon
        self.catchments, self.catchmentIDs = get_catchments(self.data)

        # Get flowlines
        if self.return_flowlines or self.return_gages:
            self.flowlines, self.flowlineIDs, self.outlet_headnodes = get_flowlines(
                self.catchmentIDs, self.downstream_dist
            )

        # If True, get gages
        if self.return_gages:
            self.gages = get_gages(self.data, self.outlet_headnodes, self.downstream_dist)

    def serialize(self):
        '''Process the results and return a list of Json FeatureCollections.'''

        output_object = []

        output_object.append(self.catchments)

        if self.return_flowlines is True:
            output_object.append(self.flowlines)

        if self.return_gages is True:
            # Put gages in a faturecollection object
            fc = {'type': 'FeatureCollection', 'features': self.gages}
            output_object.append(fc)

        return output_object
