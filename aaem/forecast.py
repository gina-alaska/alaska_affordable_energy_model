"""
forecast.py
Ross Spicer
created: 2015/09/18

    forecast
"""
from community_data import CommunityData
from diagnostics import Diagnostics
import constants
import plot
import colors

import numpy as np
from pandas import DataFrame, read_csv, concat
import os.path
import copy

from datetime import datetime

class Forecast (object):
    """ Class doc """
    
    def __init__ (self, community_data, diag = None, 
                        scalers = {'kWh consumption':1.0}):
        """
        pre:
            self.cd is a community_data instance. 
        post:
            self.start_year < self.end_year are years(ints) 
            self.cd is a community_data instance. 
        """
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = Diagnostics()
        self.cd = community_data
        
        self.forecast_population()
        
        #~ ## test block
        #~ self.forecast_consumption(scalers['kWh consumption'])
        #~ self.forecast_generation()
        #~ return
        
        if self.cd.get_item("community","model electricity") is False:
            pass
        else:

            self.forecast_consumption(scalers['kWh consumption'])
            self.forecast_generation()
  
            self.forecast_average_kW()
        
        self.calc_average_diesel_load()
        
        self.cpi = DataFrame( [
            1, 0.9765625, 0.953674316, 0.931322575, 0.909494702, 0.88817842, 
            0.867361738, 0.847032947, 0.827180613, 0.807793567, 0.788860905, 
            0.770371978, 0.752316385, 0.734683969, 0.717464814, 0.700649232,
            0.684227766, 0.668191178, 0.652530447, 0.637236765, 0.622301528,
            0.607716336, 0.593472984, 0.579563461, 0.565979942, 0.552714788,
            0.539760535, 0.527109897, 0.514755759, 0.502691171, 0.490909347,
            0.479403659, 0.468167636, 0.457194957, 0.44647945, 0.436015088,
            0.425795984, 0.415816391, 0.406070694, 0.396553412, 0.387259192, 
            0.378182804, 0.369319145, 0.360663227, 0.352210183, 0.343955257,
            0.335893805, 0.328021294, 0.320333295, 0.312825484, 0.305493636, 
            0.298333629, 0.291341435, 0.28451312, 0.277844844, 0.271332855, 
            0.264973491, 0.258763175, 0.252698413, 0.246775794, 0.240991987],
            index = [
            2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024,
            2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033,
            2034, 2035, 2036, 2037, 2038, 2039, 2040, 2041, 2042, 
            2043, 2044, 2045, 2046, 2047, 2048, 2049, 2050, 2051, 
            2052, 2053, 2054, 2055, 2056, 2057, 2058, 2059, 2060, 2061, 
            2062, 2063, 2064, 2065, 2066, 2067, 2068, 2069, 2070, 2071, 2072, 
            2073, 2074, 2075]
        )
        #~ last_cpi_year = self.cpi.index.tolist()[-1]
        #~ if self.end_year < last_cpi_year:
            #~ self.cpi = self.cpi[:self.end_year]
        #~ elif self.end_year > last_cpi_year:
            #~ self.diagnostics.add_note("Forecast",
                    #~ "extending cpi past avaiable data")
            #~ last_cpi = float(self.cpi.ix[last_cpi_year])
            #~ for i in range(last_cpi_year,self.end_year+1):
                #~ self.cpi.ix[i] = last_cpi

        #~ self.forecast_households()
        self.heat_demand_cols = []
        self.heating_fuel_cols = [] 
        self.electric_columns = []
        

    #~ def calc_electricity_values (self):
        #~ """ 
        #~ pre:
            #~ 'fc_electricity_used' should contain the kWh used for each key type
        #~ post:
            #~ self.electricty_totals is a array of yearly values of total kWh used
        #~ """
        #~ kWh = self.fc_specs["electricity"]
        #~ print kWh
        #~ years = kWh.T.keys().values
        #~ self.yearly_res_kWh = DataFrame({"year":years,
                          #~ "total":kWh['consumption residential'].values}).set_index("year")
        #~ self.yearly_total_kWh = DataFrame({"year":years,
                          #~ "total":kWh['consumption'].values}).set_index("year")
        #~ self.average_nr_kWh = kWh['consumption non-residential'].values[-3:].mean()
        #~ if np.isnan(self.average_nr_kWh):
            #~ temp = kWh['consumption non-residential']
            #~ self.average_nr_kWh = temp[ np.logical_not(np.isnan(temp))].mean() 
        #~ self.yearly_nr_kWh = DataFrame({"year":years,
                          #~ "total":kWh['consumption non-residential'].values}).set_index("year")
        #~ print self.average_nr_kWh


    def forecast_population (self):
        """
        pre:
            tbd.
        post:
            self.population is a array of estimated populations for each 
        year between start and end
        """
        # pop forecast is preprocessed now
        population = self.cd.get_item('community',"population")
        
        self.p_map = DataFrame(population["population_qualifier"])
        self.population = DataFrame(population["population"])
        
        #~ last_pop_year = self.population.index.tolist()[-1]
        #~ if self.end_year < last_pop_year:
            #~ self.population = self.population[:self.end_year]
        #~ elif self.end_year > last_pop_year:
            #~ self.diagnostics.add_note("Forecast",
                    #~ "extending popultation past avaiable data")
            #~ last_pop = int(round(self.population.ix[last_pop_year]))
            #~ for i in range(last_pop_year,self.end_year+1):
                #~ self.population.ix[i] = last_pop
        
        if len(self.p_map[self.p_map == "M"] ) < 10:
            msg = "the data range is < 10 for input population "\
                  "check population.csv in the models data directory"
            self.diagnostics.add_warning("forecast", msg)
        
        
    def forecast_consumption (self, consumption_scaler = 1.0):
        """
        pre:
            tbd.
        post:
            self.consumption is a array of estimated kWh consumption for each 
        year between start and end
        """
        total_consumption = \
            self.cd.get_item('community','utility info')['consumption'] \
            * consumption_scaler
        residential_consumption = \
            self.cd.get_item('community','utility info')\
            ['consumption residential'] * consumption_scaler
        non_residential_consumption = \
            self.cd.get_item('community','utility info')\
            ['consumption non-residential'] * consumption_scaler
        
        index = list(residential_consumption.index)

        if len(residential_consumption) < 10:
            msg = "the data range is < 10 for input consumption "\
                  "check electricity.csv in the models data directory"
            self.diagnostics.add_warning("Forecast: consumption", msg)
        
        population = self.population.ix[index]
        if any(population.isnull()):
            v= population.isnull().values.T.tolist()[0]
            for year in population[v].index.values.tolist():
                index.remove(year)
        
        if any(residential_consumption.isnull()):
            to_remove = \
                residential_consumption[residential_consumption.isnull()].index
            for year in to_remove:
                #~ print year
                index.remove(year)
        
        self.diagnostics.add_note("forecast", 
           "years with measured consumption and population " + str(index) +\
        ". List used to generate fit function")
        population = self.population.ix[index]['population'].values
        
        #~ self.measured_consumption = self.yearly_total_kWh.ix[idx] 
        consumption = residential_consumption.ix[index].values

        if len(population) < 10:
            self.diagnostics.add_warning("forecast", 
                  "the data range is < 10 matching years for "\
                  "population and consumption "\
                  "check population.csv and electricity.csv "\
                  "in the models data directory")

        try:
            #~ print population,consumption
            m, b = np.polyfit(population,consumption,1) 
        except TypeError:
            raise RuntimeError, "Known population & consumption do not overlap"

        forcasted_consumption = (m * self.population + b) #+ self.average_nr_kWh
        forcasted_consumption.columns = ['consumption residential']
        
        forcasted_consumption['consumption_qualifer'] = "P"
        
        forcasted_consumption['consumption residential']\
            [residential_consumption.ix[index].index] = \
            residential_consumption.ix[index]
            
        if consumption_scaler != 1.0:
            ## if the scaler is not 1 then none of the values are really
            ## measured
            forcasted_consumption['consumption_qualifer']\
                [residential_consumption.index] = \
                (residential_consumption * np.nan).fillna("M")
        
        
        mean_non_res_con = non_residential_consumption.values[-3:].mean()
        print non_residential_consumption.values
        print mean_non_res_con
        
        forcasted_consumption['consumption non-residential'] = mean_non_res_con
        forcasted_consumption['consumption non-residential']\
            [non_residential_consumption.ix[index].index] = \
            non_residential_consumption.ix[index]
            
        
        forcasted_consumption['consumption'] = \
            forcasted_consumption['consumption non-residential'] + \
            forcasted_consumption['consumption residential'] 
            
        forcasted_consumption['consumption non-residential']\
            [total_consumption.ix[index].index] = total_consumption.ix[index]
           
        ## don't forecast backwards 
        forcasted_consumption = \
            forcasted_consumption.ix[residential_consumption.index[0]:]
        self.consumption = forcasted_consumption
        
    def forecast_generation (self):
        """
        forecast generation
        pre:
            tbd.
            self.consumption should be a float array of kWh/yr values
        post:
            self.generation is a array of estimated kWh generation for each 
        year between start and end
        """
        measured_generation = \
            self.cd.get_item('community','utility info')['net generation']
        generation = self.consumption['consumption']/\
                    (1.0-self.cd.get_item('community','line losses')/100.0)
        generation = DataFrame(generation)
        generation.columns = ['generation']
        generation = generation.round(-3)
        
        
        index = set(measured_generation.index) & set(generation.index)
        
        generation['generation'][index] = measured_generation.ix[index]
        
        types = [u'generation diesel', u'generation hydro',
                u'generation natural gas', u'generation wind',
                u'generation solar', u'generation biomass'
            ]
        generation_types = self.cd.get_item('community','utility info')[types]
        
        backup_type = 'generation diesel'
        if (generation_types[['generation natural gas']].fillna(0)\
            != 0).any().bool():
            backup_type = 'generation natural gas'
        
        ## forecast each type
        for fuel in types:
            current_fuel = generation_types[fuel]
            #~ print current_rfuel
            name = fuel.replace('generation ','')
            ## get the hypothetical limit
            try:
                current_generation = self.cd.get_item('community',
                    name + ' generation limit')
            except KeyError:
                current_generation = 0
            ## is there a non-zero limit defined 
            if current_generation != 0:
                
                if fuel == 'generation wind':
                    measured = \
                        current_fuel[current_fuel.notnull()].values[-3:].mean()
                    max_wind_percent = .2
                    if measured > (current_generation * max_wind_percent):
                        pass
                    else:
                        generation[fuel] = current_generation * max_wind_percent
                        generation[fuel].ix[index] = current_fuel.ix[index]
                        continue
                else:
                    generation[fuel] = current_generation 
                    generation[fuel].ix[index] = current_fuel.ix[index] 
                    continue
            else:
                current_generation = \
                    current_fuel[current_fuel.notnull()].values[-3:].mean()
                    
        

            ## no generation found
            if current_generation == 0:
                generation[fuel] = current_generation
                continue 
            
            if fuel in [ u'generation wind', u'generation hydro' ]:
                generation[fuel] = current_generation
                generation[fuel].ix[index] = current_fuel.ix[index] 
                for i in generation[fuel].ix[current_fuel.index[-1]+1:].index:
                     generation[fuel].ix[i] = \
                        generation[fuel].ix[i-3:i-1].mean()
            else:
                generation[fuel] = current_generation
                generation[fuel].ix[index] = current_fuel.ix[index]
            
                
         
            #~ print fuel, current_generation
        #~ print generation['generation hydro']
        ## scale back any excess
        for fuel in ['generation wind','generation hydro','generation biomass']:
            current_fuel = generation_types[fuel]
            fuel_sums = generation[types].sum(1) 
            #~ print fuel_sums
            if any(generation['generation'] < fuel_sums):
                #~ print 'a'
                if any(generation['generation'] < generation[fuel]):
                    #~ print 'b'
                    msg = "scaling generation(" + fuel + ") where geneation(" + \
                            fuel + ") > total generation"
                    self.diagnostics.add_note('forecast', msg)   
                            
                    generation[fuel] = generation[fuel] -\
                            (fuel_sums - generation['generation'])
                    
                    generation[fuel][generation[fuel] < 0 ] = 0
                    
                    generation[fuel].ix[index] = current_fuel.ix[index] 
        
        corrected_backup_type = generation['generation'] - \
            (generation[types].sum(1) - generation[backup_type])
        #~ print corrected_backup_type
        corrected_backup_type[corrected_backup_type < 0] = 0 
        
        generation[backup_type ] = corrected_backup_type
        generation[backup_type].ix[index] = generation_types[backup_type].ix[index] 
              
        
        self.generation = generation

        
    def forecast_average_kW (self):
        """
        forecast the average kW used per community per year
        pre:
        post:
        """
        self.average_kW = (self.consumption['consumption']/ 8760.0)\
                                /(1-self.cd.get_item('community','line losses'))
        
        self.average_kW.columns = ["average load"]
        
    def forecast_households (self):
        """
        forcast # of houselholds
        pre:
        post:
        """
        peeps_per_house = float(self.base_pop) / \
            self.cd.get_item('Residential Buildings',
                'data').ix['total_occupied']
        self.households = \
            np.round(self.population / np.float64(peeps_per_house))
        self.households.columns = ["households"] 
        
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
       
        ## dynamic extension
        existing_len = len(self.population.ix[start:end])
        extend_by = (end + 1) - start - existing_len
        if extend_by > 0:
            extend = DataFrame(
                index=range(
                    self.population.index[-1] + 1,
                    self.population.index[-1] + 1+extend_by
                ), 
                columns=['population'])
            extend['population'] = self.population.iloc[-1]['population']
            population = self.population.ix[start:end].append(extend)
        
        else:
            # -1 to ensure same behavour
            population = self.population.ix[start:end]
        return population['population'].values  
    
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
            return self.consumption.ix[start]['consumption']
       
        ## dynamic extension
        existing_len = len(self.consumption.ix[start:end])
        extend_by = (end + 1) - start - existing_len
        if extend_by > 0:
            extend = DataFrame(
                index=range(
                    self.consumption.index[-1] +1,
                    self.consumption.index[-1]+extend_by+1
                ), 
                columns=['consumption'])
            extend['consumption'] = self.consumption.iloc[-1]['consumption']
            consumption = \
                DataFrame(self.consumption.ix[start:end]['consumption']).\
                append(extend)
        
        else:
            #  -1 to ensure same behavour
            consumption = \
                DataFrame(self.consumption['consumption'].ix[start:end])
        return consumption['consumption'].values  

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
            return self.generation.ix[start]['generation']
       
        ## dynamic extension
        existing_len = len(self.generation.ix[start:end])
        extend_by = (end + 1) - start - existing_len
        if extend_by > 0:
            extend = DataFrame(
                index=range(
                    self.generation.index[-1] + 1 ,
                    self.generation.index[-1]+extend_by +1
                ), 
                columns=['generation'])
            extend['generation'] = self.generation.iloc[-1]['generation']
            generation = \
                DataFrame(self.generation.ix[start:end]['generation']).\
                append(extend)
        
        else:
            generation = \
                DataFrame(self.generation['generation'].ix[start:end])
        return generation['generation'].values  

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
       
        ## dynamic extension
        existing_len = len(self.households.ix[start:end])
        extend_by = (end + 1) - start - existing_len
        if extend_by > 0:
            extend = DataFrame(
                index=range(
                    self.households.index[-1] + 1,
                    self.households.index[-1]+extend_by +1
                ), 
                columns=['households'])
            extend['households'] = self.households.iloc[-1]['households']
            households = self.households.ix[start:end].append(extend)
        
        else:
            # -1 to ensure same behavour
            households = self.households.ix[start:end]
        return households['households'].values  
        
    def save_forecast (self, path, png_path = None, do_plots = False):
        """
        save the forecast to a csv
        pre:
            everything needs to be foretasted
            path: path to each communities output dir
            png_path: altenat location for pngs
        post:
            saves 3 files
        """
        tag = self.cd.get_item("community", "name").replace(" ", "_") + "_"
        pathrt = os.path.join(path, tag)
        if png_path is None:
            if do_plots:
                os.makedirs(os.path.join(path,"images"))
            png_path = os.path.join(path, 'images',tag)
            epng_path = png_path
            hdpng_path = png_path
            hfpng_path = png_path;
            gpng_path = png_path
        else:
            epng_path = os.path.join(png_path,'electric_forecast',tag)
            try:
                if do_plots:
                    os.makedirs(os.path.join(png_path,'electric_forecast'))
            except OSError:
                pass
            gpng_path = os.path.join(png_path,'generation_forecast',tag)
            try:
                if do_plots:
                    os.makedirs(os.path.join(png_path,'generation_forecast'))
            except OSError:
                pass
            hdpng_path = os.path.join(png_path,'heat_demand_forecast',tag)
            try:
                if do_plots:
                    os.makedirs(os.path.join(png_path,'heat_demand_forecast'))
            except OSError:
                pass
            hfpng_path = os.path.join(png_path,'heating_fuel_forecast',tag)
            try:
                if do_plots:
                    os.makedirs(os.path.join(png_path,'heating_fuel_forecast'))
            except OSError:
                pass
        if self.cd.intertie != 'child' and \
            self.cd.get_item("community","model electricity"):

            #~ start = datetime.now() 
            self.save_electric(pathrt, epng_path, do_plots)
            self.save_generation_forecast(pathrt, gpng_path, do_plots)
            #~ print "saving electric:" + str(datetime.now() - start)
        if self.cd.intertie != 'parent' and \
            self.cd.get_item("community","model heating fuel"):
     
            #~ start = datetime.now() 
            self.save_heat_demand(pathrt, hdpng_path, do_plots)
            #~ print "saving heat demand:" + str(datetime.now() - start)
            
            #~ start = datetime.now() 
            self.save_heating_fuel(pathrt, hfpng_path, do_plots)
            #~ print "saving heating fuel:" + str( datetime.now() - start)
    
    def add_heat_demand_column (self, key, year_col, data_col):
        """ 
        add a column to be saved with the heat demand forecast 
        pre:
            Key is a string. year_col is a numpy array of values, date_col
        is a corresponding array of years
        post:
            a dataframe is added to self.heat_demand_cols
        """
        self.heat_demand_cols.append(DataFrame({"year":year_col, 
                                           key:data_col}).set_index("year"))
                                           
    def add_heating_fuel_column (self, key, year_col, data_col):
        """
        add a column to be saved with the heating fuel forecast 
        pre:
            Key is a string. year_col is a numpy array of values, date_col
        is a corresponding array of years
        post:
            a dataframe is added to self.heating_fuel_cols
        """
        self.heating_fuel_cols.append(DataFrame({"year":year_col, 
                                           key:data_col}).set_index("year"))
    
    
    def generate_electric_output_dataframe (self):
        """
        """
        from copy import deepcopy
        kWh_con = deepcopy(self.consumption)
        kWh_con.columns = ["total_electricity_consumed [kWh/year]",
                           'residential_electricity_consumed [kWh/year]',
                           'non-residential_electricity_consumed [kWh/year]']
        c_map = copy.deepcopy(self.c_map)
        c_map.columns = ["total_electricity_consumed_qualifier"]
        
        kWh_gen = self.generation
        kWh_gen.columns = ["total_electricity_generation [kWh/year]"]
        g_map = copy.deepcopy(c_map)
        g_map.columns = ["total_electricity_generation_qualifier"]
    
        #~ community = copy.deepcopy(self.c_map)
        community = copy.deepcopy(self.c_map)
        community.columns = ["community"]
        community.ix[:] = self.cd.get_item("community","name")
        try:
            self.electric_dataframe = \
                    concat([community,self.population.round().astype(int), 
                           self.p_map, kWh_con.round().astype(int), c_map, 
                           kWh_gen.round().astype(int), g_map] ,axis=1)
        except ValueError:
            self.electric_dataframe = None

    
    
    def save_electric (self, csv_path, png_path, do_plots):
        """ 
        save the electric forecast
        
        pre:
            self.population, consumption, and generation. should be dataframes 
        as calculated in this class. path should be the path to the output 
        directory.
        post:
            a file, electricity_forecast.csv, is save in the output directory.
        """
        self.generate_electric_output_dataframe()
        self.save_electric_csv(csv_path)
        if do_plots:
            self.save_electric_png(png_path)
        


    def save_electric_csv (self, path):
        """ 
        save the electric forecast
        
        pre:
            self.population, consumption, and generation. should be dataframes 
        as calculated in this class. path should be the path to the output 
        directory.
        post:
            a file, electricity_forecast.csv, is save in the output directory.
        """

        if self.electric_dataframe is None:
            self.diagnostics.add_warning("Forecast", 
                                ("when saving null values were found in "
                                 "generation/consumption data. Electricity "
                                 "forecast is suspect not saving summary(csv)"))
            return
        data = self.electric_dataframe
        #not joining path adding file name
        f_name = path + "electricity_forecast.csv" 
        
        fd = open(f_name ,"w")
        fd.write("# Electricity Forecast for " + \
                                    self.cd.get_item("community","name") + "\n")
        fd.write("# Qualifier info: \n")
        fd.write("#   M indicates a measured value \n")
        fd.write("#   P indicates a projected value \n")
        fd.write("#   I indicates a value carried over from the input data. May be projected or measured see input data metadata.\n")
        
        fd.close()
            
        data.index = data.index.values.astype(int)
        data.to_csv(f_name, index_label="year", mode = 'a')
    
    def save_electric_png (self, path):
        """ Function doc """
        if self.electric_dataframe is None:
            self.diagnostics.add_warning("Forecast", 
                                ("when saving null values were found in "
                                 "generation/consumption data. Electricity "
                                 "forecast is suspect not saving summary(png)"))
            return
            
        path = path+ "electricity_forecast.png"
        start = self.c_map[self.c_map['consumption_qualifier'] == 'P'].index[0]
        df2 = self.electric_dataframe[['population',
                            'total_electricity_consumed [kWh/year]',
                            'total_electricity_generation [kWh/year]',
                            'residential_electricity_consumed [kWh/year]',
                            'non-residential_electricity_consumed [kWh/year]']]
        name = self.cd.get_item("community","name") + ' Electricity Forecast'
        
        fig, ax = plot.setup_fig(name ,'years','population')
        ax1 = plot.add_yaxis(fig,'kWh')
        
        c_dict = {'population': [min(1,r*4) for r in colors.red],
                   'total_electricity_consumed [kWh/year]':colors.orange,
                    'total_electricity_generation [kWh/year]':colors.green,
                     'residential_electricity_consumed [kWh/year]':colors.yellow,
                    'non-residential_electricity_consumed [kWh/year]':colors.violet
        }
        
        plot.plot_dataframe(ax1,df2,ax,['population'],
                    {'population':'population',
                    'total_electricity_consumed [kWh/year]':'consumption',
                    'total_electricity_generation [kWh/year]':'generation',
                    'residential_electricity_consumed [kWh/year]':'residential consumption',
                    'non-residential_electricity_consumed [kWh/year]':'non residential consumption'},
                    c_dict)
        fig.subplots_adjust(right=.85)
        fig.subplots_adjust(left=.12)
        plot.add_vertical_line(ax,start, 'forecasting starts' )
        plot.add_horizontal_line(ax1,0)
    
    
        plot.create_legend(fig,.20)
        plot.save(fig,path)
        plot.clear(fig)
        
    def generate_generation_forecast_dataframe(self):
        """
        """
        data = copy.deepcopy(self.generation_by_type)
        g_map = copy.deepcopy(self.c_map)
        g_map.columns = ["generation_qualifier"]
        
        
        order = []
        try:
            for col in ['generation total', 'generation diesel', 
                        'generation hydro', 
                        'generation natural gas', 'generation wind', 
                        'generation solar', 'generation biomass']:
                #~ print data[col].ix[self.start_year:]
                if col == 'generation total' and \
                    any(np.isnan(data[col].ix[self.start_year:])):
                    raise ValueError, "nans found"
                
                kWh = col.replace(" ", "_") + " [kWh/year]"
                mmbtu = col.replace(" ", "_") + " [mmbtu/year]"
                data[kWh] = data[col].fillna(0).round().astype(int)
                data[mmbtu] = (data[col] / constants.mmbtu_to_kWh)\
                                                .fillna(0).round().astype(int)
                del data[col]
                order += [kWh, mmbtu]
            data = concat([self.population.round().astype(int),
                           self.p_map,g_map,data],axis=1) 
            data["community"] = self.cd.get_item("community","name")
                    
            self.generation_forecast_dataframe = \
                            data[[data.columns[-1]] + data.columns[:-1].tolist()]
            del data
        except ValueError:
            self.generation_forecast_dataframe = None
        
    def save_generation_forecast (self, csv_path, png_path, do_plots):
        
        self.generate_generation_forecast_dataframe()
        
        if self.generation_forecast_dataframe is None:
            self.diagnostics.add_warning("Forecast", 
                        ("when saving null values were found in "
                         "generation data. generation generation "
                         "forecast is suspect not saving summary(csv and png)"))
        else:
            self.save_generation_forecast_csv(csv_path)
            if do_plots:
                self.save_generation_forecast_png(png_path)
        
    def save_generation_forecast_csv (self, path):
        """
        """
        out_file = path + "generation_forecast.csv"
        fd = open(out_file, 'w')
        fd.write("# Generation forecast\n")
        fd.write(("# The column 'generation_qualifier' applies to all "
                                "of the following generation columns"))
        fd.write("# Qualifier info: \n")
        fd.write("#   M indicates a measured value \n")
        fd.write("#   P indicates a projected value \n")
        fd.write("#   I indicates a value carried over from the input data. May be projected or measured see input data metadata.\n")
        fd.close()
        self.generation_forecast_dataframe.to_csv(out_file, 
                                        index_label="year", mode = 'a')  
                                        
    def save_generation_forecast_png (self, path):
        """ Function doc """
            
        path = path + "generation_forecast.png"
        
        png_list = ['population',
        'generation_total [kWh/year]',
        'generation_diesel [kWh/year]',
        'generation_hydro [kWh/year]',
        'generation_natural_gas [kWh/year]',
        'generation_wind [kWh/year]',
        'generation_solar [kWh/year]',
        'generation_biomass [kWh/year]']
        
        
        
        png_dict = {'population':'population',
        'generation_total [kWh/year]':'total',
        'generation_diesel [kWh/year]':'diesel',
        'generation_hydro [kWh/year]':'hydro',
        'generation_natural_gas [kWh/year]':'natural gas',
        'generation_wind [kWh/year]':'wind',
        'generation_solar [kWh/year]':'solar',
        'generation_biomass [kWh/year]':'biomass'}
        
    
        c_dict = {'population': [min(1,r*4) for r in colors.red],
        'generation_total [kWh/year]':colors.jet,
        'generation_diesel [kWh/year]':colors.red,
        'generation_hydro [kWh/year]':colors.blue,
        'generation_natural_gas [kWh/year]':colors.violet,
        'generation_wind [kWh/year]':[ min(1,r*2) for r in colors.blue],
        'generation_solar [kWh/year]':colors.orange,
        'generation_biomass [kWh/year]':colors.avacado}
        
        temp = []
        for i in png_list:
            if  all(self.generation_forecast_dataframe[i].fillna(0) == 0):
                continue
            temp.append(i)
        png_list = temp
        if len(png_list) == 3:
            png_list = list(set(png_list).\
                    difference(['generation_total [kWh/year]']))
        
        df2 = self.generation_forecast_dataframe[png_list]
        plot_name = self.cd.get_item("community","name") +' Generation Forecast'
        
        fig, ax = plot.setup_fig(plot_name ,'years','population')
        ax1 = plot.add_yaxis(fig,'Generation kWh')
        
        plot.plot_dataframe(ax1,df2,ax,['population'],png_dict,c_dict)
        fig.subplots_adjust(right=.85)
        fig.subplots_adjust(left=.12)
        start = self.c_map[self.c_map['consumption_qualifier'] == 'P'].index[0]
        plot.add_vertical_line(ax,start, 'forecasting starts' )
        plot.add_horizontal_line(ax1,0)
        plot.create_legend(fig,.20)

        plot.save(fig,path)
        plot.clear(fig)
        
    
    def generate_heat_demand_dataframe (self):
        """
        """
        data = concat([self.population.round().astype(int), self.p_map] + \
                                                self.heat_demand_cols,axis=1) 
    
        for key in data.keys():
            try:
                col = data[key]
                idx = np.logical_not(col.apply(np.isnan))
                lv = col[idx].tail(1).values[0]
                yr = col[idx].tail(1).index[0]
                col[col.index > yr] = lv
                data[key] = col.round()
            except (TypeError, IndexError, AttributeError):
                pass
            
        idx = data.keys()[['mmbtu' in s for s in data.keys()]]
    
        data["heat_energy_demand_total [mmbtu/year]"] = data[idx].sum(1).round()
        data["community"] = self.cd.get_item("community","name")
                
        self.heat_demand_dataframe = data[[data.columns[-1]] + data.columns[:-1].tolist()]
        del data
        
    def save_heat_demand (self,csv_path, png_path, do_plots):
        """ Function doc """
        self.generate_heat_demand_dataframe()
        self.save_heat_demand_csv(csv_path)
        if do_plots:
            self.save_heat_demand_png(png_path)
    
    def save_heat_demand_csv (self, path):
        """
        save the heat demand forecast
        
        pre:
            self.population should be a dataframe. self.heat_demad_cols should 
        be populated using add_heat_demad_column. path should be the path to the
        output directory.
        post:
            a file, heat_demand_forecast.csv, is save in the output directory.
        """
        f_name = path + "heat_demand_forecast.csv"
        data =  self.heat_demand_dataframe      
        fd = open(f_name ,"w")
        fd.write("# Heat Demand Forecast for " + \
                                    self.cd.get_item("community","name") + "\n")
        fd.write("# Qualifier info: \n")
        fd.write("#   M indicates a measured value \n")
        fd.write("#   P indicates a projected value \n")
        fd.write("#   I indicates a value carried over from the input data. May be projected or measured see input data metadata.\n")
        fd.close()
        
        data.index = data.index.values.astype(int)
        data.to_csv(f_name, index_label="year", mode = 'a')
        
    def save_heat_demand_png(self,path):
        """
        """
        path = path+ "heat_demand_forecast.png"
        #~ start = self.c_map[self.c_map['consumption_qualifier'] == 'P'].index[0]
        
        cols = ['population']
        for col in self.heat_demand_dataframe.columns:
            if "[mmbtu/year]" in col:
                cols += [col]
                
        df2 = self.heat_demand_dataframe[cols]
        name = self.cd.get_item("community","name") + ' Heat Demand Forecast'
        
        fig, ax = plot.setup_fig(name ,'years','population')
        ax1 = plot.add_yaxis(fig,'Heat Demand MMBtu')
        
        c_dict = {'population': [min(1,r*4) for r in colors.red],
        'heat_energy_demand_residential [mmbtu/year]':colors.yellow,
        'heat_energy_demand_water-wastewater [mmbtu/year]':colors.cobalt,
        'heat_energy_demand_non-residential [mmbtu/year]':colors.green,
                        'heat_energy_demand_total [mmbtu/year]':colors.jet}
        
        plot.plot_dataframe(ax1,df2,ax,['population'],
            {'population':'population',
        'heat_energy_demand_residential [mmbtu/year]':'residential',
        'heat_energy_demand_water-wastewater [mmbtu/year]':'water & wastewater',
        'heat_energy_demand_non-residential [mmbtu/year]':'non-residential',
                        'heat_energy_demand_total [mmbtu/year]':'total'},
                        c_dict)
        fig.subplots_adjust(right=.85)
        fig.subplots_adjust(left=.12)
        #~ plot.add_vertical_line(ax,start, 'forecasting starts' )
        plot.add_horizontal_line(ax1,0)
    
        plot.create_legend(fig,.2)
        plot.save(fig,path)
        plot.clear(fig)
    
    def generate_heating_fuel_dataframe(self):
        """ """
        data = concat([self.population.round().astype(int), self.p_map] + \
                                                self.heating_fuel_cols, axis=1)

        for key in data.keys():
            try:
                col = data[key]
                idx = np.logical_not(col.apply(np.isnan))
                lv = col[idx].tail(1).values[0]
                yr = col[idx].tail(1).index[0]
                col[col.index > yr] = lv
                data[key] = col.round()
            except (TypeError,IndexError, AttributeError):
                pass

        hf_gal_idx = data.keys()[['gallons' in s for s in data.keys()]]
        hf_gal_idx =  hf_gal_idx[['heating_fuel' in s for s in hf_gal_idx]]
        
        hf_btu_idx = data.keys()[['mmbtu' in s for s in data.keys()]]
        hf_btu_idx =  hf_btu_idx[['heating_fuel' in s for s in hf_btu_idx]]
        
        
        data["heating_fuel_total_consumed [gallons/year]"] = \
                                        data[hf_gal_idx].sum(1).round()
        data["heating_fuel_total_consumed [mmbtu/year]"]= \
                                        data[hf_btu_idx].sum(1).round()
        data["community"] = self.cd.get_item("community","name")


        self.heating_fuel_dataframe = \
                        data[[data.columns[-1]] + data.columns[:-1].tolist()]
        del data
    
    def save_heating_fuel(self, csv_path, png_path, do_plots):
        """ """
        #~ start = datetime.now() 
        self.generate_heating_fuel_dataframe()
        #~ print "saving heating fuel *1:" + str( datetime.now() - start)
        #~ start = datetime.now() 
        self.save_heating_fuel_csv(csv_path)
        #~ print "saving heating fuel *2:" + str( datetime.now() - start)
        #~ start = datetime.now() 
        if do_plots:
            self.save_heating_fuel_png(png_path)
        #~ print "saving heating fuel *3:" + str( datetime.now() - start)
    
    def save_heating_fuel_csv (self, path):
        """
        save the heating fuel 
        
        pre:
            self.population should be a dataframe. self.heat_demad_cols should 
        be populated using add_heating_fuel_column. path should be the path to 
        the output directory. 
        post:
            a file, heating_fuel_forecast.csv, is save in the output directory.
        """
        f_name = path + "heating_fuel_forecast.csv"
        data = self.heating_fuel_dataframe
        
        fd = open(f_name ,"w")
        fd.write("# Heating Fuel Forecast for " + \
                                    self.cd.get_item("community","name") + "\n")
        fd.write("# Qualifier info: \n")
        fd.write("#   M indicates a measured value \n")
        fd.write("#   P indicates a projected value \n")
        fd.write("#   I indicates a value carried over from the input data. May be projected or measured see input data metadata.\n")
        fd.close()

        data.index = data.index.values.astype(int)
        data.to_csv(f_name, index_label="year", mode = 'a')
        
    def save_heating_fuel_png (self, path):
        """"""
        path = path+ "heating_fuel_forecast.png"
        #~ start = self.c_map[self.c_map['consumption_qualifier'] == 'P'].index[0]
        
        cols = ['population']
        for col in self.heating_fuel_dataframe.columns:
            if "[mmbtu/year]" in col:
                cols += [col]
        
        df2 = self.heating_fuel_dataframe[cols]

        name = self.cd.get_item("community","name") + ' Heating fuel Forecast'
        
        fig, ax = plot.setup_fig(name ,'years','population')
        ax1 = plot.add_yaxis(fig,'Heating fuel MMBtu')
        
        c_dict = {'population': [min(1,r*4) for r in colors.red],
            "heating_fuel_residential_consumed [mmbtu/year]":
                    colors.red,
            "cords_wood_residential_consumed [mmbtu/year]":
                    colors.avacado,
            "gas_residential_consumed [mmbtu/year]":
                    colors.violet,
            "electric_residential_consumed [mmbtu/year]":
                    colors.goldenrod,
            "propane_residential_consumed [mmbtu/year]":
                    colors.orange,
            "heating_fuel_water-wastewater_consumed [mmbtu/year]":
                    colors.cobalt,
            "heating_fuel_non-residential_consumed [mmbtu/year]":
                    colors.green,
            "heating_fuel_total_consumed [mmbtu/year]":colors.jet,}
        
        plot.plot_dataframe(ax1,df2,ax,['population'],
            {"population":'population',
            "heating_fuel_residential_consumed [mmbtu/year]":
                    'heating oil - residential',
            "cords_wood_residential_consumed [mmbtu/year]":
                    'wood - residential',
            "gas_residential_consumed [mmbtu/year]":
                    'natural gas - residential',
            "electric_residential_consumed [mmbtu/year]":
                    'electric - residential',
            "propane_residential_consumed [mmbtu/year]":
                    'propane - residential',
            "heating_fuel_water-wastewater_consumed [mmbtu/year]":
                    'heating oil - water wastewater',
            "heating_fuel_non-residential_consumed [mmbtu/year]":
                    'heating fuel(all) - non - residential',
            "heating_fuel_total_consumed [mmbtu/year]":'total'},
            c_dict)
        fig.subplots_adjust(right=.85)
        fig.subplots_adjust(left=.12)
        #~ plot.add_vertical_line(ax,start, 'forecasting starts' )
        plot.add_horizontal_line(ax1,0)
    
        plot.create_legend(fig,.30)
        plot.save(fig,path)
        plot.clear(fig)
        
    def calc_average_diesel_load (self):
        """
        """
        #~ self.average_diesel_load = 0
        try:
            generation = self.generation_by_type['generation diesel']
        except AttributeError:
            self.diagnostics.add_error('Forecast', 
                                        ('no generation diesel to caclulate'
                                         ' yearly average load. setting to 0'))
            generation = 0.0 
                                
        self.yearly_average_diesel_load = generation / constants.hours_per_year
        

def test ():
    """ 
    test the forecast
    """
    manley_data = CommunityData("../test_case/input_data/", 
                            "../test_case/baseline_results/config_used.yaml")
    
                            
    fc = Forecast(manley_data)

    return fc
