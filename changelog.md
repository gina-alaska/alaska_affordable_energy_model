#Change Log

## [0.20.6]
### changed
- updated summary layout

## [0.20.5]
### changed
- preprocessor: pce electric fuel cost calculation changed, added intertie correction

## [0.20.4]
### changed
- preprocessor: pce electric fuel cost calculation changed
- residential eff: 20yr default lifetime

## [0.20.3]
### added
- internal rate of return to components, included a column in component summaries
- diesel price adder, as a possible 'scaler'

### changed
- source for wind capacity in preprocessor, it's consitently wind_existing_systems.csv now

## [0.20.2]
### fixed
- pce preprocessing, replaces missing values with zeros
- community_data: corrects name of intertie file.

## [0.20.1]
### added
- name key to wind projects
- cli summaries command to generate web summaries
- code for generating web summaries, aaem/web.py, aaem/web_lib.py, and new function on components outputs.py

### changed
- value added as hydro projcet name now includes stream

### fixed
- typo in get_benefit function name


## [0.20.0]
### added
- Hydropower: diagnostic messages in preprocess projects function 
- Hydropower: default for missing project phase

### changed
- all configs are now sorted and commented saved
- component names updated
- residential efficiency: changed data keys
- moved some common values in component configs to community section of config
- intertie projects for electricity are now sorted to into the intertie 
- electric projects are only run for interties/ not intetied communities
- heating projects not run on interties
- wind power: start date is calculated from phase

### fixed
- issues preventing Chenega Bay, and Paxson from running
- issue where transmission was not getting data from other community
- transmission summary is generated now


## [0.19.2]
### fixed
- capital costs scaler is applied to all components

### changed
- moves averge load calculation from componets to forecast

## [0.19.1]
### fixed
- bug with run error message outputs

## [0.19.0]
### added
- ability to run a group of communities/ modified communities from cli
- add scalers for, Diesel Price, diesel price, and Capital Costs
- ability to pass scalers to run command in cli
- cli will not overwrite existing files unless -f (force flag) is provided
- functionality to easily save a community data config file

### changed
- restructured input file and config directories, 
- a community and its project will have different config files, but the same input files
- completely rewrote driver internal functionality
- updated all cli command messages
- changed cli setup command structure
- moved regional multipliers out of community data, into their own file

### removed
- old component files
- unused imports


## [0.18.1]
### changes
- updates the sphinx docs config

## [0.18.0]
### adds 
- regional option to cli run command

### changes
- cli setup command redone
- restructures all compopnentes

## [0.17.13]
### fixes
- diesel efficiency summary headings
- biomass pellet LCOE/breakeven price input includes fuel cost

### adds
- documentation for diesel efficiency

### changes
- structure of diesel efficiency component

## [0.17.12]
### adds
- diesel efficiency component

## [0.17.11]
### changes 
- for components break even cost in gal heating oil equiv.
- renames efficiency components function names to be more consistent with newer components
- moves res/non-res summary functions to respective component files

### fixes
- non-residential proposed value calculations
- missing years in consumption input data issue in forecast and some summaries
- range of yeas to use when calculating LCOE/break even price
- ashp Excess Generation Capacity needed calculation


## [0.17.10]
### changes
- headers: Gallons Diesel -> Gallons Heating Fuel where Nessary
- ASHP: changes inputs to LCOE and breakeven prices
- transmission: changes inputs to LCOE and breakeven prices
- non-res: adds % heating cost scaler to breakeven cost calculation

### adds
- kwh consumption summary: added region column
- ASHP (both): added excess kW column

### fixes
- biomass cordwood: fuel costs no longer doubled



## [0.17.9]
### changes
- non residential buildings component: kWh estimattion scale fractor is changed for interties to include the whole intertie

## [0.17.8]
### fixes
- heat recovery projects are now run
- heat recovery est. potential is calculated correctly

## [0.17.7]
### changes
- non-res efficiency levelized cost of energy caclulation
- biomass cordwood levelized cost of energy caclulation

## [0.17.6]
### changes 
- non residential buildings component: changes to calculation of pre retrofit diesel price

### adds
- consumption summary

## [0.17.5]
## fixes
- corrected lower case 'other' to 'Other' key in non-res building component

## [0.17.4]
### added
- heat recovery component
- documentation setup files

### updated
- ashp reasons for not running 

## [0.17.3]
### changes
- updates the Levelized and Breakeven cost caclutation to include the NPV of the fuel used

### fixes
- method for caclulating intertie prices
- waste water summary 
- res/non-res fuel_amouts for calculating Levelized and Breakeven cost 

## [0.17.2]
### changes
- electricity prices are made to be consistent on interties

## [0.17.1]
### changes
- ashp: caclulation of LOCE and break even cost include electricity used saved

## [0.17.0]
### changed
- forecast: can extend further into the future using the last year as a flat value where actual forecasted values are unavailable
- hydropower: lifetime set to 50 years
- diesel prices: method for preprocessing and reading  
- ashp both: added 2x multiplier to estimate cost of system needed
- ashp res: added minimum 18,000 Btu/hr for size of unit installed
- ashp res: added Capacity modifier to


