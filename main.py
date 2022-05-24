from fastapi import FastAPI, HTTPException, Response, File, UploadFile, Form
from fastapi.responses import RedirectResponse
from poly_query import Poly_Query

from fastapi import FastAPI

app = FastAPI()


@app.post("/upload")
async def Query_Polygons(file: UploadFile):
    get_flowlines, downstream_dist = True, 55
    try:
        contents = await file.read()
        results = Poly_Query(contents, get_flowlines, downstream_dist)
        results = results.serialize()
        
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        await file.close()
    
    return results
