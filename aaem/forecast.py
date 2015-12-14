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
        
    def set_res_HF_fuel_forecast (self, fc, start_year):
        """
        set the residential HF consumption forecast
        
        pre: 
        """
        #~ start_pad = np.zeros(start_year - self.start_year)
        end_pad = np.zeros(self.end_year - (start_year + len(fc))+1) + fc[-1]
        self.res_HF = np.append(fc, end_pad)
        years = (self.end_year - np.arange(len(self.res_HF)))[::-1]
        self.res_HF = DataFrame({'year': years,
                                'consumption': self.res_HF}).set_index('year')
    
    def set_com_HF_fuel_forecast (self, fc, start_year):
        """
        set the residential HF consumption forecast
        
        pre: 
        """
        #~ start_pad = np.zeros(start_year - self.start_year)
        end_pad = np.zeros(self.end_year - (start_year + len(fc))+1) + fc[-1]
        self.com_HF = np.append(fc, end_pad)
        years = (self.end_year - np.arange(len(self.com_HF)))[::-1]
        self.com_HF = DataFrame({'year': years,
                                'consumption': self.com_HF}).set_index('year')
        
    def set_www_HF_fuel_forecast (self, fc, start_year):
        """
        set the residential HF consumption forecast
        
        pre: 
        """
        #~ start_pad = np.zeros(start_year - self.start_year)
        end_pad = np.zeros(self.end_year - (start_year + len(fc) )+1) + fc[-1]
        self.www_HF = np.append( fc, end_pad)
        years = (self.end_year - np.arange(len(self.www_HF)))[::-1]
        self.www_HF = DataFrame({'year': years,
                                'consumption': self.www_HF}).set_index('year')
        
    def calc_total_HF_forecast(self):
        """
        calculates the forecast totals
        """
        try:
            r = self.res_HF
        except AttributeError:
            r = np.zeros(self.end_year - self.start_year) + np.nan
            years = (self.end_year - np.arange(len(r)))[::-1]
            self.res_HF = DataFrame({'year': years,
                                   'consumption': r}).set_index('year')
        try:
            c = self.com_HF 
        except AttributeError:
            c = np.zeros(self.end_year - self.start_year) + np.nan
            years = (self.end_year - np.arange(len(c)))[::-1]
            self.com_HF = DataFrame({'year': years,
                                   'consumption': c}).set_index('year')
        try:
            w = self.www_HF
        except AttributeError:
            w = np.zeros(self.end_year - self.start_year) + np.nan 
            years = (self.end_year - np.arange(len(w)))[::-1]
            self.www_HF = DataFrame({'year': years,
                                   'consumption': w}).set_index('year')

        total = self.res_HF.fillna(0).values.T[0] + \
                        self.com_HF.fillna(0).values.T[0] + \
                        self.www_HF.fillna(0).values.T[0]

        if np.isnan(self.res_HF.values).all() and \
           np.isnan(self.com_HF.values).all() and \
           np.isnan(self.www_HF.values).all():
               total += np.nan
        
        years = years = (self.end_year - np.arange(len(total)))[::-1]
        self.total_HF = DataFrame({'year': years,
                            'total fuel consumption': total}).set_index('year')
        
    def save_forecast (self, path):
        """
        save the forecast to a csv
        pre:
            everything needs to be foretasted
        post:
            saves a file
        """
        
        # change col headers and change units
        res_gal = self.res_HF
        res_gal.columns = ["heating_fuel_residential_consumed [gallons/year]"]
        res_mmbtu = self.res_HF / constants.mmbtu_to_gal_HF
        res_mmbtu.columns = ["heating_fuel_residential_consumed [mmbtu/year]"]
        
        com_gal = self.com_HF
        com_gal.columns = \
                        ["heating_fuel_non-residential_consumed [gallons/year]"]
        com_mmbtu = self.com_HF / constants.mmbtu_to_gal_HF
        com_mmbtu.columns = \
                        ["heating_fuel_non-residential_consumed [mmbtu/year]"]
        
        ww_gal = self.www_HF
        ww_gal.columns = \
                       ["heating_fuel_water-wastewater_consumed [gallons/year]"]
        ww_mmbtu = self.www_HF / constants.mmbtu_to_gal_HF
        ww_mmbtu.columns = \
                       ["heating_fuel_water-wastewater_consumed [mmbtu/year]"]
        
        total_gal = self.total_HF
        total_gal.columns = ["heating_fuel_total_consumed [gallons/year]"]
        total_mmbtu = self.total_HF / constants.mmbtu_to_gal_HF
        total_mmbtu.columns = ["heating_fuel_total_consumed [mmbtu/year]"]
        
        kWh_con = self.consumption
        kWh_con.columns = ["total_electricity_consumed [kWh/year]"]
        self.c_map.columns = ["total_electricity_consumed_qualifier"]
        
        kWh_gen = self.generation
        kWh_gen.columns = ["total_electricity_generation [kWh/year]"]
        
        # make a data frames
        dfe = concat([self.population.round().astype(int), self.p_map, 
                      self.consumption.round(), self.c_map, 
                      self.generation.round()],axis=1)
                     
        dff = concat([self.population.round().astype(int), self.p_map,
                      res_gal.round(), res_mmbtu.round(),
                      com_gal.round(), com_mmbtu.round(),
                      ww_gal.round(), ww_mmbtu.round(),
                      total_gal.round(),
                      total_mmbtu.round()],axis=1)
        
        # fix the index
        dfe.index = dfe.index.values.astype(int)
        dff.index = dff.index.values.astype(int)
        #file names
        e_file = path + "electricity_forecast.csv"
        f_file = path + "heating_fuel_forecast.csv"
        
        # save e_file
        # add the file header
        fd = open(e_file ,"w")
        fd.write("# Electricity Forecast for " + \
                                    self.cd.get_item("community","name") + "\n")
        fd.write("# Qualifier info: \n")
        fd.write("#   M indicates a measured value \n")
        fd.write("#   P indicates a projected value \n")
        fd.close()
        
        # save
        dfe.to_csv(e_file, index_label="year",mode = "a")
        
        # save f_file
        # add the file header
        fd = open(f_file ,"w")
        fd.write("# Heating Fuel Forecast for " + \
                                    self.cd.get_item("community","name") + "\n")
        fd.write("# Qualifier info: \n")
        fd.write("#   M indicates a measured value \n")
        fd.write("#   P indicates a projected value \n")
        fd.close()
        
        # save
        dff.to_csv(f_file, index_label="year",mode = "a")
        

def test ():
    """ Function doc """
    manley_data = CommunityData("../test_case/input_data/", 
                            "../test_case/baseline_results/config_used.yaml")
    
                            
    fc = Forecast(manley_data)
    fc.calc_total_HF_forecast()

    return fc
