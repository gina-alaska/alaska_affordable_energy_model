"""
forecast.py
Ross Spicer
created: 2015/09/18

    forecast
"""
from community_data import CommunityData
from diagnostics import diagnostics
import constants

import numpy as np
from pandas import DataFrame, read_csv, concat
import os.path

def growth(xs, ys , x):
    """
    growth function
    
    pre:
        xs,ys are arrays of known x and y values. x is a scaler or np.array 
    of values to calculate new y values for
    
    post:
        return new y values
    """
    xs = np.array(xs)
    ys = np.log(np.array(ys))
    
    xy_bar = np.average(xs*ys)
    x_bar = np.average(xs)
    y_bar = np.average(ys)
    x_sq_bar = np.average(xs**2)
    
    beta = (xy_bar - x_bar*y_bar)/(x_sq_bar- x_bar**2)
    alpha = y_bar - beta* x_bar
    return np.exp(alpha  + beta * x)


class Forecast (object):
    """ Class doc """
    
    def __init__ (self, community_data, diag = None):
        """
        pre:
            self.cd is a community_data instance. 
        post:
            self.start_year < self.end_year are years(ints) 
            self.cd is a community_data instance. 
        """
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        self.cd = community_data
        self.fc_specs = self.cd.get_section('forecast')
        self.start_year = self.fc_specs["end year"]
        self.end_year = self.fc_specs["end year"]
        self.base_pop = self.fc_specs['population'].ix\
                    [self.cd.get_item('residential buildings',
                                            'data').ix['year']].values[0]
        self.cpi = self.cd.load_pp_csv("cpi.csv")
        self.forecast_population()
        self.forecast_consumption()
        self.merge_real_and_proj() # merge pop and con
        self.forecast_generation()
        self.forecast_average_kW()
        self.forecast_households()
        self.heat_demand_cols = []
        self.heating_fuel_cols = [] 
        self.electric_columns = []
        
    def merge_real_and_proj (self):
        """ 
            joins the measured and projected population and kWh consumption 
        dataframes.
        
        pre:
            self.population, self.fc_specs["population"],
        self.measured_consumption and self.consumption should be dataframs 
        with years as indexs. 
        post:
            self.population and self.consumption contain the population and 
        consumptions for a continuous period, containing the measured and 
        projected values
            self.p_map and self.c_map are dataframes of qualifiers on 
        self.population and self.consumption
        """
        self.p_map = concat(\
                     [self.fc_specs["population"] - self.fc_specs["population"],
                      self.population]).astype(bool).astype(str).\
                      replace("True", "P").\
                      replace("False", "M")
        self.p_map.columns  = [self.p_map.columns[0] + "_qualifier"]
        
        self.population = concat([self.fc_specs["population"],self.population])
        real = self.measured_consumption
        projected = self.consumption
        real.columns = projected.columns
        
        self.population.index = self.population.index.values.astype(int)
        
        self.c_map = concat([real-real,projected]).astype(bool).astype(str).\
                      replace("True", "P").\
                      replace("False", "M")
        
        self.c_map.columns  = [self.c_map.columns[0] + "_qualifier"]
        
        self.consumption =  concat([real,projected])
        self.consumption.index = self.consumption.index.values.astype(int)

    def calc_electricity_totals (self):
        """ 
        pre:
            'fc_electricity_used' should contain the kWh used for each key type
        post:
            self.electricty_totals is a array of yearly values of total kWh used
        """
        kWh = self.fc_specs["electricity"]
        years = kWh.T.keys().values
        totals = np.nansum([kWh['residential'].values,
                            kWh['non-residential'].values,
                                            ],0)
        self.yearly_kWh_totals = DataFrame({"year":years,
                                        "total":totals}).set_index("year")

    def forecast_population (self):
        """
        pre:
            tbd.
        post:
            self.population is a array of estimated populations for each 
        year between start and end
        """
        if len(self.fc_specs["population"]) < 10:
            msg = "the data range is < 10 for input population "\
                  "check population.csv in the models data directory"
            self.diagnostics.add_warning("forecast", msg)
        
        population = self.fc_specs["population"].T.values.astype(float)
        years = self.fc_specs["population"].T.keys().values.astype(int)
        new_years = np.array(range(years[-1]+1,self.end_year+1))
        
        population = DataFrame({"year":new_years, 
             "population":growth(years,population,new_years)}).set_index("year")
    
        population.ix[new_years[0]+15:] =\
                                    np.float64(population.ix[new_years[0]+15])
        
        self.population = population
        
        
    def forecast_consumption (self):
        """
        pre:
            tbd.
        post:
            self.consumption is a array of estimated kWh consumption for each 
        year between start and end
        """
        self.calc_electricity_totals()
        
        if len(self.yearly_kWh_totals) < 10:
            msg = "the data range is < 10 for input consumption "\
                  "check electricity.csv in the models data directory"
            self.diagnostics.add_warning("forecast", msg)
        #~ ### for fit version
        start = self.fc_specs["population"].T.keys().values[0] \
                if self.fc_specs["population"].T.keys().values[0] > \
                self.yearly_kWh_totals.T.keys().values[0] \
                else self.yearly_kWh_totals.T.keys().values[0]
             
        start = int(start)
        
        end = self.fc_specs["population"].T.keys().values[-1] \
                if self.fc_specs["population"].T.keys().values[-1] < \
                self.yearly_kWh_totals.T.keys().values[-1] \
                else self.yearly_kWh_totals.T.keys().values[-1]
        end = int(end)
        population = self.fc_specs["population"].ix[start:end].T.values[0]
        
        self.measured_consumption = self.yearly_kWh_totals.ix[start:end]
        consumption = self.measured_consumption.T.values[0]
        if len(population) < 10:
            self.diagnostics.add_warning("forecast", 
                  "the data range is < 10 matching years for "\
                  "population and consumption "\
                  "check population.csv and electricity.csv "\
                  "in the models data directory")
        
        # get slope(m),intercept(b)
        m, b = np.polyfit(population,consumption,1) 
        
        # forecast kWh where population is known
        last_year = int(self.yearly_kWh_totals.T.keys()[-1])
        fc_con_known_pop  = m * self.fc_specs["population"][last_year+1:] + b

        #forecast with forecasted population 
        fc_con_fc_pop = m * self.population + b

        consumption = concat([fc_con_known_pop, fc_con_fc_pop])
        consumption.columns = ["consumption kWh"]
        
        self.consumption = consumption
        self.start_year = last_year
        
    def forecast_generation (self):
        """
        pre:
            tbd.
            self.consumption should be a float array of kWh/yr values
        post:
            self.generation is a array of estimated kWh generation for each 
        year between start and end
        """
        generation = self.consumption/\
                    (1.0-self.cd.get_item('community','line losses'))
        self.generation = generation.apply(np.round, args=(-3,))
        
        self.generation.columns = ["kWh generation"]
        
    def forecast_average_kW (self):
        """
        ???
        """
        self.average_kW = (self.consumption/ 8760.0)\
                                /(1-self.cd.get_item('community','line losses'))
        
        self.average_kW.columns = ["avg. kW"]
        
    def forecast_households (self):
        """
        forcast # of houselholds
        """
        peps_per_house = float(self.base_pop) / \
    self.cd.get_item('residential buildings','data').ix['total_occupied']
        self.households = np.round(self.population / np.float64(peps_per_house))
        self.households.columns = ["HH"] 
        
    def get_population (self, start, end = None):
        """
        get population values from the population forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end(if provided) is a year where start <= end < self.end_year
        post:
            returns a float or list of floats
        """
        if end is None:
            return self.population.ix[start].T.values[0]
        return self.population.ix[start:end-1].T.values[0]
    
    def get_consumption (self, start, end = None):
        """
        get consumption values from the consumption forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end(if provided) is a year where start <= end < self.end_year
        post:
            returns a float or list of floats
        """
        if end is None:
            return self.consumption.ix[start].T.values[0]
        return self.consumption.ix[start:end-1].T.values[0]

    def get_generation (self, start, end = None):
        """
        get population values from the population forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end(if provided) is a year where start <= end < self.end_year
        post:
            returns a float or list of floats
        """
        if end is None:
            return self.generation.ix[start].T.values[0]
        return self.generation.ix[start:end-1].T.values[0]

    def get_households (self, start, end = None):
        """
        get households values from the households forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end(if provided) is a year where start <= end < self.end_year
        post:
            returns a float or list of floats
        """
        if end is None:
            return self.households.ix[start].T.values[0]
        return self.households.ix[start:end-1].T.values[0]
        
    def save_forecast (self, path):
        """
        save the forecast to a csv
        pre:
            everything needs to be foretasted
        post:
            saves a file
        """
       
        self.save_electirc(path)
        self.save_heat_demand(path)
        self.save_heating_fuel(path)

    
    def add_heat_demand_column (self, key, year_col, data_col):
        """ Function doc """
        self.heat_demand_cols.append(DataFrame({"year":year_col, 
                                           key:data_col}).set_index("year"))
                                           
    def add_heating_fuel_column (self, key, year_col, data_col):
        """ Function doc """
        self.heating_fuel_cols.append(DataFrame({"year":year_col, 
                                           key:data_col}).set_index("year"))
    
    def save_electirc (self, path):
        """ Function doc """
        f_name = path + "electricity_forecast.csv"
        
        kWh_con = self.consumption
        kWh_con.columns = ["total_electricity_consumed [kWh/year]"]
        c_map = self.c_map
        c_map.columns = ["total_electricity_consumed_qualifier"]
        
        kWh_gen = self.generation
        kWh_gen.columns = ["total_electricity_generation [kWh/year]"]
        g_map = c_map.replace("M","P")
        g_map.columns = ["total_electricity_generation_qualifier"]
        
        data = concat([self.population.round().astype(int), self.p_map, 
                       kWh_con.round().astype(int), c_map, 
                       kWh_gen.round().astype(int), g_map] ,axis=1)
        
        
        
        
        fd = open(f_name ,"w")
        fd.write("# Electricity Forecast for " + \
                                    self.cd.get_item("community","name") + "\n")
        fd.write("# Qualifier info: \n")
        fd.write("#   M indicates a measured value \n")
        fd.write("#   P indicates a projected value \n")
        
        fd.close()
            
        data.index = data.index.values.astype(int)
        data.to_csv(f_name, index_label="year", mode = 'a')
    
    
    def save_heat_demand (self, path):
        """ Function doc """
        f_name = path + "heat_demand_forecast.csv"
        data = concat([self.population.round().astype(int), self.p_map] + \
												self.heat_demand_cols,axis=1)
              
        idx = ['mmbtu' in s for s in data.keys()]
        total_demand = DataFrame(data[data.keys()[idx]].sum(1))
        total_demand.columns = ["heat_energy_demand_total [mmbtu/year]"]

        data = concat([data, total_demand], axis=1)
        
        fd = open(f_name ,"w")
        fd.write("# Heat Demand Forecast for " + \
                                    self.cd.get_item("community","name") + "\n")
        fd.write("# Qualifier info: \n")
        fd.write("#   M indicates a measured value \n")
        fd.write("#   P indicates a projected value \n")
        
        fd.close()
        
        for key in data.keys():
            try:
                col = data[key]
                lv = col[np.logical_not(col.apply(np.isnan))].tail(1).values[0]
                yr = col[np.logical_not(col.apply(np.isnan))].tail(1).index[0]
                col[col.index > yr] = lv
                data[key] = col.round()
            except TypeError:
                pass
            
        data.index = data.index.values.astype(int)
        data.to_csv(f_name, index_label="year", mode = 'a')
        
    
    def save_heating_fuel (self, path):
        """ Function doc """
        f_name = path + "heating_fuel_forecast.csv"
        data = concat([self.population.round().astype(int), self.p_map] + \
                                                self.heating_fuel_cols, axis=1)

        hf_gal_idx = ['heating_fuel' in s for s in data.keys()] and \
                                          ['gallons' in s for s in data.keys()]
        hf_btu_idx = ['heating_fuel' in s for s in data.keys()] and \
                                          ['mmbtu' in s for s in data.keys()]

        total_gal = DataFrame(data[data.keys()[hf_gal_idx]].sum(1)).round()
        total_gal.columns = ["heating_fuel_total_consumed [gallons/year]"]
        
        total_btu = DataFrame(data[data.keys()[hf_btu_idx]].sum(1)).round()
        total_btu.columns = ["heating_fuel_total_consumed [mmbtu/year]"]
        
        
        data = concat([data,total_gal,total_btu],axis=1)
        
        fd = open(f_name ,"w")
        fd.write("# Heating Fuel Forecast for " + \
                                    self.cd.get_item("community","name") + "\n")
        fd.write("# Qualifier info: \n")
        fd.write("#   M indicates a measured value \n")
        fd.write("#   P indicates a projected value \n")
        fd.close()
        for key in data.keys():
            try:
                col = data[key]
                lv = col[np.logical_not(col.apply(np.isnan))].tail(1).values[0]
                yr = col[np.logical_not(col.apply(np.isnan))].tail(1).index[0]
                col[col.index > yr] = lv
                data[key] = col.round()
            except TypeError:
                pass
            except AttributeError:
                pass
        data.index = data.index.values.astype(int)
        data.to_csv(f_name, index_label="year", mode = 'a')
        
def test ():
    """ Function doc """
    manley_data = CommunityData("../test_case/input_data/", 
                            "../test_case/baseline_results/config_used.yaml")
    
                            
    fc = Forecast(manley_data)

    return fc
