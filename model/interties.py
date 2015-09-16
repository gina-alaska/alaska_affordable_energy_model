"""
interites.py
Ross Spicer
created: 2015/09/15

    python version of interties tab. currently only the inputs section has
been implemented
"""
import numpy as np
from math import isnan


from annual_savings import AnnualSavings
#~ # for live testing ---
#~ import annual_savings
#~ reload(annual_savings)
#~ AnnualSavings = annual_savings.AnnualSavings
#~ # -------------------
from community_data import manley_data



# AEA Assumptions. Also, should move somewhere
loss_per_mile = .001 # Transmission line loss/mile (%)
O_and_M_cost = 10000.00 # $/mile/year
project_life = 20 # years
start_year = 2016

interest_rate = .05
discount_rate = .03

transmission_line_cost = {True:  500000, # road needed  -- $/mi
                          False: 250000  # road not needed -- $/mi
                         } 

class Interties (AnnualSavings):
    """
    class for preforming the interties work
    """

    def __init__ (self, community_data):
        """
        Class initialiser

        pre:
            community_data is a class( or whatever) of community data
        post:
            the model can be run
        """
        self.community_data = community_data

        # used in the NPV calculation so this is a relevant output
        self.current_consumption = self.community_data["consumption/year"]
        self.line_losses = self.community_data["line_losses"]
        


    def calc_annual_electric_savings (self):
        """
        calculate the annual electric savings
        """
        self.annual_electric_savings = np.zeros(self.project_life)
        # calc poposed
        # calc base
        # set self.electric_savings to proposed - base
        
    
    def calc_annual_heating_savings (self):
        """
        calculate the annual heating savings 
        """
        self.annual_heating_savings = np.zeros(self.project_life)
        # same as calc_electric_savings work flow but for heating

    def run (self):
        """
        do the calculations

        pre:
            None
        post:
            All values will be calculated and usable
        """
        self.set_project_life_details(start_year ,project_life)
        
        self.calc_transmission_loss()
        self.calc_kWh_transmitted()
        
        road_needed = self.community_data["road_needed"]
        self.calc_transmission_line_cost(transmission_line_cost[road_needed])
        
        self.calc_loss_of_heat_recovered()
        self.calc_O_and_M()
        self.calc_communtiy_price_difference()
        
        self.calc_capital_costs()
        self.calc_annual_electric_savings()
        self.calc_annual_heating_savings()
        self.calc_annual_total_savings()
        
        self.calc_annual_costs(interest_rate)
        self.calc_annual_benefit()
        
        self.calc_npv(discount_rate)
        

    def calc_transmission_loss (self):
        """
        calculate annual transmission loss percentage

        pre:
            "dist_to_nearest_comm" value needs to be accessible and a number or
        nan for "N/a" values
            loss_per_mile is a number < 1
        post:
            self.transmission_loss is a number (a percentege)
        """
        # %/year
        self.transmission_loss = 0 # Annual Transmission Loss Percentage
        if isnan(self.community_data["dist_to_nearest_comm"]) == False:
            self.transmission_loss = 1.0 - \
            ((1 - loss_per_mile) ** self.community_data["dist_to_nearest_comm"])
        #~ self.transmission_loss = round(self.transmission_loss, 7)

    def calc_kWh_transmitted (self):
        """
        calculate kWh transmitted over intertie

        pre:
            "resource_potential" value needs to be accessible and a string
            "dist_to_nearest_comm" value needs to be accessible and a number or
        nan for "N/a" values
            self.current_consumption is a number
            self.transmission_loss and self.line_losses are < 1
        post:
            self.kWH_transmitted is a number (kWh transmitted)
        """
        # kWh
        self.kWh_transmitted = 0
        if self.community_data["resource_potential"].lower() != "low" and \
           isnan(self.community_data["dist_to_nearest_comm"]) == False:
            self.kWh_transmitted = self.current_consumption * \
                                   (1+self.transmission_loss) * \
                                   (1+self.line_losses)

    def calc_transmission_line_cost (self, cost_per_mile):
        """
        calculate cost for transmission line

        pre:
            "intertie_cost_known" and "road_needed" are booleans
            "intertie_cost" value needs to be accessible and a number or
        nan if not available
            "dist_to_nearest_comm" value needs to be accessible and a number or
        nan for "N/a" values
            cost_per_mile, cost of transmission mile in dollars
        post:
            self.transmission_line_cost is a number($ value)
        """
        self.transmission_line_cost = self.community_data["intertie_cost"]
        if self.community_data["intertie_cost_known"] == False:
            self.transmission_line_cost = cost_per_mile * \
                                    self.community_data["dist_to_nearest_comm"]

    def calc_capital_costs (self):
        """
        set the capital costs
        
        pre:
            self.calc_transmission_line_cost needs to have been called
        post:
            self.capital_costs is the cost of the transmission line
        """
        self.capital_costs = self.transmission_line_cost

    def calc_loss_of_heat_recovered (self, hr_percent = .15):
        """
        calculate loss of heat recovered

        pre:
            "HR_installed" and "HR_operational" are booleans
            "dist_to_nearest_comm" value needs to be accessible and a number or
        nan for "N/a" values
            "diesel_consumed" is a positive number of gallons
            hr_precent is a decimal percent 

        post:
            self.loss_of_heat_recovered is a number(gallons)
        """
        self.loss_of_heat_recovered = 0         # gal
        if isnan(self.community_data["dist_to_nearest_comm"]):
            self.loss_of_heat_recovered = float('nan')
        elif self.community_data["HR_installed"] == True and \
             self.community_data["HR_operational"] == True:
            # where does .15 come from
            # it's an argument now 
            self.loss_of_heat_recovered = \
                            self.community_data["diesel_consumed"] * hr_percent

    def calc_O_and_M (self):
        """
        calculate O&M

        pre:
            "dist_to_nearest_comm" value needs to be accessible and a number or
        nan for "N/a" values
            O_and_M_cost is a positive dollar amount

        post:
            self.O_and_M is a number(gallons/year)
        """
        self.O_and_M = float('nan')
        if isnan(self.community_data["dist_to_nearest_comm"]) == False:
            self.O_and_M = O_and_M_cost * \
                            self.community_data["dist_to_nearest_comm"]

    def calc_communtiy_price_difference (self):
        """
        calculate Difference in Price between communities


        pre:
            "dist_to_nearest_comm" value needs to be accessible and a number or
        nan for "N/a" values
            "res_non-PCE_elec_cost" and "cost_power_nearest_comm" should
        be positive dollar ammounts

        post:
            self.communtiy_price_difference is a number ($) or Nan if
            not available
        """
        self.communtiy_price_difference = float('nan')
        if isnan(self.community_data["dist_to_nearest_comm"]) == False:
            self.communtiy_price_difference = \
                            self.community_data["res_non-PCE_elec_cost"] -\
                            self.community_data["cost_power_nearest_comm"]

    def print_proposed_sytstem_analysis (self):
        """
        print system analysis

        pre:
            all of the functions in the class need to have been called( calling
        run() does this)
        post:
            none
        """
        text =  "kWh currently consumed                  : " + \
                str(self.current_consumption) + " kWh \n"
        text += "Annual Transmission Loss %              : " + \
                str(round(self.transmission_loss,3)*100) + "%\n"
        text += "Distribution line Losses                : " + \
                str(int((round(self.line_losses,2)*100))) + "%\n"
        text += "kWh tranmitted over intertie            : " + \
                str((round(self.kWh_transmitted,1))) + " kWh\n"
        text += "Cost for Transmission Line              : " + \
                "$ " + str(int(round(self.transmission_line_cost))) + "\n"
        text += "Loss of Heat Recovered from Gen-set     : " + \
                str(round(self.loss_of_heat_recovered)) + " gal\n"
        text += "O&M                                     : " + \
                "$ " + str(int(round(self.O_and_M))) + "/year\n"
        text += "System Lifetime                         : " + \
                str(self.project_life) + " years\n"
        text += "Difference in Price between communities : " + \
                "$ " + str(round(self.communtiy_price_difference,2)) + "\n"
        print text


def test ():
    """
    test the class
    pre:
        manley_data will eventually have to be an object of the proper
    type(for now it's hardcoded here).
    post:
        returns an Interties object for further testing
    """
    it = Interties(manley_data)
    it.run()
    it.print_proposed_sytstem_analysis()
    print ""
    print "NPV net benefit: " + str(it.npv)
    return it

