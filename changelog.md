#Change Log

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
