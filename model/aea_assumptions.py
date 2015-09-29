"""
aea_assumptions.py
Ross Spicer
created: 2015/09/18

    assumptions by the AEA
"""

loss_per_mile = .001 # Transmission line loss/mile (%)
O_and_M_cost = 10000.00 # $/mile/year
project_life = 20 # years
start_year = 2016

fuel_repairs = 500  # $/year
fuel_OM = 1000 # $/year
diesel_generator_OM = 84181 # $/yr
diesel_generation_eff = 10.802351555 # kWh/gal

heating_fuel_premium = 0.45 # $

interest_rate = .05
discount_rate = .03

transmission_line_cost = {True:  500000, # road needed  -- $/mi
                          False: 250000  # road not needed -- $/mi
                         } 


gallons_per_barrel = 42 #gal/barrel - from Diesel fuel price tab 


## Wastewater assumptions

## heating degree days - kWh?
HDD_KWH = {"Circulating/Gravity": 3.93236229561503,
           "Circulating/Vac": 11.4132439375221,
           "Haul": 0,
           "Pressure/Gravity": -0.848162217309015,
           "Wash/HB": -0.528728194855285,
           }

## heating degree days - Gallons HF?
HDD_HF = {"Circulating/Gravity": 0.544867662390884,
           "Circulating/Vac": -0.297715988257898,
           "Haul": 0,
           "Pressure/Gravity": 2.2408614639956,
           "Wash/HB": 0.17155240756494,
           }

## Population - kWh?
POP_KWH = {"Circulating/Gravity": 54.4093002543652,
           "Circulating/Vac": 161.481419074818,
           "Haul": 69.7824047085659,
           "Pressure/Gravity": 263.448648548957,
           "Wash/HB": 144.393961746201,
           }
           
## Population - Gallons HF?
POP_HF = {"Circulating/Gravity": 3.57835240238995,
           "Circulating/Vac": 23.8252508422151,
           "Haul": 7.06151797216891,
           "Pressure/Gravity": -78.7469560579852,
           "Wash/HB": 22.3235825717145,
           }
           
ww_baseline_retrofit_cost = 360 # capex/person ($)

# per region based on department of ED estimates 
# were percents now decimals
construction_mulitpliers = { "Aleutians": 1.4, 
                             "Bering Straits": 1.8,
                             "Bristol Bay": 1.25,
                             "Copper River/Chugach":1.1,
                             "Kodiak":1.18,
                             "Lower Yukon-Kuskokwim":1.6,
                             "North Slope":1.8,
                             "Northwest Arctic":1.7,
                             "Southeast": 1.15,
                             "Yukon-Koyukuk/Upper Tanana":1.4,
                            }
                            
                             


heat_recovery_multiplier = {True:  0.5, 
                            False: 1.0
                           }

w_ww_audit_cost = 10000



#~ 14356.0653747073
#~ 
#~ 
#~ 
#~ 3195









## own file? 
com_estimated_enegery_use = {
"kWh/sf/yr<300":
    {"education":2.0686402976, "health care":3.9937030563, "office":2.9619198286, "other":2.8562067795, 
    "public_assembly":2.6686973586, "public_order":6.1944656937, "warehouse":5.15258984672822, "unknown":3.6994604087},
"gal/sf/yr<300":
    {"education":.90, "health care":.70, "office":.70, "other":0.422614765874726, 
    "public_assembly":.50, "public_order":.50, "warehouse":1.00, "unknown":0.6746592523
},
"est.sf<300":
    {"education":14356.0653747073, "health care":2377.5763888889, "office":1894.0630952381, "other":2557.8465658257, 
"public_assembly":3195, "public_order":2409.2584022039, "warehouse":6279.4886363636, "unknown":1500},

}


com_average_refit_cost = 7.00 # $/sf 
com_cohort_savings_multiplier = .26

# TODO: do the classy part later
class AEAAssumptions (object):
    """ Class doc """
    
    def __init__ (self):
        """ Class initialiser """
        pass
