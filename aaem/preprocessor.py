"""
preprocessor.py
ross spicer

process data into a format for the model to use 
"""
from pandas import DataFrame,read_csv, concat
import shutil
import os.path

def population (in_file, out_dir, com_id):
    """
    create the population input file
    
    pre:
        in_file is the most current population file in the data-repo
        out dir is a path, com_id is a string ex "Adak"
    post: 
        a file is saved, and the data frame it was generated from is returned
    """
    pop_data = read_csv(in_file, index_col = 1) # update to GNIS
    pops = pop_data.ix[com_id]["2003":"2014"].values
    years = pop_data.ix[com_id]["2003":"2014"].keys().values.astype(int)
    #~ return pops, years
    df = DataFrame([years,pops],["year","population"]).T.set_index("year")
    df.to_csv(out_dir+"population.csv")
    return df
    
def pce_electricity (in_file, com_id):
    """
    parse PCE electricity data 
    
    pre:
        in_file is the most current PCE file in the data-repo
    com_id is a string ex "Adak"
    
    post: 
       a data frame is returned
    """
    df = read_csv(in_file, index_col = 1) # update to GNIS
    data = df.ix[com_id][["year","residential_kwh_sold",
                                     "commercial_kwh_sold",
                                     "community_kwh_sold",
                                     "government_kwh_sold",
                                     "unbilled_kwh"]]
    sums = []
    for year in set(data["year"].values):
        if len(data[data["year"] == year]) != 12:
            continue
        temp = data[data["year"] == year].sum()
        temp["year"] = int(year)
        sums.append(temp)
    df = DataFrame(sums).set_index("year")
    for key in df.keys():
        df[key.split('_')[0]] = df[key]
        del(df[key])
    return df
    
def eia_electricity (in_file, com_id):
    """
    parse EIA electricity data 
    
    pre:
        in_file is the most current PCE file in the data-repo
    com_id is a string ex "Sitka"
    
    post: 
       a data frame is returned
    """
    df = read_csv(in_file, index_col = 0, comment='#')
    data = df.ix[com_id][['Data Year','Sum - Residential Megawatthours',
            'Sum - Commercial Megawatthours',
            'Sum - Industrial Megawatthours']].values.astype(int)
    df = DataFrame(data,
                 columns=["year","residential",
                          "commercial","industrial"]).set_index("year")
    return df
    
def electricity (in_file, out_dir, com_id):
    """
    create the electricity input file
    
    pre:
        in_file is the most current PCE file in the data-repo
        out dir is a path, com_id is a string ex "Adak"
    post: 
        a file is saved, and the data frame it was generated from is returned
    """
    try:
        data = pce_electricity (in_file, com_id)
        data["industrial"] = data["residential"]/0-data["residential"]/0
    except KeyError:
        data = eia_electricity (in_file, com_id)
        nans = data["residential"]/0-data["residential"]/0
        data["community"] = nans
        data["government"] = nans
        data["unbilled"] = nans
    data.to_csv(out_dir+"electricity.csv")
    return data

def wastewater (data_file, assumptions_file, out_dir, com_id):
    """
    preprocess wastewater data
    
    pre:
        data_file & assumptions_file are the most current wastewater and 
    assumption files from the AAEM data repo. out dir is a path, com_id is
    a string ex "Adak"
    post:
        a file is saved in out_dir
    exceptions:
        raises a key error if the community is not in the waste water data
    or if the system type is unknown
    """
    
    out_file = out_dir+"wastewater_data.csv"
    fd = open(out_file,'w')
    fd.write("# " + com_id + " wastewater data\n")
    fd.write("# System Type: The system type \n")
    fd.write("# SQFT: system square feet  \n")
    fd.write("# HF Used: gal/yr Heating fuel used pre-retrofit\n")
    fd.write("# HF w/Retro: gal/yr Heating fuel used post-retrofit\n")
    fd.write("# kWh/yr: kWh/yr used pre-retrofit\n")
    fd.write("# kWh/yr w/ retro: kWh/yr used post-retrofit\n")
    fd.write("# Implementation Cost: cost to refit \n")
    fd.write("# HR: heat recovery (units ???) \n")
    fd.write("# Steam District: ??? \n")
    fd.write("# HDD kWh: assumption ??? \n") # JEN: what are these numbers?
    fd.write("# HDD HF: an assumption ??? \n")
    fd.write("# pop kWh: an assumption ??? \n")
    fd.write("# pop HF: an assumption ??? \n")
    fd.write("#### #### #### #### ####\n")
    fd.close()
    
    try:
    
        ww_d = read_csv(data_file, comment = '#', index_col = 0).ix[com_id]
    except KeyError:
        raise StandardError, str(com_id) + " is not in " + data_file
    try:
        ww_a = read_csv(assumptions_file, comment = '#', index_col = 0)
        ww_a = ww_a.ix[ww_d["System Type"]]
    except KeyError:
        raise StandardError, "wastewater system type is unknown"
    df = concat([ww_d,ww_a])
    df.to_csv(out_file, mode = 'a')
   
