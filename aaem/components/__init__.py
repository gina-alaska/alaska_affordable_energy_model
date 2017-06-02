from importlib import import_module
import definitions as definitions


comp_lib = {
    "Residential Energy Efficiency": "residential_buildings",
    "Non-residential Energy Efficiency": "non_residential",
    "Water and Wastewater Efficiency": "wastewater",
    "Wind Power": "wind_power",
    'Solar Power': "solar_power",
    #~ 'Biomass for Heat (Cordwood)': "biomass_wood",
    #~ 'Biomass for Heat (Pellet)': 'biomass_pellet',
    #~ 'Residential ASHP': 'ashp_res',
    #~ 'Non-Residential ASHP': 'ashp_non_res',
    'Hydropower': 'hydro',
    'Transmission and Interties': 'transmission',
    'Heat Recovery': 'heat_recovery',
    #~ 'Diesel Efficiency': 'diesel_efficiency',
        }

comp_order = ["Residential Energy Efficiency",
              "Non-residential Energy Efficiency",
              "Water and Wastewater Efficiency",
              "Wind Power",
              'Solar Power',
              #~ 'Biomass for Heat (Cordwood)',
              #~ 'Biomass for Heat (Pellet)',
              #~ 'Residential ASHP',
              #~ 'Non-Residential ASHP',
              'Hydropower',
              'Transmission and Interties',
              'Heat Recovery',
              #~ 'Diesel Efficiency'
    ]


    

