
from driver import run_model
from preprocessor import preprocess
import os.path
from pandas import read_csv, concat

defaults = """community: 
  current year: 2014 #year to base npv calculations on <int>
  interest rate: .05 # rate as decimal <float> (ex. .05) 
  discount rate: .03 # rate as decimal <float> (ex. .03)
  model financial: True
  
  #do these come from community profiles?
  #consumption kWh: 384000.00 # kWh consumed/year <float> 12345.00
  line losses: .1210 #rate as decimal <float> (ex. .1210)

forecast:
  end year: 2040 # end year <int>

residential buildings: 
  enabled: True
  lifetime: 15 # number years <int>  
  start year: 2015 # start year <int>

community buildings:
  enabled: True
  lifetime: 10 # number years <int>  
  start year: 2015 # start year <int>

water wastewater:
  enabled: True
  lifetime: 15 # number years <int>  
  start year: 2015 # start year <int>
"""



def setup_reg_test (directory, community, data_dir):
    """
    sets up a regression test 
    """
    directory = os.path.abspath(directory)
    try:
        os.makedirs(os.path.join(directory,"config"))
    except OSError:
        pass
        
    config_text = "community:\n  name: " + community +\
                  " # community provided by user\n"
    config_file = open(os.path.join(directory, "config",
                                    "community_data.yaml"), 'w')
    config_file.write(config_text)
    config_file.close()
    def_file = open(os.path.join(directory, "config", 
                                    "test_defaults.yaml"), 'w')
    def_file.write(defaults)
    def_file.close()
    
    
    driver_text =  'overrides: ' + os.path.join(directory,"config",
                                                "community_data.yaml") + '\n'
    driver_text += 'defaults: ' + os.path.join(directory,"config",
                                                "test_defaults.yaml") + '\n'
    driver_text += 'data directory: ' + os.path.join(directory,
                                                "input_data") + '\n'
    driver_text += 'output directory path: ' + os.path.join(directory,
                                                 "results") + '\n'
    driver_text += 'output directory suffix: NONE # TIMESTAMP|NONE|<str>\n'
    
    driver_file = open(os.path.join(directory, 
                       community.replace(" ", "_") + "_driver.yaml"), 'w')
    driver_file.write(driver_text)
    driver_file.close()
    
    preprocess(data_dir,os.path.join(directory,"input_data"),community)
    
    run_model(os.path.join(directory, 
              community.replace(" ", "_") + "_driver.yaml"))
    os.rename(os.path.join(directory,"results"),
              os.path.join(directory,"baseline_results"))
    
def reg_test (config_file, lim = .1):
    """
    test the driver with manley data
    """
    model, out_dir = run_model(os.path.abspath(config_file))
    
    out_dir = os.path.dirname(os.path.dirname(out_dir))
    new_e = read_csv(os.path.join(out_dir,"results",
                                                    "electricity_forecast.csv"),
                                                    index_col=0, header=0, 
                                                    comment = "#")
    base_e = read_csv(os.path.join(out_dir,"baseline_results",
                                                    "electricity_forecast.csv"),
                                                    index_col=0, header=0,
                                                    comment = "#")
                                                    
    new_f = read_csv(os.path.join(out_dir,"results",
                                                   "heating_fuel_forecast.csv"),
                                                    index_col=0, header=0, 
                                                    comment = "#")
    base_f = read_csv(os.path.join(out_dir,"baseline_results",
                                                   "heating_fuel_forecast.csv"),
                                                    index_col=0, header=0,
                                                    comment = "#")
                                                    
    cols_e = ["population",
                "total_electricity_consumed [kWh/year]",
                "total_electricity_generation [kWh/year]"]
                
                
    cols_f = ["population",
                "heating_fuel_residential_consumed [gallons/year]",
                "heating_fuel_residential_consumed [mmbtu/year]",
                "heating_fuel_non-residential_consumed [gallons/year]",
                "heating_fuel_non-residential_consumed [mmbtu/year]",
                "heating_fuel_water-wastewater_consumed [gallons/year]",
                "heating_fuel_water-wastewater_consumed [mmbtu/year]",
                "heating_fuel_total_consumed [gallons/year]",
                "heating_fuel_total_consumed [mmbtu/year]"]

    l_e = (new_e[cols_e] > (base_e[cols_e] * (1 - lim))) 
    h_e = (new_e[cols_e] < (base_e[cols_e] * (1 + lim)))

    l_f = (new_f[cols_f] > (base_f[cols_f] * (1 - lim))) 
    h_f = (new_f[cols_f] < (base_f[cols_f] * (1 + lim)))


    res_e = (l_e == h_e)
    res_f = (l_f == h_f)
    
    results = concat([res_e,res_f],axis=1)
    
    results.to_csv(os.path.join(out_dir,"forecast_comparison_results.csv"), 
                                       index_label="year")
    
    return results, model