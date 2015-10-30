from pandas import DataFrame,read_csv


def population (in_file, out_dir, com_id):
    """
    
    """
    pop_data = read_csv(in_file, index_col = 1) # update to GNIS
    pops = pop_data.ix[com_id]["2003":"2014"].values
    years = pop_data.ix[com_id]["2003":"2014"].keys().values.astype(int)
    #~ return pops, years
    df = DataFrame([years,pops],["year","population"]).T.set_index("year")
    df.to_csv(out_dir+"population.csv")
    return df
    
def electricity (in_file, out_dir, com_id):
    """
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
    df.to_csv(out_dir+"electricity.csv")
    return df

def create_forecast_inputs (pop_file, pce_file, out_dir, com_id):
    """
    """
    pop = population(pop_file,out_dir,com_id)
    con = electricity(pce_file,out_dir,com_id)
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
