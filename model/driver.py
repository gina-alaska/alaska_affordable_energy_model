"""
driver.py

    will run the model
"""
from community_data import CommunityData
from forecast import Forecast
from residential_buildings import ResidentialBuildings
from community_buildings import CommunityBuildings
from wastewater import WaterWastewaterSystems
from pandas import DataFrame
import numpy as np



def test (community, com_data_file = "../data/community_data_template.csv"):
    """ Function doc """
    cd = CommunityData(com_data_file, community)
    
    fc = Forecast(cd)
    rb = ResidentialBuildings(cd, fc)
    rb.run()
    cb = CommunityBuildings(cd, fc)
    cb.run()
    ww = WaterWastewaterSystems(cd, fc)
    ww.run()
    
    #~ fc.calc_electricity_totals()
    #~ fc.forecast_population()
    fc.forecast_consumption()
    fc.forecast_generation()
    fc.forecast_average_kW()
    #~ fc.forecast_households()
    fc.calc_total_HF_forecast()
    
    df = DataFrame( {"pop": fc.population,
                     "HH" : fc.households,
                     "kWh consumed" : fc.consumption,
                     "kWh generation": fc.generation,
                     "avg. kW": fc.average_kW,
                     "res HF": fc.res_HF,
                     "com HF":fc.com_HF,
                     "ww HF":fc.www_HF,
                     "total HF": fc.total_HF,}, 
                     np.array(range(len(fc.population))) + fc.start_year)
    #~ df.to_csv("test.csv", columns = ["pop","HH", "kWh consumed",
                                                #~ "kWh generation","avg. kW",
                                                #~ "res HF", "com HF", "ww HF",
                                                #~ "total HF"])
    return df, (cd,fc,rb,cb,ww)
