from .poly_query import Poly_Query


def poly_query(data, get_flowlines, downstream_dist):

    results = Poly_Query(data, get_flowlines, downstream_dist)
    results = results.serialize()
    return results