## [0.16.13]
### added
- added water/wastewater summary

## [0.16.12]
### added
- levelized cost of energy, and break even costs added to components 

### updated
- biomass includes maintanance cost in savings

## [0.16.11]
### updated
- transmission calculations for proposed intertie system, and heat recovery lost
- transmission summary

## [0.16.10]
### updated
- transmission component transmission loss per mile

### added
- documentation for interties.py (transmission comp)

## [0.16.9]
### updated
- interties cost savings 

## [0.16.8]
### added
- consumption col to village log

### fixes
- population col in village log

## [0.16.7]
### added
- Transmission component

## [0.16.6]
### changes
- hydro project tags are based on index, project names are saved as information in input data

### fixes
- generating summaries for running model with only interties no longer crashs

## [0.16.5]
### fixes
- preprocessor coping for intertie projects
- added hr used flag check for calculating heating fuel lost


## [0.16.4]
### changed
- intertied community prices (diesel & electric) are the same 
- hydro proposed generation is capped for actual diesel generation
- fixed diesel prices when community is tagged with a project

## [0.16.3]
### fixed
- Hydro summary headers

### changed
- population added to village sector summary
- hydro Net generation maxed at actual consumption of start year

## [0.16.2]
### added
- hydropower component

### updated
- all other components are updated to ignore projects not from their components
- summaries and outputs updated to disregard non related projects

## [0.16.1]
### added
- file for each community summarizing the npv values per component

### upadate
- updated headings for component outputs
- added intertie column for ASHP summaries
- added diesel prices to Solar and Wind Summaries
- updated the component template

## [0.16.0]
### added
- intergration of existing projects for wind
- support to driver for exiting projects

### changed
- current year to 2015

## [0.15.5]
## fixed
- data in peak monthly btu/hr column of ashp residential summary

## added
- intertie column to ashp summaries

## [0.15.4]
### fixed
- biomass pellet price key
- ASHP formulas fixed

### added
- monthly ashp table files added to community component output folders


## [0.15.3]
### fixed
- headers in summaries
- conversion factors in summaries

## [0.15.2]
### fixed
- bug in summaries related to rounding 

## [0.15.1]
### changed
- summary file headers for all componentes have been updated

## [0.15.0]
### changed
- biomass price keys have been renamed, and expanded for pellet prices
- added test for running for biomass wood based on resource availability

## [0.14.9]
### added 
- ASHP (air source heat pump) base component
- Non-residential ASHP component
- Residential ASHP component

### fixes
- bug in cli copy where metadata.txt was not copied
- bug in cli compare caused by .pkl file
- bug in fuel oil summary, where non-res heating fuel total was shown as opposed to non-res heating oil.

## [0.14.8]
### added 
- electric price summary

## [0.14.7]
### changed
- speed up cli run command

### added
- output of results in a binary fromat (python pickle)

## [0.14.6]
### changed
- plots not generated by default with cli

### added
- order for componentes to run it to insure that values needed in biomass components are calculated ahead of time
- plot(-p) option added to cli, to generate plots

### updated
- wing power, proposed generation takes existing solar generation into account
- wind power, added test to check for proposed capacity > 0 before doing calculations
- wind power, added more reasons for not runing
- solar power, proposed generation takes existing wind generation into account
- biomass pellet, added road_system test

### fixed 
- copy errors between biomass base and biomass pellet and biomass cordwood 
- Klukwan preprocessing for generation data, now includes Chilkat Valley
- missing prices fix; if a given fuel price is N/A, default to 0 

## [0.14.5]
### added 
- biomass base
- biomass cordwood
- biomass pellet

## [0.14.4]
### changed 
- updated solar and wind component outputs
- changed solar default values (.3 -> .15, no powerhouse cost)

### fixed
- generation calculation with missing lineloss fixed

## [0.14.3]
### changed 
- solar and wind output headers
- subtracts existing solar load from propoesed when calculating proposed

## [0.14.2]
### added
- notes column to solar and wind summaries
- existing solar data to solar summary

### changed
- disel generato efficiency is now validated in community data
- caclulation of propsed offset for wind where hydro is present
- default starting date for RE projects is 2020

### fixed
- PCE generator efficiency is now calculated from only the diesel generation 

## [0.14.1]
### fixed
- setup function for natural gas
- plotting of intertie electricity forecasts
- wind power summary not being generated is fixed

### changed
- solar power output format
- number of years used in caclulating gennerator efficiency (was 1: now 3)
- solar capacity is detrimied as percent of diesel generation

### added
- solar power minumum run conditions


## [0.14.0]
### added
- solar power component

### changed
- handling of diesel data

## [0.13.4]
### removed
- wind class and potential minimum requirments

### changed
- wind log file columns
- wind defalut yaml options

### added
- wind interties for wind class

## [0.13.3]
### fixed
- list of data files to copy in cli_lib

## [0.13.2]
### changed
- preprocessing of population data index
- forecast csv files have I qualifer added

## [0.13.1]
### changed
- wind summary file
- tuned the wind component

