from importlib import import_module

comp_lib = {
    "residential buildings": "residential_buildings",
    "non-residential buildings": "community_buildings",
    "water wastewater": "wastewater",
    "wind power": "wind_power",
    'solar power': "solar_power",
    'biomass pellet': 'biomass_pellet'
    }


def get_raw_data_files():
    raw_data_files = []
    for comp in comp_lib:
        try:
            raw_data_files += \
                import_module("aaem.components." +comp_lib[comp]).raw_data_files
        except AttributeError:
            pass
    return raw_data_files
