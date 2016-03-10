"""
forecast.py
Ross Spicer
created: 2015/09/18

    forecast
"""
from community_data import CommunityData
from diagnostics import diagnostics
import constants
import plot

import numpy as np
from pandas import DataFrame, read_csv, concat
import os.path
import copy



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
        
        yr = self.cd.get_item('residential buildings', 'data').ix['year']
        self.base_pop = self.fc_specs['population'].ix[yr].values[0][0]
        
        kWh = self.fc_specs["electricity"]
        self.base_res_consumption = float(kWh['consumption residential'].ix[yr])
        self.base_non_res_consumption = \
            float(kWh['consumption non-residential'].ix[yr])
        self.base_total_consumption = float(kWh['consumption'].ix[yr])
        
        self.cpi = self.cd.load_pp_csv("cpi.csv")
        self.forecast_population()
        self.forecast_consumption()
        self.forecast_generation()
        self.forecast_average_kW()
        self.forecast_households()
        self.heat_demand_cols = []
        self.heating_fuel_cols = [] 
        self.electric_columns = []
        

    def calc_electricity_totals (self):
        """ 
        pre:
            'fc_electricity_used' should contain the kWh used for each key type
        post:
            self.electricty_totals is a array of yearly values of total kWh used
        """
        kWh = self.fc_specs["electricity"]
        years = kWh.T.keys().values
        self.yearly_kWh_totals = DataFrame({"year":years,
                          "total":kWh['consumption'].values}).set_index("year")

    def forecast_population (self):
        """
        pre:
            tbd.
        post:
            self.population is a array of estimated populations for each 
        year between start and end
        """
        # pop forecast is preprocessed now
        self.p_map = DataFrame(self.fc_specs["population"]\
                                            ["population_qualifier"])
        self.population = DataFrame(self.fc_specs["population"]["population"])
        if len(self.p_map[self.p_map == "M"] ) < 10:
            msg = "the data range is < 10 for input population "\
                  "check population.csv in the models data directory"
            self.diagnostics.add_warning("forecast", msg)
        
        
    def forecast_consumption (self):
        """
        pre:
            tbd.
        post:
            self.consumption is a array of estimated kWh consumption for each 
        year between start and end
        """
        self.calc_electricity_totals()
        idx =  self.yearly_kWh_totals.index.values.astype(int).tolist()

        if len(self.yearly_kWh_totals) < 10:
            msg = "the data range is < 10 for input consumption "\
                  "check electricity.csv in the models data directory"
            self.diagnostics.add_warning("forecast", msg)
        population = self.population.ix[idx]
        if any(population.isnull()):
            v= population.isnull().values.T.tolist()[0]
            for year in population[v].index.values.tolist():
                idx.remove(year)
        
        if any(self.yearly_kWh_totals.isnull()):
            v = self.yearly_kWh_totals.isnull().values.T.tolist()[0]
            for year in self.yearly_kWh_totals[v].index.values.tolist():
                idx.remove(year)
        
        self.diagnostics.add_note("forecast", 
           "years with measured consumption and population " + str(idx) +\
        ". List used to generate fit function")
        population = self.population.ix[idx]
        population = self.population.ix[idx].T.values[0]
        self.measured_consumption = self.yearly_kWh_totals.ix[idx]
        consumption = self.measured_consumption.T.values[0]
        if len(population) < 10:
            self.diagnostics.add_warning("forecast", 
                  "the data range is < 10 matching years for "\
                  "population and consumption "\
                  "check population.csv and electricity.csv "\
                  "in the models data directory")
        # get slope(m),intercept(b)
        try:
            m, b = np.polyfit(population,consumption,1) 
        except TypeError:
            raise RuntimeError, "Known population & consumption do not overlap"
        
        fc_consumption = m * self.population + b
        start = int(self.measured_consumption.index[-1] + 1)
        years= idx +self.population.ix[start:].index.values.astype(int).tolist()
        cons = (consumption-consumption).tolist() + \
                                  fc_consumption.ix[start:].T.values[0].tolist()
                                  
        self.c_map = DataFrame({'year':years, 'consumption': cons}).\
                                                        set_index('year').\
                                                        astype(bool).\
                                                        astype(str).\
                                                        replace("True", "P").\
                                                        replace("False", "M")   
        self.c_map.columns  = [self.c_map.columns[0] + "_qualifier"]
        
        cons = consumption.tolist() +\
                                fc_consumption.ix[start:].values.T.tolist()[0]
        consumption = DataFrame({'year':years, 
                                 'consumption': cons}).set_index('year')
        consumption.columns = ["consumption kWh"]
        self.consumption = consumption
        self.consumption.index = self.consumption.index.values.astype(int)
        self.start_year = int(self.yearly_kWh_totals.T.keys()[-1])
        
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
        generation = self.consumption/\
                    (1.0-self.cd.get_item('community','line losses'))
        self.generation = generation.apply(np.round, args=(-3,))
        
        
        try:
            real = self.cd.get_item('community',"generation")[2003:]
            idx = real.index.values.tolist()
            df = DataFrame(real.ix[idx])
            df.columns = ['consumption kWh']
            self.generation.ix[idx] = df.ix[idx]
        except:
            pass
        
        
        
        self.generation.columns = ["kWh generation"]
        
    def forecast_average_kW (self):
        """
        forecast the average kW used per community per year
        pre:
        post:
        """
        self.average_kW = (self.consumption/ 8760.0)\
                                /(1-self.cd.get_item('community','line losses'))
        
        self.average_kW.columns = ["avg. kW"]
        
    def forecast_households (self):
        """
        forcast # of houselholds
        pre:
        post:
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
            saves 3 files
        """
        tag = self.cd.get_item("community", "name").replace(" ", "_") + "_"
        pathrt = os.path.join(path, tag)
        os.makedirs(os.path.join(path,"images"))
        if self.cd.intertie != 'child':
            self.save_electric(pathrt, os.path.join(path,"images",tag))
        if self.cd.intertie != 'parent':
            self.save_heat_demand(pathrt, os.path.join(path,"images",tag))
            self.save_heating_fuel(pathrt, os.path.join(path,"images",tag))

    
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
        kWh_con = self.consumption
        kWh_con.columns = ["total_electricity_consumed [kWh/year]"]
        c_map = copy.deepcopy(self.c_map)
        c_map.columns = ["total_electricity_consumed_qualifier"]
        
        kWh_gen = self.generation
        kWh_gen.columns = ["total_electricity_generation [kWh/year]"]
        g_map = copy.deepcopy(c_map)
        g_map.columns = ["total_electricity_generation_qualifier"]
    
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
            
    
    
    def save_electric (self, csv_path, png_path):
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
        start = self.p_map[self.p_map['population_qualifier'] == 'P'].index[0]
        df2 = self.electric_dataframe[['population',
                                    'total_electricity_consumed [kWh/year]',
                                    'total_electricity_generation [kWh/year]']]
        name = self.cd.get_item("community","name") + ' Electricity Forecast'
        
        fig, ax = plot.setup_fig(name ,'years','population')
        ax1 = plot.add_yaxis(fig,'kWh')
        
        plot.plot_dataframe(ax1,df2,ax,['population'],
                       column_map = {'population':'population',
                    'total_electricity_consumed [kWh/year]':'consumption',
                    'total_electricity_generation [kWh/year]':'generation'})
        fig.subplots_adjust(right=.85)
        fig.subplots_adjust(left=.12)
        plot.add_vertical_line(ax,start, 'forecasting starts' )
    
    
        plot.create_legend(fig)
        plot.save(fig,path)
    
    def generate_heat_demand_dataframe (self):
        """
        """
        data = concat([self.population.round().astype(int), self.p_map] + \
                                                self.heat_demand_cols,axis=1) 
    
        for key in data.keys():
            try:
                col = data[key]
                lv = col[np.logical_not(col.apply(np.isnan))].tail(1).values[0]
                yr = col[np.logical_not(col.apply(np.isnan))].tail(1).index[0]
                col[col.index > yr] = lv
                data[key] = col
            except (TypeError, IndexError):
                pass
            
        idx = ['mmbtu' in s for s in data.keys()]
        total_demand = DataFrame(data[data.keys()[idx]].sum(1))
        total_demand.columns = ["heat_energy_demand_total [mmbtu/year]"]

        community = copy.deepcopy(self.c_map)
        community.columns = ["community"]
        community.ix[:] = self.cd.get_item("community","name")
        data = concat([community, data, total_demand], axis=1)
        
        for key in data.keys():
            try:
                col = data[key]
                data[key] = col.round()
            except (TypeError, AttributeError):
                pass
        self.heat_demand_dataframe = data
    def save_heat_demand (self,csv_path, png_path):
        """ Function doc """
        self.generate_heat_demand_dataframe()
        self.save_heat_demand_csv(csv_path)
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
        fd.close()
        
        data.index = data.index.values.astype(int)
        data.to_csv(f_name, index_label="year", mode = 'a')
        
    def save_heat_demand_png(self,path):
        """
        """
        path = path+ "heat_demand_forecast.png"
        start = self.p_map[self.p_map['population_qualifier'] == 'P'].index[0]
        df2 = self.heat_demand_dataframe[['population',
                            'heat_energy_demand_residential [mmbtu/year]',
                            'heat_energy_demand_water-wastewater [mmbtu/year]',
                            'heat_energy_demand_non-residential [mmbtu/year]',
                            'heat_energy_demand_total [mmbtu/year]']]
        name = self.cd.get_item("community","name") + ' Heat Demand Forecast'
        
        fig, ax = plot.setup_fig(name ,'years','population')
        ax1 = plot.add_yaxis(fig,'Heat Demand MMBtu')
        
        plot.plot_dataframe(ax1,df2,ax,['population'],
            {'population':'population',
        'heat_energy_demand_residential [mmbtu/year]':'residential',
        'heat_energy_demand_water-wastewater [mmbtu/year]':'water & wastewater',
        'heat_energy_demand_non-residential [mmbtu/year]':'non-residential',
                        'heat_energy_demand_total [mmbtu/year]':'total'})
        fig.subplots_adjust(right=.85)
        fig.subplots_adjust(left=.12)
        plot.add_vertical_line(ax,start, 'forecasting starts' )
    
    
        plot.create_legend(fig,.2)
        plot.save(fig,path)
        
    
    def generate_heating_fuel_dataframe(self):
        """ """
        data = concat([self.population.round().astype(int), self.p_map] + \
                                                self.heating_fuel_cols, axis=1)
                                                
        for key in data.keys():
            try:
                col = data[key]
                lv = col[np.logical_not(col.apply(np.isnan))].tail(1).values[0]
                yr = col[np.logical_not(col.apply(np.isnan))].tail(1).index[0]
                col[col.index > yr] = lv
                data[key] = col
            except (TypeError, IndexError):
                
                pass

        #~ hf_gal_idx = ['heating_fuel' in s for s in data.keys()] and \
        hf_gal_idx = data.keys()[['gallons' in s for s in data.keys()]]
        hf_gal_idx =  hf_gal_idx[['heating_fuel' in s for s in hf_gal_idx]]
        #~ hf_gal_idx = hf_gal_idx[['heating_fuel' in s for s in hf_gal_idx]]
        #~ print data[hf_gal_idx]
                                         
        #~ hf_btu_idx = ['heating_fuel' in s for s in data.keys()] and \
        hf_btu_idx = data.keys()[['mmbtu' in s for s in data.keys()]]
        hf_btu_idx =  hf_btu_idx[['heating_fuel' in s for s in hf_btu_idx]]

        total_gal = DataFrame(data[hf_gal_idx].sum(1)).round()
        total_gal.columns = ["heating_fuel_total_consumed [gallons/year]"]
        
        total_btu = DataFrame(data[hf_btu_idx].sum(1)).round()
        total_btu.columns = ["heating_fuel_total_consumed [mmbtu/year]"]
        
        
        community = copy.deepcopy(self.c_map)
        community.columns = ["community"]
        community.ix[:] = self.cd.get_item("community","name")
        data = concat([community,data,total_gal,total_btu],axis=1)
        
        for key in data.keys():
            try:
                col = data[key]
                data[key] = col.round()
            except (TypeError, AttributeError):
                pass
        self.heating_fuel_dataframe = data
    
    def save_heating_fuel(self, csv_path, png_path):
        """ """
        self.generate_heating_fuel_dataframe()
        self.save_heating_fuel_csv(csv_path)
        self.save_heating_fuel_png(png_path)
    
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
        fd.close()
        for key in data.keys():
            try:
                col = data[key]
                lv = col[np.logical_not(col.apply(np.isnan))].tail(1).values[0]
                yr = col[np.logical_not(col.apply(np.isnan))].tail(1).index[0]
                col[col.index > yr] = lv
                data[key] = col.round()
            except (TypeError, IndexError):
                pass
            except AttributeError:
                pass
        data.index = data.index.values.astype(int)
        data.to_csv(f_name, index_label="year", mode = 'a')
        
    def save_heating_fuel_png (self, path):
        """"""
        path = path+ "heating_fuel_forecast.png"
        start = self.p_map[self.p_map['population_qualifier'] == 'P'].index[0]
        df2 = self.heating_fuel_dataframe[["population",
            "heating_fuel_residential_consumed [mmbtu/year]",
            "cords_wood_residential_consumed [mmbtu/year]",
            "gas_residential_consumed [mmbtu/year]",
            "electric_residential_consumed [mmbtu/year]",
            "propane_residential_consumed [mmbtu/year]",
            "heating_fuel_water-wastewater_consumed [mmbtu/year]",
            "heating_fuel_non-residential_consumed [mmbtu/year]",
            "heating_fuel_total_consumed [mmbtu/year]"]]

        name = self.cd.get_item("community","name") + ' Heat Demand Forecast'
        
        fig, ax = plot.setup_fig(name ,'years','population')
        ax1 = plot.add_yaxis(fig,'Heat Demand MMBtu')
        
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
                    'heating oil - non - residential',
            "heating_fuel_total_consumed [mmbtu/year]":'total'})
        fig.subplots_adjust(right=.85)
        fig.subplots_adjust(left=.12)
        plot.add_vertical_line(ax,start, 'forecasting starts' )
    
    
        plot.create_legend(fig,.30)
        plot.save(fig,path)
       

def test ():
    """ 
    test the forecast
    """
    manley_data = CommunityData("../test_case/input_data/", 
                            "../test_case/baseline_results/config_used.yaml")
    
                            
    fc = Forecast(manley_data)

    return fc
