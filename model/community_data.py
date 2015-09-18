"""
community_data.py
ross spicer
created: 2015/09/16

    a place holder for an eventual community data module. the manley_data
is here for testing
"""

## w&ww - water and wastewater
## it - intertie


# True == 'yes'/ False == 'no'
manley_data = {
        "community": "Manley Hot Springs",
        "region": "Yukon-Koyukuk/Upper Tanana",
        "population": 89, # number people
        "HDD": 14593, # Degrees/day
        
        
        "generation_total": 440077.00, # kWh/yr 
        "consumption/year": 384000, # kWh/year TODO: probably has a better name
        "diesel_consumed": 40739, # gallons
        
        "dist_to_nearest_comm": 53, # miles
        "cost_power_nearest_comm": 00.1788, # $/kWh pre-PCE
        
        "res_non-PCE_elec_cost": 00.83, # $/kWh
        
        "line_losses": .1210, # %  # or is this an assumption
            
        "it_lifetime" : 20, # years
        "it_start_year" : 2016, # a year 
        "it_phase": "Recon", # orange is supposed to be linked from
                                    #annother tab, but this olny shows up here
        "it_hr_installed": True, 
        "it_hr_operational": True,
        "it_road_needed": True, #road needed for for T&D
        "it_cost_known": False,
        "it_cost": float('nan'), # not available for here
        "it_resource_potential": "N/a",
        "it_resource_certainty": "N/a",

        "w&ww_system_type": "Haul", 
        "w&ww_energy_use_known": False,
        "w&ww_energy_use_electric": float("nan"), # kWh 
        "w&ww_energy_use_hf": float("nan"), # Gallons
        "w&ww_heat_recovery_used": False,
        "w&ww_heat_recovery": float("nan"), # units?
        "w&ww_audit_preformed": False,
        "w&ww_audit_savings_elec": float("nan"), # kWh
        "w&ww_audit_savings_hf": float("nan"), # gal
        "w&ww_audit_cost": float("nan"), # $ -- make cost_from_audit
        
}

# TODO: i'think this should be written last
class CommunityData (object):
    """ Class doc """
    
    def __init__ (self):
        """ Class initialiser """
        pass
        
    def __getitem__ (self):
        """ Function doc """
        pass

    def __setitem__ (self):
        """ Function doc """
        pass
        
    def __del__ (self):
        """ Function doc """
        pass


        
        
