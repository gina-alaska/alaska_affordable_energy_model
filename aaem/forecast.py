"""
forecast.py
Ross Spicer
created: 2015/09/18

    forecast
"""
from community_data import CommunityData
from diagnostics import diagnostics

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
        self.forecast_generation()
        self.forecast_average_kW()
        self.forecast_households()

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
             
        
        
        end = self.fc_specs["population"].T.keys().values[-1] \
                if self.fc_specs["population"].T.keys().values[-1] < \
                self.yearly_kWh_totals.T.keys().values[-1] \
                else self.yearly_kWh_totals.T.keys().values[-1]
        
        population = self.fc_specs["population"].ix[start:end].T.values[0]
        consumption = self.yearly_kWh_totals[start:end].T.values[0]
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
        consumption["consumption kWh"] = consumption["population"] 
        del consumption["population"] 
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
        
        self.generation["kWh generation"] = self.generation["consumption kWh"]
        del(self.generation["consumption kWh"])
        
    def forecast_average_kW (self):
        """
        ???
        """
        self.average_kW = (self.consumption/ 8760.0)\
                                /(1-self.cd.get_item('community','line losses'))
        
        self.average_kW["avg. kW"] = self.average_kW["consumption kWh"]
        del(self.average_kW["consumption kWh"])
        
    def forecast_households (self):
        """
        forcast # of houselholds
        """
        peps_per_house = float(self.base_pop) / \
    self.cd.get_item('residential buildings','data').ix['total_occupied']
        self.households = np.round(self.population / np.float64(peps_per_house))
        self.households["HH"] = self.households["population"]
        del(self.households["population"])
        
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
        return self.population.ix[start-1:end-1].T.values[0]
    
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
        return self.consumption.ix[start-1:end-1].T.values[0]

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
        return self.generation.ix[start-1:end-1].T.values[0]

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
        return self.households.ix[start-1:end-1].T.values[0]
        
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
        try:
            r = self.res_HF
        except AttributeError:
            r = np.zeros(self.end_year - self.start_year)
            years = (self.end_year - np.arange(len(r)))[::-1]
            self.res_HF = DataFrame({'year': years,
                                   'consumption': r}).set_index('year')
        try:
            c = self.com_HF 
        except AttributeError:
            c = np.zeros(self.end_year - self.start_year)
            years = (self.end_year - np.arange(len(c)))[::-1]
            self.com_HF = DataFrame({'year': years,
                                   'consumption': c}).set_index('year')
        try:
            w = self.www_HF
        except AttributeError:
            w = np.zeros(self.end_year - self.start_year)
            #~ print self.end_year - 
            years = (self.end_year - np.arange(len(w)))[::-1]
            self.www_HF = DataFrame({'year': years,
                                   'consumption': w}).set_index('year')
        
        self.total_HF = self.res_HF + self.com_HF + self.www_HF
        
        self.res_HF["res HF"] = self.res_HF["consumption"]
        del(self.res_HF["consumption"])
        self.com_HF["com HF"] = self.com_HF["consumption"]
        del(self.com_HF["consumption"])
        self.www_HF["ww HF"] = self.www_HF["consumption"]
        del(self.www_HF["consumption"])
        self.total_HF["total HF"] = self.total_HF["consumption"]
        del(self.total_HF["consumption"])
        
    def save_forecast (self, path):
        """
        save the forecast to a csv
        pre:
            everything needs to be foretasted
        post:
            saves a file
        """
        df = concat([self.population.T, self.households.T, self.consumption.T,
                     self.generation.T, self.average_kW.T, self.res_HF.T,
                     self.com_HF.T, self.www_HF.T, self.total_HF.T]).T
        
        #~ return df
        #~ df = DataFrame( {"pop": self.population,
                     #~ "HH" : self.households,
                     #~ "kWh consumed" : self.consumption,
                     #~ "kWh generation": self.generation,
                     #~ "avg. kW": self.average_kW,
                     #~ "res HF": self.res_HF,
                     #~ "com HF": self.com_HF,
                     #~ "ww HF": self.www_HF,
                     #~ "total HF": self.total_HF,}, 
              #~ np.array(range(len(self.population))) + self.start_year)
        df.to_csv(path, index_label="year")
        
        

def test ():
    """ Function doc """
    manley_data = CommunityData("../data/", "../test_case/manley_data.yaml")
    
                            
    fc = Forecast(manley_data)
    #~ fc.calc_electricity_totals()

    return fc
