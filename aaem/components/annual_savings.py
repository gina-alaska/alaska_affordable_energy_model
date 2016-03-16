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
        cost_per_year = -np.pmt(rate, self.project_life, self.capital_costs) 
        cpi= self.forecast.cpi.ix[self.start_year:self.end_year-1].T.values[0]
        self.annual_costs = cost_per_year * cpi
        
    
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
        
    
    def set_project_life_details (self, start_year,project_life,fc_period = 25):
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
        
        # do caclulations for whole forecast period & only save project life
        self.project_life = fc_period 
        self.end_year = self.start_year + self.project_life 
        
        # remember the actual lifetime
        self.actual_project_life = project_life
        self.actual_end_year = self.start_year + project_life - 1
        
    def get_diesel_prices (self):
        """
        get the diesel prices
        
        pre:
            community name should be in the community data.
        post:
            self.diesel prices has prices for the project life
        """
        prices = self.cd["diesel prices"]
        self.diesel_prices = prices.get_projected_prices(self.start_year,
                                                         self.end_year)
                                                         
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
    def run (self):
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
        
    def get_refit_HF_use (self): # ex: eff(res) G81-V81
        """ returns HF use array (refit) """
        try:
            return self.refit_HF_consumption
        except:
            return self.get_nan_range()
        
    def get_base_HF_cost (self): # ex: eff(res) G93-V93
        """ returns HF cost array (baseline) """
        try:
            return self.baseline_HF_cost
        except:
            return self.get_nan_range()
        
    def get_refit_HF_cost (self): # ex: eff(res) G86-V86
        """ returns HF cost array (refit) """
        try:
            return self.refit_HF_cost
        except:
            return self.get_nan_range()

    def get_fuel_price (self): # ex: eff(res) G84-V84 or G90-V90
        """ get the diesel fuel price used"""
        try:
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
        
    def get_refit_kWh_use (self): # ex: eff(res) G73-V73
        """ returns kWh use array (refit) """
        try:
            return self.refit_kWh_consumption
        except:
            return self.get_nan_range()
    
    def get_base_kWh_cost (self): # ex: eff(res) G75-V75
        """ returns kWh cost array (baseline) """
        try:
            return self.baseline_kWh_cost
        except:
            return self.get_nan_range()
        
    def get_refit_kWh_cost (self): # ex: eff(res) G70-V70
        """ returns kWh cost array (refit) """
        try:
            return self.refit_kWh_cost
        except:
            return self.get_nan_range()
        
    ## annual savings
    def get_electric_savings_costs (self): # ex: eff(res) G57-V57 or G75-V75
        """ returns kWh savings array (base - refit) """
        try:
            return self.annual_electric_savings
        except:
            return self.get_nan_range()
        
    def get_heating_savings_costs (self): # ex: eff(res) G58-V58 or G94-V94
        """ returns HF savings array (base - refit) """ 
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
    
    def get_net_beneft (self): # ex: eff(res) G62-V62
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
        years = np.array(range(self.project_life)) + self.start_year
        df = DataFrame({
                "Heating Oil Consumption Baseline": self.get_base_HF_use(),
                "Heating Oil Consumption Retrofit": self.get_refit_HF_use(),
                "Heating Oil Consumption Savings": self.get_base_HF_use() -\
                                            self.get_refit_HF_use(), 
                "Heating Oil Cost Baseline": self.get_base_HF_cost(),
                "Heating Oil Cost Retrofit": self.get_refit_HF_cost(),
                "Heating Oil Cost Savings": 
                                        self.get_heating_savings_costs(),
                "Electricity Consumption Baseline": self.get_base_kWh_use(),
                "Electricity Consumption Retrofit": self.get_refit_kWh_use(),
                "Electricity Consumption Savings": self.get_base_kWh_use() -\
                                           self.get_refit_kWh_use(), 
                "Electricity Cost Basline": self.get_base_kWh_cost(),
                "Electricity Cost Retrofit": self.get_refit_kWh_cost(),
                "Electricity Cost Savings": 
                                    self.get_electric_savings_costs(),
                "Project Capital Cost": self.get_capital_costs(),
                "Total Cost Savings": self.get_total_savings_costs(),
                "Net Benefit": self.get_net_beneft(),
                       }, years)

        df["community"] = self.cd['name']
        
        ol = ["community",
              "Heating Oil Consumption Baseline", 
              "Heating Oil Consumption Retrofit", 
              "Heating Oil Consumption Savings", "Heating Oil Cost Baseline",
              "Heating Oil Cost Retrofit", "Heating Oil Cost Savings",
              "Electricity Consumption Baseline",
              "Electricity Consumption Retrofit", 
              "Electricity Consumption Savings", "Electricity Cost Basline",
              "Electricity Cost Retrofit", "Electricity Cost Savings",
              "Project Capital Cost", "Total Cost Savings", "Net Benefit"]
        fname = os.path.join(directory,
                                   self.component_name + "_output.csv")
        fname = fname.replace(" ","_")
        
        
        fin_str = "Enabled" if self.cd["model financial"] else "Disabled"
        fd = open(fname, 'w')
        fd.write(("# " + self.component_name + " model outputs\n"
                  #~ "# Finacial Component: " + fin_str + '\n'
                  #~ "# --- Cost Benefit Information ---\n"
                  #~ "# NPV Benefits: " + str(self.get_NPV_benefits()) + '\n'
                  #~ "# NPV Cost: " + str(self.get_NPV_benefits()) + '\n'
                  #~ "# NPV Net Benefit: " + str(self.get_NPV_benefits()) + '\n'
                  #~ "# Benefit Cost Ratio: " + str(self.get_BC_ratio()) + '\n'
                  #~ "# --------------------------------\n"
          "# year: year for projection \n"
          "# Heating Oil Consumption Baseline: Gallons Heating "
                                        "Fuel used with no retrofits \n"
          "# Heating Oil Consumption Retrofit: Gallons Heating "
                                        "Fuel used with retrofits \n"
          "# Heating Oil Consumption Savings: Gallons Heating Oil savings \n"
          "# Heating Oil Cost Baseline: Cost Heating "
                                        "Fuel used with no retrofits \n"
          "# Heating Oil Cost Retrofit: Cost Heating "
                                        "Fuel used with retrofits \n"
          "# Heating Oil Cost Savings: Cost Heating Oil savings \n"
          "# Electricity Consumption Baseline: kWh used with no retrofits \n"
          "# Electricity Consumption Retrofit: kWh used with retrofits \n"
          "# Electricity Consumption Savings: kWh savings \n"
          "# Electricity Cost Baseline: Cost kWh used with no retrofits\n"
          "# Electricity Cost Retrofit: Cost kWh used with retrofits \n"
          "# Electricity Cost Savings: Cost kWh savings \n"
          "# Project Capital Cost: Cost of retrofits \n"
          "# Total Cost Savings: savings from retrofits\n"
          "# Net Benefit: benefit from retrofits\n"
                  )) 
        fd.close()
        
        # save npv stuff
        df2 = DataFrame([self.get_NPV_benefits(),self.get_NPV_costs(),
                            self.get_NPV_net_benefit(),self.get_BC_ratio()],
                       ['NPV Benefits','NPV Cost',
                            'NPV Net Benefit','Benefit Cost Ratio'])
        df2.to_csv(fname, header = False, mode = 'a')
        
        # save to end of project(actual lifetime)
        df[ol].ix[:self.actual_end_year].to_csv(fname, index_label="year", 
                                                                    mode = 'a')
                                                                    