## [0.13.0]
### added
- wind component

### changed
- some component_template.py modifcations 

## [0.12.2]
### changed
- all of a components code is in the comoponts .py file

## [0.12.1]
### fixed
- community buildings values are now saved properly

## [0.12.0]
### changed
- residential buildings component updated for new data format
- community buildigns component updated for new data format
- moved # houshold calculation to res component
- wind generation capacity caclulation


## [0.11.0]
### added
- other fuel types to non-residential buildings component
- template for other components

### changed
- cli compare command

## [0.10.2]
### added
- biomass heating fuel to waterwaste/water components 
- none added to waterwaste/water system type map in preprocessor. Acts like unknown system type.

### fixed
- correctet consumption summing of measured values 

## [0.10.1]
### added
- aaem/cli/cli_lib.py for cli functionality commomn to multiple commands
- added modeled water and non-res columns to forecast comparsion summary

### fixed
- missing unknown columns in non-residential building summary
- in correct display of unknown buildings in missing non-residential building summary

### changed
- the way addition building  in non-res component are calculated. No more -2

## [0.10.0]
### changed
- preprocessor updated to take new keys for generation limits

### fixed
- missing generation_forecast.csv files
- issue where not all intertie subcommunites were being used
- issue in creating forecast compareison file
- issue in preprocessor indexing cauing some communites to get the wrong data input files

## [0.9.3]
### fixed
- fixes missing renwable generation sources were data was avaialble
- fixes negitive generation created by scaling the generaton back
- fixes outputs for generatin forecast where data is not avaiable. They don't get saved.

## [0.9.2]
### changed
- added columns to non-residential_builing_summary.csv for each building types electric(mmbtu) and heaitng(mmbtu) consumtion

### added
- summary comparing the forecasted (trend line vs. modeled) electrictiy consumption numbers forecast_component_consumption_comparison_summary.csv


## [0.9.1]
### changed
- on generation forecast plots the total is not plotted if only one fuel source is present

## [0.9.0]
### added
- generation capacity (generation limits) for wind and hydro

### fixed
- fixed interties in the fuel oil log
- the generation rollback function is called


## [0.8.5]
### fixed
- fixed consumption column names for elcetricity forecast

## [0.8.4]
### changed
- consumption forecasting method
- electricity plots updated for new forecasting method

## [0.8.3]
### added
- dashed line at y = 0 for consumption to help show when values go below 0

### changed
- plot colors, population alawys has the same color

### fixed
- residential component output csv uses the right prices for a community and not the temp prices uesd before
- sqft values in the  non-res output files dont inclued the Water & Sewer systems 

## [0.8.2]
### added
- ability to enable or disable the electricity/heating fuel comonents of the model
- auto disable of electricity component if yearly_electricity_summary.csv is missing
- limits on linelosses
- ability to change the limits on linelosses in config files
- generation will scale back on renewable sources if predicted generation drops

### fixed 
- heating oil summary has been fixed for intertied communities

## [0.8.1]
### added
- fuel oil log
- auto fill in of LNG prices for Barrow and Nuiqsut

### changed
- generation forecast is now part of the forecast component

### fixed
- negative EIA diesel generation values are set to zero, while still accounting for the fuel used in said generation 
- other fuel types in the PCE data are picked up by the preprocessor. 

## [0.8.0]
### fixed 
- residential heating fuel for interties
- fixes generation forecast where natural gas was shown as present when it was in fact not
- fixes some preprocessor issues for the interties where some columns were not summed for the yearly electric summary
- gross generation vs net generation has been fixed in the PCE data where the power house consumption is not available
- measured generation is now used in the output files (before it was being over written with calculated values) 

### changed
- moved calculation of residential average kWh/household to the preprocessor

## [0.7.4]
### added
- timing feature for all commands. use: aaem -t <command> ...  to time any command

### changed 
- colors on generation forecast plot

### fixed
- bug where prices for kWh and heating fuel were the same in the village log

## [0.7.3]
### added
- time(-t) option to run command to time it

### fixed
- indexing in the preprocessor for items with one row

## [0.7.2]
### changed
- added % of total columns to building s summary

## [0.7.1]
### changed
- Order of communites has been alphabetized

### fixed
- Square footage not being included for single building categories

## [0.7.0]
### changed
- GNIS ID is used to index building inventory in preprocessor
- Water and Wastewater systems components now runs with unknown system types

## [0.6.4]
### fixed
- the missing intertie kWh prices have been fixed

## [0.6.3]
### fixed
- the non-residential buildings summary file columns have been corrected

## [0.6.2]
### added
- summary of non-residential buildings file
- total heating fuel added to residential summary file

### fixed
- in residential component houses to retrofit has minimum of 0
- 'North Slope' $/kWh prices are set to a default value ($0.15) 


## [0.6.1]
### changed
- some w&ww function names have been changed for clarity

### fixed
- negative residential consumption values
- preprocessor overwriting copies.csv for intertie sub communities. 
- wastewater kWh costs are calculated correctly
- cost of a project per year is now calculated over proper period

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
