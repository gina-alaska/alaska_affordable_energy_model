"""
annual_savings.py
ross spicer
created: 2015/09/16

    this file is the representation of what is being calculated at the bottom of 
each of the spread sheet tabs.
"""
import numpy as np
from abc import ABCMeta, abstractmethod

from diesel_prices import DieselProjections

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
        self.annual_total_savings = self.annual_electric_savings + \
                              self.annual_heating_savings
    
    def calc_annual_costs (self, rate):
        """
        calculate the cost of the project for each year.
        
        pre:
            rate should be an interest rate.
            self.project_life is the # of years project is active for
            self.captial_costs is the total cost of the project
        post:
            self.annual_costs will be a numpy array of dollar values 
        indicating the cost of the project per year.
        """
        rate = np.zeros(self.project_life) + rate
        
        self.annual_costs = -np.pmt(rate, self.project_life
                                                    , self.capital_costs)
    
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
            self.annual_net_benefit is  an array of the annual monetary benefit over 
        projects life time
        post:
            self.net_npv, self.benefit_npv, slef.cost_npv is a dollar value
            self.benefit_cost_ratio is a ratio 
        """
        # number of arrays as zero ($ value) until project start
        yts = np.zeros((self.start_year - current_year)+1)
        #~ print yts
        
        self.benefit_npv = np.npv(rate, 
                                    np.append(yts, self.annual_total_savings))
        self.cost_npv = np.npv(rate, np.append(yts, self.annual_costs))
        self.benefit_cost_ratio = self.benefit_npv/self.cost_npv 
        self.net_npv = np.npv(rate, np.append(yts, self.annual_net_benefit))
        
    
    def set_project_life_details (self, start_year, project_life):
        """
        set the details for the project life time(
        pre:
            start_year is an int represnting a year
            projct life is the number(int >0) of years 
        post:
            self.start_year, and self.project_life are the input values
        and self.end_year would be the year the project ends.
        """
        self.start_year = start_year
        self.project_life = project_life 
        self.end_year = self.start_year + self.project_life
        
    def get_diesel_prices (self):
        """
        get the diesel prices
        
        pre:
            community name should be in the community data.
        post:
            self.diesel prices has prices for the project life
        """
        prices = DieselProjections(self.cd["name"])
        self.diesel_prices = prices.get_projected_prices(self.start_year,
                                                         self.end_year)
    
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
  
    ## Heating
    def get_base_HF_use (self): # ex: eff(res) G89-V89
        """ returns HF use array (baseline) """
        pass
        
    def get_refit_HF_use (self): # ex: eff(res) G81-V81
        """ returns HF use array (refit) """
        pass
        
    def get_base_HF_cost (self): # ex: eff(res) G93-V93
        """ returns HF cost array (baseline) """
        pass
        
    def get_refit_HF_cost (self): # ex: eff(res) G86-V86
        """ returns HF cost array (refit) """
        pass

    def get_fuel_price (self): # ex: eff(res) G84-V84 or G90-V90
        """ get the diesel fuel price used"""
        pass

        
    ## Electric 
    def get_base_kWh_use (self): # ex: eff(res) G89-V89
        """ returns kWh use array (baseline) """
        pass
        
    def get_refit_kWh_use (self): # ex: eff(res) G73-V73
        """ returns kWh use array (refit) """
        pass
    
    def get_base_kWh_cost (self): # ex: eff(res) G75-V75
        """ returns kWh cost array (baseline) """
        pass
        
    def get_refit_kWh_cost (self): # ex: eff(res) G70-V70
        """ returns kWh cost array (refit) """
        pass
        
    ## annual savings
    def get_electric_savings_costs (self): # ex: eff(res) G57-V57 or G75-V75
        """ returns kWh savings array (base - refit) """
        pass
        
    def get_heating_savings_costs (self): # ex: eff(res) G58-V58 or G94-V94
        """ returns HF savings array (base - refit) """ 
        pass
        
    def get_total_savings_costs (self): # ex: eff(res) G59-V59 
        """ returns total savings array """
        pass
    
    def get_captial_costs (self): # ex: eff(res) G55-V55
        """ return capital costs array """ 
        pass
    
    def get_net_beneft (self): # ex: eff(res) G62-V62
        """ return net benefit array """
        pass
        
    ## NPVs
    def get_NPV_benefits (self): # ex: eff(res) C13
        """ return NPV benefits (float) """
        pass
    
    def get_NPV_costs (self): # ex: eff(res) C14
        """ return NPV costs (float) """
        pass
    
    def get_BC_ratio (self): # ex: eff(res) C15
        """ return NPV benefit/cost ratio (float) """
        pass
        
    def get_NPV_net_benefit (self): # ex: eff(res) C16
        """ return NPV net benefit (float) """
        pass
