"""
defaults.py

this file contains default yaml file info as strings
"""

### This is the absolute default yaml string used by the model
absolute = """community: 
  name: ABSOLUTE DEFAULT NAME # community name <string>
  region: IMPORT # name <string>
  current year: ABSOLUTE DEFAULT  #year to base npv calculations on <int>
  model financial: True 
 
 
  #AEA ASSUMPTIONS
  interest rate: .05 # rate as decimal <float> (ex. .05) 
  discount rate: .03 # rate as decimal <float> (ex. .03)
  heating fuel premium: IMPORT # price/gallon <float> (ex. 0.45)

  # fuel repairs: 500 # price/yr <float> TODO: still used??
  # fuel o&m: 1000 # # price/yr <float> TODO: still used??
  # diesel generator o&m: 84181 # price/yr <float> TODO: still used??
  diesel generation efficiency: IMPORT #10.802351555 # kWh/gal <float>

  #do these come from community profiles?
  generation: IMPORT # kWh generated/yr  <float> 123456.00
  #consumption kWh: ABSOLUTE DEFAULT # kWh consumed/year <float> 12345.00

  consumption HF: IMPORT # gallons HF consumed/year <float> 12345.00

  line losses: IMPORT #rate as decimal <float> (ex. .1210)
  max line losses: .4 # rate a decimal maximum allowed line losses
  default line losses: .1 # rate a decimal line losses will be set to this if they are less than zero

  res non-PCE elec cost: IMPORT # $cost/kWh <float> (ex. .83)
  elec non-fuel cost: IMPORT # $cost/kWh <float> (ex. .83)

  HDD: IMPORT
  diesel prices: IMPORT
  electric non-fuel prices: IMPORT
  propane price: IMPORT
  biomass price: IMPORT
  natural gas price: 0
  
  generation numbers: IMPORT

forecast:
  end year: ABSOLUTE DEFAULT  # end year <int>
  population: IMPORT
  electricity: IMPORT 

residential buildings:
  min kWh per household: 6000 # minimum average consumed kWh/year per house<int>
  enabled: False
  lifetime: ABSOLUTE DEFAULT # number years <int>  
  start year: ABSOLUTE DEFAULT # start year <int>
  average refit cost: 11000 # cost/refit <float>
  data: IMPORT

non-residential buildings:
  enabled: False
  lifetime: ABSOLUTE DEFAULT # number years <int>  
  start year: ABSOLUTE DEFAULT # start year <int>
  average refit cost: 7.00 # cost/sqft. <float>
  cohort savings multiplier: .26 # pecent as decimal <float>
  com building data: IMPORT
  number buildings: IMPORT
  com building estimates: IMPORT

water wastewater:
  enabled: False
  lifetime:  ABSOLUTE DEFAULT # number years <int>  
  start year:  ABSOLUTE DEFAULT # start year <int>
  audit cost: 10000 # price <float> (ex. 10000)
  average refit cost: 360.00 # cost/per person <float>
  data: IMPORT

  electricity refit reduction: .25 # decimal precent <float> percent saved by preforming electricity refit 
  heating fuel refit reduction: .35 # decimal precent <float> percent saved by preforming heating fuel refit 
  
  
  heat recovery multiplier:
    True: .5 # precent as decimal <float> 
    False: 1.0 # precent as decimal <float> 

#interties:
#  enabled: False
#  lifetime : ABSOLUTE DEFAULT # number years <int> 
#  start year : ABSOLUTE DEFAULT # start year <int>
#  phase: ABSOLUTE DEFAULT # project phase <string> 
#  hr installed: ABSOLUTE DEFAULT # is the hreat recovery installed <bool>
#  hr operational: ABSOLUTE DEFAULT # is the heat recovery operational <bool>
#  road needed: ABSOLUTE DEFAULT # is a road needed <bool> 
#  cost known: ABSOLUTE DEFAULT # is the cost known <bool>
#  cost: ABSOLUTE DEFAULT # cost for initerite <float>
#  resource potential: ABSOLUTE DEFAULT #<string>
#  resource certainty: ABSOLUTE DEFAULT #<string>
  
  
#  loss per mile: .001 # precent as decimal <float> (ex. .001)
#  o&m cost: 10000.00 # $cost/kWh <float> 
#  transmission line cost : 
#    True:  500000 # road needed
#    False: 250000 # road not needed

#TODO: move to anoter file and save value used with output??
# like what happens with the .csv stuff
construction multipliers:
  "Aleutians": 1.4 # precent as decimal <float> (ex. 1.4)
  "Bering Straits": 1.8 # precent as decimal <float> (ex. 1.8)
  "Bristol Bay": 1.25 # precent as decimal <float> (ex. 1.25)
  "Copper River/Chugach": 1.1 # precent as decimal <float> (ex. 1.1)
  "Kodiak": 1.18 # precent as decimal <float> (ex. 1.18)
  "Lower Yukon-Kuskokwim": 1.6 # precent as decimal <float> (ex. 1.6)
  "North Slope": 1.8 # precent as decimal <float> (ex. 1.8)
  "Northwest Arctic": 1.7 # precent as decimal <float> (ex. 1.7)
  "Southeast": 1.15 # precent as decimal <float> (ex. 1.15)
  "Yukon-Koyukuk/Upper Tanana": 1.4 # precent as decimal <float> (ex. 1.4)
"""


### This is used as the model defaults uesd by set up in creating runs of the 
### model
for_setup = """community: 
  current year: 2014 #year to base npv calculations on <int>
  interest rate: .05 # rate as decimal <float> (ex. .05) 
  discount rate: .03 # rate as decimal <float> (ex. .03)
  model financial: True

forecast:
  end year: 2040 # end year <int>

residential buildings: 
  enabled: True
  lifetime: 15 # number years <int>  
  start year: 2017 # start year <int>

non-residential buildings:
  enabled: True
  lifetime: 10 # number years <int>  
  start year: 2017 # start year <int>

water wastewater:
  enabled: True
  lifetime: 15 # number years <int>  
  start year: 2017 # start year <int>
"""
