"""
preprocessor.py
ross spicer

process data into a format for the model to use 
"""
from pandas import DataFrame,read_csv
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
    #~ df.to_csv(out_dir+"electricity.csv")
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
    #~ df.to_csv(out_dir+"eia.csv")
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
        
def create_forecast_inputs (pop_file, pce_file, out_dir, com_id):
    """
    create the input file used by the forecast module
    pre:
        electricity, and populations preconditions
    post:
        some files are saved in out dir, and the forecast_input 
    DataFrame is returned
    """
    pop = population(pop_file,out_dir,com_id)
    con = pce_electricity(pce_file,com_id)
    t = []
    
    for year in pop.T.keys():
        try:
            temp = con.T[year].values.tolist()
            temp.insert(0,pop.T[year].values[0])
            temp.insert(0,int(year))
            t.append(temp)
        except KeyError:
            temp = [float("nan"),float("nan"),float("nan"),
                    float("nan"),float("nan")]
            temp.insert(0,pop.T[year].values[0])
            temp.insert(0,int(year))
            t.append(temp)

    
    df = DataFrame(t,columns= ["years","population","residential",
                "community","commercial","gov","unbilled"]).set_index("years")
    df.to_csv(out_dir+"forecast_inputs.csv")
    return df
    
def preprocess(data_dir, out_dir, com_id):
    """
    """
    data_dir = os.path.abspath(data_dir) + '/'
    out_dir = os.path.abspath(out_dir) + '/'
    # copy files that still need their own preprocessor function yet
    shutil.copy(data_dir+"com_benchmark_data.csv", out_dir)
    shutil.copy(data_dir+"com_building_estimates.csv", out_dir)
    shutil.copy(data_dir+"com_num_buildings.csv", out_dir)
    shutil.copy(data_dir+"diesel_fuel_prices.csv", out_dir)
    shutil.copy(data_dir+"hdd.csv", out_dir)
    shutil.copy(data_dir+"res_model_data.csv", out_dir)
    shutil.copy(data_dir+"ww_assumptions.csv", out_dir)
    
    population(data_dir+"population.csv",out_dir,com_id)
    
    try:
        electricity(data_dir+"power-cost-equalization-pce-data.csv", out_dir,
                                                                    com_id)
    except KeyError:
        electricity(data_dir+"EIA.csv", out_dir, com_id)
    