def residential (fuel_file, data_file, out_dir, com_id):
    """ Function doc """
    out_file = out_dir + "residential_data.csv"
    fd = open(out_file,'w')
    fd.write("# " + com_id + " residential data\n")
    fd.write("# energy_region: region used by model \n")
    fd.write("# year: year of data  collected \n")
    fd.write("# total_occupied: # houses occupied \n")
    fd.write("# BEES_number: # of houses at BEES standard \n")
    fd.write("# BEES_avg_area: average Sq. ft. of BEES home \n")
    fd.write("# BEES_avg_EUI: BEES energy use intensity MMBtu/sq. ft.\n")
    fd.write("# BEES_total_consumption: BEES home energy consumption MMBtu \n")
    
    fd.write("# pre_number: # of houses pre-retrofit \n")
    fd.write("# pre_avg_area: average Sq. ft. of pre-retrofit home \n")
    fd.write("# pre_avg_EUI: pre-retrofit energy use intensity MMBtu/sq. ft.\n")
    
    fd.write("# post_number: # of houses at post-retrofit \n")
    fd.write("# post_avg_area: average Sq. ft. of post-retrofithome \n")
    fd.write("# post_avg_EUI: post-retrofit energy use intensity "+\
             "MMBtu/sq. ft.\n")
    fd.write("# post_total_consumption: post-retrofit home energy consumption"+\
             " MMBtu \n")
             
    fd.write("# opportunity_non-Wx_HERP_BEES:  # of houses \n")
    fd.write("# opportunity_potential_reduction: ???? \n")
    fd.write("# opportunity_savings: potention savings in heating Fuel(gal)\n")
    fd.write("# opportunity_total_percent_community_savings: ???\n")
    
    fd.write("# Total; Utility Gas; LP; Electricity; Fuel Oil; "+\
            "Coal; Wood; Solar; Other; No Fuel Used: % of heating fuel types\n")
    fd.write("#### #### #### #### ####\n")
    fd.write("key, value\n")
    fd.close()
    
    fuel = read_csv(fuel_file, index_col=0, comment = "#").ix[com_id]
    fuel = fuel.ix[["Total", "Utility Gas", "LP", "Electricity", "Fuel Oil",
                    "Coal", "Wood", "Solar", "Other", "No fuel used"]]
    
    data = read_csv(data_file, index_col=0, comment = "#").ix[com_id]
    
    df = concat([data,fuel])
    del df.T["energy_region"]
    df.to_csv(out_file,mode="a")

    

    
def preprocess (data_dir, out_dir, com_id):
    """
    preprocess data in to data dir 
    
    pre:
        data dir: path to the data files from the AAEM-data dir
        out_dir: save location
        com_id: community id("Name")
    post:
        all of the files necessary to run the model are in out_dir, if out_dir
    dose not it exist it is created
    """
    data_dir = os.path.abspath(data_dir) + '/'
    out_dir = os.path.abspath(out_dir) + '/'
    try:
        os.makedirs(out_dir)
    except OSError:
        pass
    
    ### copy files that still need their own preprocessor function yet
    shutil.copy(data_dir+"com_benchmark_data.csv", out_dir)
    shutil.copy(data_dir+"com_building_estimates.csv", out_dir)
    shutil.copy(data_dir+"com_num_buildings.csv", out_dir)
    shutil.copy(data_dir+"diesel_fuel_prices.csv", out_dir)
    shutil.copy(data_dir+"hdd.csv", out_dir)
    shutil.copy(data_dir+"cpi.csv", out_dir)
    ###
    
    
    
    population(data_dir+"population.csv",out_dir,com_id)
    residential(data_dir+"res_fuel_source.csv", data_dir+"res_model_data.csv",
                out_dir, com_id)
    wastewater(data_dir+"ww_data.csv", data_dir+"ww_assumptions.csv",
               out_dir, com_id)
    
    
    try:
        electricity(data_dir+"power-cost-equalization-pce-data.csv", out_dir,
                                                                    com_id)
    except KeyError:
        electricity(data_dir+"EIA.csv", out_dir, com_id)
    
