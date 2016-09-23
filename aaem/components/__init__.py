from importlib import import_module

comp_lib = {
    "Residential Energy Efficiency": "residential_buildings",
    "Non-residential Energy Efficiency": "non-residential",
    "Water and Wastewater Efficiency": "wastewater",
    "Wind Power": "wind_power",
    'Solar Power': "solar_power",
    'Biomass for Heat (Cordwood)': "biomass_wood",
    'Biomass for Heat (Pellet)': 'biomass_pellet',
    'Residential ASHP': 'ashp_res',
    'Non-Residential ASHP': 'ashp_non-res',
    'Hydropower': 'hydro',
    'Transmission and Interties': 'transmission',
    'Heat Recovery': 'heat_recovery',
    'Diesel Efficiency': 'diesel_efficiency',
        }

comp_order = ["Residential Energy Efficiency",
              "Non-residential Energy Efficiency",
              "Water and Wastewater Efficiency",
              "Wind Power",
              'Solar Power',
              'Biomass for Heat (Cordwood)',
              'Biomass for Heat (Pellet)',
              'Residential ASHP',
              'Non-Residential ASHP',
              'Hydropower',
              'Transmission and Interties',
              'Heat Recovery',
              'Diesel Efficiency']

def get_raw_data_files():
    raw_data_files = []
    for comp in comp_lib:
        try:
            raw_data_files += \
                import_module("aaem.components." +comp_lib[comp]).raw_data_files
        except AttributeError:
            pass
    return raw_data_files
