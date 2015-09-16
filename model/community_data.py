"""
community_data.py
ross spicer
created: 2015/09/16

    a place holder for an eventual community data module. the manley_data
is here for testing
"""


manley_data = {
        "community": "Manley Hot Springs",
        "HR_installed": True, # True == 'yes'/ False == 'no'
        "HR_operational": True,
        "dist_to_nearest_comm": 53, # miles
        "cost_power_nearest_comm": 00.18, # $/kWh pre-PCE
        "project_phase": "Recon", # orange is supposed to be linked from
                                    #annother tab, but this olny shows up here
        "road_needed": True, #road needed for for T&D
        "intertie_cost_known": False,
        "intertie_cost": float('nan'), # not available for here
        "consumption/year": 384000, # kWh/year
        "line_losses": .1210, # %
        "resource_potential": "N/a",
        "resource_certainty": "N/a",
        "diesel_consumed": 40739, # gallons
        "res_non-PCE_elec_cost": 00.83, # $/kWh
        "HDD": 14593, # Degrees/day
        "population": 89, # number people
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
