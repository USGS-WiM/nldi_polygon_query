from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from poly_query import Poly_Query


app = FastAPI(
    title='Polygon Querying of NLDI for catchments and flowlines',
    docs_url='/docs'
)

class Item(BaseModel):
    data: dict
    get_flowlines: bool
    downstream_dist: float


# Redirect root and /settings.SERVICE_NAME to the docs
@app.get("/", include_in_schema=False)
def docs_redirect_root():
    return RedirectResponse(url=app.docs_url)


# Use post operation to process geojson object with polygons to query.
# Includes two additional params to use in the query.
@app.post("/nldi_poly_query/")
async def query_poly(request: Item):


    content = request.data
    get_flowlines = request.get_flowlines
    downstream_dist = request.downstream_dist
    

    try:
        results = Poly_Query(content, get_flowlines, downstream_dist)
        results = results.serialize()
    
        return results

        
    except Exception as e:
        raise HTTPException(status_code = 500, detail =  str(e))
  