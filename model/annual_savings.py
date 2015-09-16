"""
annual_savings.py
ross spicer
created: 2015/09/16

    this file is the representation of what is being calculated at the bottom of 
each of the spread sheet tabs.
"""
import numpy as np
from abc import ABCMeta, abstractmethod

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
        self.annual_costs = np.pmt(rate, self.project_life, self.capital_costs)
    
    def calc_annual_benefit (self):
        """
        calculate the yearly benefit of the project
        pre:
            annual_total_savings and annual_costs are arrays of the same length
        (project life) consisting of dollar values 
        post:
            annual_benefit is an array of the annual monetary benefit over 
        projects life time
        """
        self.annual_benefit = self.annual_total_savings - self.annual_costs
        
    def calc_npv (self, rate):
        """
        clacualte the NPV net benfit
        pre:
            rate: should be the savings rate 
            self.annual_benefit is  an array of the annual monetary benefit over 
        projects life time
        post:
            self.npv is a dollar value
        """
        self.npv = np.npv(rate, self.annual_benefit)
    
    @abstractmethod
    def calc_capital_costs (self):
        """
        abstract function 
        should be implemented by child class to calculate self.capital_costs
        (the cost of the project) a dollar value
        """
        raise NotImplementedError, "should be implemented by child class to" +\
        " calculate self.capital_costs(the cost of the project) a dollar value"
    
    # is there a better way to do this? not abstract?
    @abstractmethod
    def set_project_life_details(self, start_year, project_life):
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
