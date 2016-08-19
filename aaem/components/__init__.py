from importlib import import_module

comp_lib = {
    "residential buildings": "residential_buildings",
    "non-residential buildings": "community_buildings",
    "water wastewater": "wastewater",
    "wind power": "wind_power",
    'solar power': "solar_power",
    'biomass cordwood': "biomass_wood",
    'biomass pellet': 'biomass_pellet',
    'ASHP residential': 'ashp_res',
    'ASHP non-residential': 'ashp_non-res',
    'Hydropower': 'hydro',
    'transmission': 'interties',
    'heat recovery': 'heat_recovery',
    'diesel efficiency': 'diesel_efficiency',
        }

comp_order = ["residential buildings",
              "non-residential buildings",
              "water wastewater",
              "wind power",
              'solar power',
              'biomass cordwood',
              'biomass pellet',
              'ASHP residential',
              'ASHP non-residential',
              'Hydropower',
              'transmission',
              'heat recovery',
              'diesel efficiency']

def get_raw_data_files():
    raw_data_files = []
    for comp in comp_lib:
        try:
            raw_data_files += \
                import_module("aaem.components." +comp_lib[comp]).raw_data_files
        except AttributeError:
            pass
    return raw_data_files
