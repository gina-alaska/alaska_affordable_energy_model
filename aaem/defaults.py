"""
defaults.py

this file contains default yaml file info as strings
"""




for_setup = """community: 
  current year: 2014 #year to base npv calculations on <int>
  interest rate: .05 # rate as decimal <float> (ex. .05) 
  discount rate: .03 # rate as decimal <float> (ex. .03)
  model financial: True
  
  #do these come from community profiles?
  #consumption kWh: 384000.00 # kWh consumed/year <float> 12345.00
  line losses: .1210 #rate as decimal <float> (ex. .1210)

forecast:
  end year: 2040 # end year <int>

residential buildings: 
  enabled: True
  lifetime: 15 # number years <int>  
  start year: 2015 # start year <int>

community buildings:
  enabled: True
  lifetime: 10 # number years <int>  
  start year: 2015 # start year <int>

water wastewater:
  enabled: True
  lifetime: 15 # number years <int>  
  start year: 2015 # start year <int>
"""
