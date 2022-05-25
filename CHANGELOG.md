# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/USGS-WiM/nldi_polygon_query/)

### Added 

- Added an additional parameter to the POST operation. This takes the form of a tuple, with the first value being a boolean to return flowlines and the second being a float to return the flowlines downstream to the float value distance.

### Changed  

- Updated README and requirements
- Changed small things in main.py and utils.py to make FastAPI work

### Removed 

- Removed nldi-flowtools.py left over from fork
