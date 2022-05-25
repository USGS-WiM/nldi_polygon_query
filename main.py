from fastapi import FastAPI, HTTPException, UploadFile, Form
from fastapi.responses import RedirectResponse
from poly_query import Poly_Query

from fastapi import FastAPI

app = FastAPI(
    title='Polygon Querying of NLDI for catchments and flowlines',
    docs_url='/docs'
)


# Redirect root and /settings.SERVICE_NAME to the docs
@app.get("/", include_in_schema=False)
def docs_redirect_root():
    return RedirectResponse(url=app.docs_url)


# Use post operation to upload geojson file with polygons to query.
# Includes two additional params to use in the query.
@app.post("/nldi_poly_query/")
async def query_poly(file: UploadFile,
                     get_flowlines: str = Form(...),
                     downstream_dist: str = Form(...)
    ):

    # Convert params from strings to bool and float
    if get_flowlines == 'True' or get_flowlines == 'TRUE':
        get_flowlines = True
    elif get_flowlines == 'False' or get_flowlines == 'FALSE':
        get_flowlines = False
    downstream_dist = float(downstream_dist)

    try:
        contents = await file.read()
        results = Poly_Query(contents, get_flowlines, downstream_dist)
        results = results.serialize()

        await file.close()
    
        return results

        
    except Exception as e:
        raise HTTPException(status_code = 500, detail =  str(e))
  