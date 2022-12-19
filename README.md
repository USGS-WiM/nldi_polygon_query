![WiM](wim.png)


# NLDI Polygon Query

This is a python package for querying the Network Linked Data Index for hydrographic data. The input data to this package is a GeoJSON FeatureCollection, and so is the output. The package will parse the input FeatureCollection, separate multipolygons and make requests to the NLDI for catchments and flowlines (depending on the input parameters) that overlap with the query polygons. A trace downstream distance can be set in order to return flowlines a set distance downstream for the query polygons. In addition, stream gages in the query polygons and along the flowlines can also be returned with this package. StreamStats GageServices are used for the gage queries.

Services for the `main` branch can be found at https://streamstats.usgs.gov/nldipolygonservices and documentation can be found at https://streamstats.usgs.gov/nldipolygonservices/docs.

### Prerequisites

Python 3
Git

## Installing
To run the services locally, run the following in your Windows command prompt:

```bash
# clone repository
git clone https://github.com/USGS-WiM/nldi_polygon_query.git
cd nldi_polygon_query
# create a virtual environment
python -m venv env
# active the virtual environment
.\env\Scripts\activate
# install the project's dependencies
pip install -r requirements.txt
# deploy at a local server
uvicorn main:app --host 127.0.0.1 --port 8000
```

Alternate instructions for the Windows [Anaconda3](https://docs.anaconda.com/anaconda/install/index.html) prompt:

```bash
# clone repository
git clone https://github.com/USGS-WiM/nldi_polygon_query.git
cd nldi_polygon_query
# create a new Conda environment
conda create --name nldi_polygon_query
# active the Conda environment
conda activate nldi_polygon_query
# install the project's dependencies
conda install pip
pip install -r requirements.txt
# deploy at a local server
uvicorn main:app --host 127.0.0.1 --port 8000
```

Add --reload to the end of the uvicorn main:app --host 127.0.0.1 --port 8000 to enable hot reload for local testing purposes only.

Once the above code has been run successfully, the service documentation will be available at http://127.0.0.1:8000/docs/.
### Getting Started

Once the API is running locally, you can make requests to it. To use the API, a geojson file containing a FeatureCollection can be submitted with a `POST` call, and the response will also be in the format of a FeatureCollection. Here is a quick example of how to do so in Python.

```bash
import requests

url = 'http://127.0.0.1:8000/nldi_poly_query'

file = {'file': open(<file path>, 'r')}

params = {'get_flowlines': True, 'downstream_dist': 55}
resp = requests.post(url=url, files=file, data=params) 
```

## Development Workflow

An issue will be assigned to you via GitHub. Your workflow begins after assignment:
1. Create a branch based on the `dev` branch with your initials and the issue number as the branch name (e.g. JD-5): `git checkout -b JD-5`
3. Work on the issue.
     1. In the "Projects" section on the sidebar of the issue page, under "StreamStats Ecoystem", change the "Status" to "In Progress".
     2. While you work, you may wish to have the app running live with live reload: `uvicorn main:app --host 127.0.0.1 --port 8000 --reload`
     3. Add your changes: `git add .`
     4. Check that your files were added as expected: `git status`
     5. Frequently commit your work to your local branch. Use simple, short, and descriptive messages with a verb describing the work. Include the issue number. Example: `git commit -m "#5 add weightEst4 endpoint"`
4. Update the [CHANGELOG.md](https://github.com/USGS-WiM/nldi_polygon_query/blob/master/CHANGELOG.md) to describe your work.
5. Ensure your code is synced with the latest version of the `dev` branch: 
     1. Use this command: `git pull origin dev`
     2. If there are no merge conflicts, the updates made to the `dev` branch will be incorporated into your local branch automatically.
     3. If there are merge conflicts, you will need to resolve conflicts manually. Please be careful with this step so that no code is lost. Once complete, you will need to add your changes: `git add .` and then commit again: `git commit -m "add message here"`
6. Push your committed and synced branch to the remote repository on GitHub: `git push origin JD-5`
7. Submit a [Pull Request](https://github.com/USGS-WiM/nldi_polygon_query/pulls):
     1. Request that your branch be merged into the `dev` branch.
     2. Name the Pull Request in this format: "Fixes #5 - Issue Description". 
     3. Use [keywords](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/using-keywords-in-issues-and-pull-requests) to automatically close issues (e.g. "Closes #5).
     4. Assign a reviewer (typically the lead developer).
8. Once your Pull Request is reviewed, address any feedback that needs to be addressed. Once you have addressed feedback, click the button to re-request review.
9. Upon approval of the Pull Request, your issue will be merged into the `dev` branch and you can start on a new issue.

## Deployment

1. [Contact SysOps](https://github.com/USGS-WiM/wim-infrastructure/issues/new) to request access to the FastAPI_Services server
2. Use [Putty](https://www.putty.org/) to SSH onto the FastAPI_Services server. In the Putty Configuration:
     - Host Name: `<you_username>@FastAPI_Services_hostname_or_IP_address`
     - Port: 22
     - Connection type: SSH
     - In the sidebar, Connection > SSH > Auth: "Private key file for authentication:" click "Browse" to upload your private key file
     - Click "Open" to connect
 3. Go to the app directory: `cd /var/www/nldi_polygon_query/`
 4. Pull the latest code: `sudo git pull origin master`
 5. Restart the daemon: `sudo systemctl restart nldi_polygon_query`
 6. Check that the services were updated: https://streamstats.usgs.gov/nldipolygonservices/docs
 7. Exit when finished: `exit`

## Built With

* [Python](https://www.python.org/) - The main programming language used
* [FastAPI](https://fastapi.tiangolo.com/) - Web framework for building APIs

## Authors

* **[Anders Hopkins](https://github.com/Anders-Hopkins)**  - *Lead Developer* - [USGS Web Informatics & Mapping](https://wim.usgs.gov/)

## License

This project is licensed under the Creative Commons CC0 1.0 Universal License - see the [LICENSE.md](LICENSE.md) file for details.

## Suggested Citation
In the spirit of open source, please cite any re-use of the source code stored in this repository. Below is the suggested citation:

`This project contains code produced by the Web Informatics and Mapping (WIM) team at the United States Geological Survey (USGS). As a work of the United States Government, this project is in the public domain within the United States. https://wim.usgs.gov`

## About WIM
* This project authored by the [USGS WIM team](https://wim.usgs.gov)
* WIM is a team of developers and technologists who build and manage tools, software, web services, and databases to support USGS science and other federal government cooperators.
* WIM is a part of the [Upper Midwest Water Science Center](https://www.usgs.gov/centers/upper-midwest-water-science-center).
