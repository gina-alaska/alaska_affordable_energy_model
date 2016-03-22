#Change Log

## [0.6.0]
### added
- input file listing files that were copied

### fixed
- negative & missing consumption values

## [0.5.5]
### changed
- when plotting a data frame colored can be consistent if the same set of columns is provided

### fixed
- mmbtu is used in electricity consumption
- heating oil prices are output correctly
- non_residential_buildings_summary.csv has correct name 
- non_residential_buildings_summary.csv has correct columns 

## [0.5.4]
### changed
- internal representation of Heating Fuel and heating oil for non-residential buildings and water/wastewater systems
- the equation for $/kWh now includes as scaler percent for the amount diesel generated kWh added in

### fixed
- summary output files now have correct units (mmbtu)
- Valdez prices have been fixed 

## [0.5.3]
### changed
- residential building component output file was reformatted. 
- natural gas numbers are only calculated if a price is provided

### added
- propane, biomass, and natural gas price prices as options in config 
- propane, and biomass prices preprocessed
- summary file have been added.

## [0.5.2]
### changed
- default colors

## [0.5.1]
### changed
- output images created with run command will be in a seperate directory with in results(__images)

## [0.5.0]
### changed
- changed file name of pce file to correct name, power-cost-equalization-pce-data.csv, as it is now correct in the data repo

## [0.4.2]
### fixed
- fixed memory bug in plotting	

## [0.4.1]
### added
- clear function for figures to plot.py

### Changed
- default start year is 2017 in config .yaml files
- Improved speed when plotting in forecast and generation forecast

## [0.4.0]
### Changed
- community buildings is now non-residential buildings for input/output purposes
- intertie parent groups only get electric output
- intertie child communities only get heating output
- cli refresh command will tag directory with model and data versions
- cli commands don't add 'run_' to directories anymore

### Added
- general plotting functionality (plot.py, colors.py)
- automatic plotting for forecast and generation forecast
- added frame work for components to have additional output files
- added non-residential building summary file to outputs 

### Fixed
- typo in water/wastewater system map
- project lifetimes are correct, while maintaining longer forecast period 
- reading in diesel fuel prices corrected to match data file format

## [0.3.2]
### Fixed
- bug in preprocessor where float needed to be an int

## [0.3.2]
### added
- powerhouse consumption is assumbed to be 3% of gross genneration when not provided
- ground work for copper valley intertie(Doesn't affect resuts yet)

## [0.3.1]
### Fixed
- CommunityBuildings unknown building types 'ie. Vacant' will default to Other when estimating.

## [0.3.0]
### Changed
- in .yaml config files (IMPORT) can now, and should, be (--see input_data)
- natural gas will now absorb extra consumption in generation forecast when available 
- community names are in diagnostic file names
- in  CommunityBuildigns module the post refit consumption formulas has been changed to use real data if available.

### Added
- header in post model run .yaml config file
- community are a column in  output .csv files
- preprocessor diagnostic file is forwarded to output directory


## [0.2.1]
### Fixed
- various bugs in the devlopment flag [--dev(-d)] in the cli

## [0.2.0]
### Changed
- '-' to '_' in file names

### Added
- delompment flag for run, setup & refresh
- ability to log run out put to file
- more diagnostic messages in the preprocessor

### Fixed
- bug in setup where intertied directories were failing if they existed
- typo in metadata file name
- added the rest of the underscores to paths and names


## [0.1.2]
### Changed
- setup & refresh work form master community list
- run clears old results first
- fatal errors are logged instead of causing the model to crash
- P & M are used as tags in population file again

### Added
- added '_' for spaces in all output names
- more version info to meta data
- ability for forecast to ignore years with missing data when calculation m & b


## [0.1.1]
### Changed
- residential buildings now calculates the average kWh/Household number for communities with kWh/Household > 6000 in the base year
