# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/USGS-WiM/nldi_polygon_query/tree/dev)

## [0.2.2] - 2023-1-11
### Removed
- Removed the old version of the polygon query endpoint.


## [0.2.1] - 2022-12-16
### Added
- Added functionality to check the activate status of gages. 


## [0.2.0] - 2022-11-15
### Added 
- Added functionality to query gages inside the area of interest and on downstream flowlines

### Changed  
- The output object is now a list of GeoJson FeatureCollections: catchments, flowlines and gages

### Removed 
- Removed unneeded functions from utils.py and unneeded package imports from utils.py and poly_query.py


## [0.1.1] - 2022-06-17
### Added 
- Enforced PEP8 standards
- Added a list of flowline comids to the properties of the output flowlines object
- Made it possible to return flowlines while downstream_dist = 0

### Changed  
- Cleaned up poly_query.py and utils.py

### Removed 
- Removed redundent variables from poly_query.py and utils.py



## [0.1.0] - 2022-05-25
### Added 
- Added two params to post operation: bool value to return flowlines and float value to return distance downstream flowlines.

### Changed  
- Updated README and requirements
- Changed small things in main.py and utils.py to make FastAPI work
- Updated service URL in README

### Removed 
- Removed nldi-flowtools.py left over from fork
