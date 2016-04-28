"""
cli_lib.py

    functionality used by multiple cli commands
"""
import os
import shutil
from aaem import summaries



def copy_model_data (repo, raw):
    """
        copies the data needed to run the model from the data repo to the raw 
    data folder.
    
    pre:
        repo : path to the data repo
        raw: path to the raw data folder
    post:
        the files used to run the preprocessor are copied to the raw directory
    """
    shutil.copy(os.path.join(repo,
                    "power-cost-equalization-pce-data.csv"), raw)
    shutil.copy(os.path.join(repo, "com_building_estimates.csv"), raw)
    shutil.copy(os.path.join(repo, "com_num_buildings.csv"), raw)
    shutil.copy(os.path.join(repo, "cpi.csv"), raw)
    shutil.copy(os.path.join(repo, "diesel_fuel_prices.csv"), raw)
    shutil.copy(os.path.join(repo, "eia_generation.csv"), raw)
    shutil.copy(os.path.join(repo, "eia_sales.csv"), raw)
    shutil.copy(os.path.join(repo, "hdd.csv"), raw)
    shutil.copy(os.path.join(repo, "heating_fuel_premium.csv"), raw)
    shutil.copy(os.path.join(repo, "interties.csv"), raw)
    shutil.copy(os.path.join(repo, "non_res_buildings.csv"), raw)
    shutil.copy(os.path.join(repo, "population.csv"), raw)
    shutil.copy(os.path.join(repo, "population_neil.csv"), raw)
    shutil.copy(os.path.join(repo, "purchased_power_lib.csv"), raw)
    shutil.copy(os.path.join(repo, "res_fuel_source.csv"), raw)
    shutil.copy(os.path.join(repo, "res_model_data.csv"), raw)
    shutil.copy(os.path.join(repo, "valdez_kwh_consumption.csv"), raw)
    shutil.copy(os.path.join(repo, "ww_assumptions.csv"), raw)
    shutil.copy(os.path.join(repo, "ww_data.csv"), raw)
    shutil.copy(os.path.join(repo, "VERSION"), raw)
    shutil.copy(os.path.join(repo, "community_list.csv"), raw)
    shutil.copy(os.path.join(repo, "propane_price_estimates.csv"), raw)
    shutil.copy(os.path.join(repo, "biomass_price_estimates.csv"), raw)
    shutil.copy(os.path.join(repo, "generation_limits.csv"), raw)
  
def generate_summaries (coms, base):
    """
        generates the summaries 
    
    pre:
        coms : dictionary of run communites
        base: path to root of out put folder
    post:
        summaries are written
    """
    summaries.res_log(coms,os.path.join(base,'results'))
    summaries.com_log(coms,os.path.join(base,'results'))
    summaries.village_log(coms,os.path.join(base,'results'))
    summaries.building_log(coms,os.path.join(base,'results'))
    summaries.fuel_oil_log(coms,os.path.join(base,'results'))
    summaries.forecast_comparison_log(coms,os.path.join(base,'results'))
    
def list_files (directory, root = None):
    """ Function doc """
    l = []
    if root is None:
        root = directory
    for item in os.listdir(directory):
        if item[0] == '.':
            continue
        if not os.path.isdir(os.path.join(directory,item)):
            l.append(os.path.join(directory.replace(root,""),item))
        else:
            l += list_files(os.path.join(directory,item),root)
    return l
    
