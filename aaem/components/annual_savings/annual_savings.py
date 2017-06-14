"""
annual_savings.py
ross spicer
created: 2015/09/16

    this file is the representation of what is being calculated at the bottom of 
each of the spread sheet tabs.
"""
import numpy as np
import os.path
from abc import ABCMeta, abstractmethod
from pandas import DataFrame


class AnnualSavings (object):
    """
        Abstract base class to use as base class for all model components 
    that have the goal of generating an NPV benefit for the project
    """
    __metaclass__ = ABCMeta
    
    def calc_annual_total_savings (self):
        """
        calculate an array of annual savings values for the project
        
        pre:
            self.annual_electric_savings and self.annual_heating_savings
        need to be arrays of dollar values. 
        post:
            annual_total_savings will be an array of dollar amounts. 
        """
        #~ print self.annual_electric_savings, self.annual_heating_savings
        self.annual_total_savings = self.annual_electric_savings + \
                              self.annual_heating_savings
    
    def calc_annual_costs (self, rate, cost_scaler = 1.0):
        """
        calculate the cost of the project for each year.
        
        pre:
            rate should be an interest rate.
            self.project_life is the # of years project is active for
            self.capital_costs is the total cost of the project
        post:
            self.annual_costs will be a numpy array of dollar values 
        indicating the cost of the project per year.
        """
        self.capital_costs *= cost_scaler
        cost_per_year = -np.pmt(rate, self.actual_project_life, 
                                    self.capital_costs) 
        #~ cpi= self.forecast.cpi.ix[self.start_year:self.end_year].T.values[0]
        self.annual_costs = cost_per_year * np.ones(self.actual_project_life)
        
    
    def calc_annual_net_benefit (self):
        """
        calculate the yearly benefit of the project
        pre:
            annual_total_savings and annual_costs are arrays of the same length
        (project life) consisting of dollar values 
        post:
            annual_net_benefit is an array of the annual monetary benefit over 
        projects life time
        """
        self.annual_net_benefit = self.annual_total_savings - self.annual_costs
        
    def calc_npv (self, rate, current_year):
        """
        clacualte the NPV net benfit
        pre:
            rate: should be the savings rate 
            self.annual_net_benefit is  an array of the annual monetary benefit 
        over projects life time
        post:
            self.net_npv, self.benefit_npv, slef.cost_npv is a dollar value
            self.benefit_cost_ratio is a ratio 
        """
        # These need to be calculated for the actual project life
        end = self.actual_project_life
        
        
        # number of arrays as zero ($ value) until project start
        yts = np.zeros((self.start_year - current_year)+1)

        self.benefit_npv = np.npv(rate, 
                           np.append(yts, self.annual_total_savings[:end]))
        self.cost_npv = np.npv(rate, np.append(yts, self.annual_costs[:end]))
        self.benefit_cost_ratio = self.benefit_npv/self.cost_npv 
        self.net_npv = np.npv(rate, 
                       np.append(yts, self.annual_net_benefit[:end]))
        
    def calc_cost_of_energy (self, fuel_amount, maintenance = 0):
        """
        calculates the cost of energy
        pre:
            fuel_amount is a the amount of fuel generated, used or saved
        units may vary (i.e. kWh, gal..) per year scaler, list, or np.array 
            maintenance is the operation and maintenance cost per year as a 
        scaler, list, or np.array 
            
        post:
            returns a price in $/[units of fuel_amount]
        """
        yts = np.zeros((self.start_year - self.cd["current year"])+1)
        
        if not type(maintenance) in [list,np.ndarray]:
            maintenance = np.zeros(self.actual_project_life) +  maintenance
        else:
            maintenance = maintenance[:self.actual_project_life]
        maintenance = np.array(maintenance)
        
        maintenance_npv = np.npv(self.cd['discount rate'], 
                                    np.append(yts, maintenance))
        
        
        if not type(fuel_amount) in [list,np.ndarray]:
            fuel_amount = np.zeros(self.actual_project_life) + fuel_amount
        else:
            fuel_amount = fuel_amount[:self.actual_project_life]  
        
        fuel_npv = np.npv(self.cd['discount rate'], 
                                    np.append(yts, fuel_amount))    
                                
        
        return (self.cost_npv + maintenance_npv)/ fuel_npv
        
    def calc_levelized_costs (self, maintenance_costs):
        """
        calculate the levelized costs
        pre:
            maintenance_costs is the operation and maintenance cost per year
            self.get_fuel_total_saved(), and self.get_total_enery_produced (), 
        must exitst and return numbers representing fuel saved, anenergy 
        produced or a dict with 'MMBtu' and 'kWh' as keys whose values are 
        numbers
        post:
            self.break_even_cost is the break even cost in $/gal
            self.levelized_cost_of_energy is the LCOE in $/kWh for 
        electricity projects, and $/MMBtu for heating projects
            for projectes with electricity efficciency and heating efficiency 
        self.levelized_cost_of_energy is a dictonary wiht 'MMBtu' and 'kWh' 
        as keys
        """
        fuel_saved = self.get_fuel_total_saved()
        self.break_even_cost = \
            self.calc_cost_of_energy(fuel_saved, maintenance_costs)
                                        
        energy_produced = self.get_total_enery_produced ()
        if type(energy_produced) is dict:
            #~ print energy_produced['MMBtu']
            self.levelized_cost_of_energy = {}
            self.levelized_cost_of_energy['MMBtu'] = \
                self.calc_cost_of_energy(energy_produced['MMBtu'][0],
                                         maintenance_costs)*\
                                            energy_produced['MMBtu'][1]
            self.levelized_cost_of_energy['kWh'] = \
                self.calc_cost_of_energy(energy_produced['kWh'][0],
                                         maintenance_costs)*\
                                            energy_produced['kWh'][1]
        else:
            self.levelized_cost_of_energy = \
                self.calc_cost_of_energy(energy_produced, maintenance_costs)
        
    def calc_internal_rate_of_return (self):
        """
        calculate the interal rate of return
        """
        self.irr = 0
        try:
            l = [-self.capital_costs] +\
                self.annual_total_savings[:self.actual_project_life].tolist()
            self.irr = np.irr(l)
        except (AttributeError, ValueError, np.linalg.linalg.LinAlgError):
            pass
            
    def set_project_life_details (self, start_year,project_life):
        """
        set the details for the project life time(
        pre:
            start_year is an int represnting a year
            projct life: is the number(int >0) of years (<= fc_period) 
            fc_period: <int> length of forecast period
        post:
            self.start_year, and self.project_life are the input values
        and self.end_year would be the year the project ends.
        """
        self.start_year = start_year
        
        #~ # do caclulations for whole forecast period & only save project life
        #~ self.project_life = fc_period 
        #~ self.end_year = self.start_year + self.project_life 
        
        # remember the actual lifetime
        self.actual_project_life = project_life
        self.project_life = project_life
        self.actual_end_year = self.start_year + project_life - 1
        self.end_year = self.start_year + project_life - 1
        
    def get_diesel_prices (self):
        """
        get the diesel prices
        
        pre:
            community name should be in the community data.
        post:
            self.diesel prices has prices for the project life
        """
        #~ prices = self.cd["diesel prices"]
        #~ self.diesel_prices = prices.get_projected_prices(self.start_year,
                                                         #~ self.end_year)
        self.cd["diesel prices"].index = \
            self.cd["diesel prices"].index.astype(int)
        self.cd["diesel prices"] = self.cd["diesel prices"].astype(float)                                               
        self.diesel_prices = self.cd["diesel prices"].ix[self.start_year:]
        self.diesel_prices.columns = ['prices']
        start, end  = self.start_year, self.end_year
        
        
        existing_len = len(self.diesel_prices.ix[start:end])
        extend_by = (end + 1) - start - existing_len
        if extend_by > 0:
            extend = DataFrame(
                index=range(
                    self.diesel_prices.index[-1] + 1,
                     self.diesel_prices.index[-1]+extend_by +1
                ), 
                columns=['prices'])
            extend['prices'] =  self.diesel_prices.iloc[-1]['prices']
            self.diesel_prices = \
                DataFrame( self.diesel_prices.ix[start:end]['prices']).\
                append(extend)
        else:
            #  -1 to ensure same behavour
            self.diesel_prices = \
                DataFrame(self.diesel_prices['prices'].ix[start:end])
        self.diesel_prices = self.diesel_prices['prices'].values

                                                         
    def get_electricity_prices (self):
        """
        """
        self.cd["electric non-fuel prices"].index = \
            self.cd["electric non-fuel prices"].index.astype(int)
        self.cd["electric non-fuel prices"] = \
            self.cd["electric non-fuel prices"].astype(float)                                               
        prices = self.cd["electric non-fuel prices"]
        self.electricity_prices = prices.ix[self.start_year:]
        
        self.cd["electric non-fuel prices"].index = self.cd["electric non-fuel prices"].index.astype(int)
        self.cd["electric non-fuel prices"] = self.cd["electric non-fuel prices"].astype(float)                                               
        self.electricity_prices = self.cd["electric non-fuel prices"].ix[self.start_year:]
        self.electricity_prices.columns = ['prices']
        start, end  = self.start_year, self.end_year
        
        
        existing_len = len(self.electricity_prices.ix[start:end])
        extend_by = (end + 1) - start - existing_len
        if extend_by > 0:
            extend = DataFrame(
                index=range(
                    self.electricity_prices.index[-1] +1 ,
                     self.electricity_prices.index[-1] + 1+extend_by
                ), 
                columns=['prices'])
            extend['prices'] =  self.electricity_prices.iloc[-1]['prices']
            self.electricity_prices = \
                DataFrame( self.electricity_prices.ix[start:end]['prices']).\
                append(extend)
        else:
            #  -1 to ensure same behavour
            self.electricity_prices = \
                DataFrame(self.electricity_prices['prices'].ix[start:end])
                
        self.electricity_prices = self.electricity_prices['prices'].values

                                                         
    def save_additional_output(self, directory):
        """
        """
        pass
    
    @abstractmethod
    def calc_capital_costs (self):
        """
        abstract function 
        should be implemented by child class to calculate self.capital_costs
        (the cost of the project) a dollar value
        """
        raise NotImplementedError, "should be implemented by child class to" +\
        " calculate self.capital_costs(the cost of the project) a dollar value"

        
    @abstractmethod
    def calc_annual_electric_savings (self):
        """
        abstract function
        should be implemented by child class to create 
        self.annual_electric_savings as an np.array, length self.project_life, 
        of dollar values(numbers)"
        """
        raise NotImplementedError, "should be implemented by child class to" +\
        " create self.annual_electric_savings as an np.array, length" +\
        " self.project_life, of dollar values(numbers)"

    @abstractmethod
    def calc_annual_heating_savings (self):
        """
        abstract function 
        should be implemented by child class to create 
        self.annual_heating_savings as an np.array, length self.project_life, 
        of dollar values(numbers)"
        """
        raise NotImplementedError, "should be implemented by child class to" +\
        " create self.annual_heating_savings as an np.array, length" +\
        " self.project_life, of dollar values(numbers)"
    
    @abstractmethod
    def run (self, scalers = {'capital costs':1.0}):
        """
        abstract function 
        should be implemented by child class to run component
        """
        raise NotImplementedError, "should be implemented by child class to" +\
        " run the component"
  
    ## helper
    def get_nan_range (self):
        """
            gets an array of nan's for the project life time, the "get" 
        functions defined here should return a array of nan's indicating that 
        the value is not applicable to the component. If a "get" should do 
        something else overload it in the component
        pre:
            self.lifetime > 0
        post:
            returns array of nan's length self.lifetime
        """
        return np.zeros(self.project_life)/0
        
    ## Heating
    def get_base_HF_use (self): # ex: eff(res) G89-V89
        """ returns HF use array (baseline) """
        try:
            return self.baseline_HF_consumption
        except:
            return self.get_nan_range()
        
    def get_proposed_HF_use (self): # ex: eff(res) G81-V81
        """ returns HF use array (proposed) """
        try:
            return self.proposed_HF_consumption
        except:
            return self.get_nan_range()
        
    def get_base_HF_cost (self): # ex: eff(res) G93-V93
        """ returns HF cost array (baseline) """
        try:
            return self.baseline_HF_cost
        except:
            return self.get_nan_range()
        
    def get_proposed_HF_cost (self): # ex: eff(res) G86-V86
        """ returns HF cost array (proposed) """
        try:
            return self.proposed_HF_cost
        except:
            return self.get_nan_range()

    def get_fuel_price (self): # ex: eff(res) G84-V84 or G90-V90
        """ get the diesel fuel price used"""
        try:
            ### TODO:CHANGE THIS TOO??
            return self.diesel_prices
        except:
            return self.get_nan_range()

        
    ## Electric 
    def get_base_kWh_use (self): # ex: eff(res) G89-V89
        """ returns kWh use array (baseline) """
        try:
            return self.baseline_kWh_consumption
        except:
            return self.get_nan_range()
        
    def get_proposed_kWh_use (self): # ex: eff(res) G73-V73
        """ returns kWh use array (proposed) """
        try:
            return self.proposed_kWh_consumption
        except:
            return self.get_nan_range()
    
    def get_base_kWh_cost (self): # ex: eff(res) G75-V75
        """ returns kWh cost array (baseline) """
        try:
            return self.baseline_kWh_cost
        except:
            return self.get_nan_range()
        
    def get_proposed_kWh_cost (self): # ex: eff(res) G70-V70
        """ returns kWh cost array (proposed) """
        try:
            return self.proposed_kWh_cost
        except:
            return self.get_nan_range()
        
    ## annual savings
    def get_electric_savings_costs (self): # ex: eff(res) G57-V57 or G75-V75
        """ returns kWh savings array (base - proposed) """
        try:
            return self.annual_electric_savings
        except:
            return self.get_nan_range()
        
    def get_heating_savings_costs (self): # ex: eff(res) G58-V58 or G94-V94
        """ returns HF savings array (base - proposed) """ 
        try:
            return self.annual_heating_savings
        except:
            return self.get_nan_range()
        
    def get_total_savings_costs (self): # ex: eff(res) G59-V59 
        """ returns total savings array """
        try:
            return self.annual_total_savings
        except:
            return self.get_nan_range()
    
    def get_capital_costs (self): # ex: eff(res) G55-V55
        """ return capital costs array """ 
        try:
            return self.annual_costs
        except:
            return self.get_nan_range()
    
    def get_net_benefit (self): # ex: eff(res) G62-V62
        """ return net benefit array """
        try:
            return self.annual_net_benefit
        except:
            return self.get_nan_range()
        
    ## NPVs
    def get_NPV_benefits (self): # ex: eff(res) C13
        """ return NPV benefits (float) """
        try:
            return self.benefit_npv
        except AttributeError:
            return "N/A"
    
    def get_NPV_costs (self): # ex: eff(res) C14
        """ return NPV costs (float) """
        try:
            return self.cost_npv
        except AttributeError:
            return "N/A"
    
    def get_BC_ratio (self): # ex: eff(res) C15
        """ return NPV benefit/cost ratio (float) """
        try:
            return self.benefit_cost_ratio
        except AttributeError:
            return "N/A"
        
    def get_NPV_net_benefit (self): # ex: eff(res) C16
        """ return NPV net benefit (float) """
        try:
            return self.net_npv
        except AttributeError:
            return "N/A"
        
    ## save functions
    def save_csv_outputs (self, directory):
        """
        save all csv outputs
        pre:
            directory should exist and be an absolute path
        post:
            electric,heating, and finical csv files are saved
        """
        self.save_component_csv(directory)
        #~ self.save_electric_csv (directory)
        #~ self.save_heating_csv (directory)
        #~ if self.cd["model financial"]:
            #~ self.save_financial_csv (directory)

    def save_component_csv (self, directory):
        """
        save the output from the component.
        """
        if not self.run:
            return
        years = np.array(range(self.project_life)) + self.start_year
        df = DataFrame({
                self.component_name + \
                    ": Heating Fuel Consumption Baseline (gallons/year)": 
                                            self.get_base_HF_use(),
                self.component_name + \
                    ": Heating Fuel Consumption Proposed (gallons/year)": 
                                            self.get_proposed_HF_use(),
                self.component_name + \
                    ": Heating Fuel Consumption Savings (gallons/year)": 
                                            self.get_base_HF_use() -\
                                            self.get_proposed_HF_use(), 
                self.component_name + \
                    ": Heating Fuel Cost Baseline ($/year)": 
                                            self.get_base_HF_cost(),
                self.component_name + \
                    ": Heating Fuel Cost Proposed ($/year)": 
                                            self.get_proposed_HF_cost(),
                self.component_name + \
                    ": Heating Fuel Cost Savings ($/year)": 
                                            self.get_heating_savings_costs(),
                self.component_name + \
                    ": Electricity Consumption Baseline (kWh/year)": 
                                            self.get_base_kWh_use(),
                self.component_name + \
                    ": Electricity Consumption Proposed (kWh/year)": 
                                            self.get_proposed_kWh_use(),
                self.component_name + \
                    ": Electricity Consumption Savings (kWh/year)": 
                                            self.get_base_kWh_use() -\
                                            self.get_proposed_kWh_use(), 
                self.component_name + \
                    ": Electricity Cost Basline ($/year)": 
                                            self.get_base_kWh_cost(),
                self.component_name + \
                    ": Electricity Cost Proposed ($/year)": 
                                            self.get_proposed_kWh_cost(),
                self.component_name + \
                    ": Electricity Cost Savings ($/year)": 
                                            self.get_electric_savings_costs(),
                self.component_name + \
                    ": Project Capital Cost ($/year)": 
                                            self.get_capital_costs(),
                self.component_name + \
                    ": Total Cost Savings ($/year)": 
                                            self.get_total_savings_costs(),
                self.component_name + \
                    ": Net Benefit ($/year)": 
                                            self.get_net_benefit(),
                       }, years)

        df["Community"] = self.cd['name']
        
        ol = ["Community",
              self.component_name + \
                        ": Heating Fuel Consumption Baseline (gallons/year)", 
              self.component_name + \
                        ": Heating Fuel Consumption Proposed (gallons/year)", 
              self.component_name + \
                        ": Heating Fuel Consumption Savings (gallons/year)", 
              self.component_name + ": Heating Fuel Cost Baseline ($/year)",
              self.component_name + ": Heating Fuel Cost Proposed ($/year)", 
              self.component_name + ": Heating Fuel Cost Savings ($/year)",
              self.component_name + \
                        ": Electricity Consumption Baseline (kWh/year)",
              self.component_name + \
                        ": Electricity Consumption Proposed (kWh/year)", 
              self.component_name + \
                        ": Electricity Consumption Savings (kWh/year)", 
              self.component_name + ": Electricity Cost Basline ($/year)",
              self.component_name + ": Electricity Cost Proposed ($/year)", 
              self.component_name + ": Electricity Cost Savings ($/year)",
              self.component_name + ": Project Capital Cost ($/year)", 
              self.component_name + ": Total Cost Savings ($/year)", 
              self.component_name + ": Net Benefit ($/year)"]
        fname = os.path.join(directory,
                               self.cd['name'] + '_' +\
                               self.component_name.lower().replace(' ','_').\
                               replace('&','and') +\
                               "_output.csv")
        fname = fname.replace(" ","_")
        
        # save to end of project(actual lifetime)
        df[ol].ix[:self.actual_end_year].to_csv(fname, index_label="Year")
                                                                    

