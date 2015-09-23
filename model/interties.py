"""
interites.py
Ross Spicer
created: 2015/09/15

    python version of interties tab. currently only the inputs section has
been implemented
"""
import numpy as np
from math import isnan


#~ from annual_savings import AnnualSavings
# for live testing ---
import annual_savings
reload(annual_savings)
AnnualSavings = annual_savings.AnnualSavings
# -------------------
from community_data import manley_data
from forecast import Forecast
import aea_assumptions as AEAA


                        

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
        self.cd = community_data

        # used in the NPV calculation so this is a relevant output
        self.current_consumption = self.cd["consumption/year"]
        self.line_losses = self.cd["line_losses"]
        
    def calc_annual_electric_savings (self):
        """
        calculate the annual electric savings
        pre:
             TODO: write this 
        post:
            self.annual_electric_savings is an np.array of $/year values
        """
        #~ self.annual_electric_savings = np.zeros(self.project_life)
        self.calc_proposed_electric_savings()
        self.calc_base_electric_savings()
        self.annual_electric_savings = self.base_electric_savings - \
                                       self.proposed_electric_savings

    #TODO: fix calculation as spread sheet is updated
    def calc_proposed_electric_savings (self):
        """
        calcualte the savings for the proposed electric savings
        pre:
            TODO: write this 
        post:
           self.proposed_electric_savings is an np.array of $/year values 
        """
        self.proposed_electric_savings = np.zeros(self.project_life) 
        elec_gen = self.ff_gen_displaced/(1.0 - self.transmission_loss) # kWh/yr
        price = self.cd["cost_power_nearest_comm"] # $/kWh
        # += to assure the array is the right length
        # $/year
        self.proposed_electric_savings += (elec_gen * price) + self.O_and_M 

    #TODO: fix calculation as spread sheet is updated    
    def calc_base_electric_savings (self, generator_repairs = 1500):
        """
        calcualte the savings for the base electric savings
        pre:
            TODO: write this 
        post:
           self.base_electric_savings is an np.array of $/year values 
        """
        self.base_electric_savings = np.zeros(self.project_life)
        fuel_use = self.ff_gen_displaced / AEAA.diesel_generation_eff # gal/yr
        fuel_cost = fuel_use * self.diesel_prices # $/yr
        
        # += to assure the array is the right length
        # $/yr + $/yr + gal/yr - gal/yr -> ($ + gal - gal)/yr -> $/yr -- WHAT?
        # i'm doing this instead $/yr + $/yr -> $/yr
        self.base_electric_savings += (fuel_cost + AEAA.diesel_generator_OM)
        
            
    def calc_annual_heating_savings (self):
        """
        calculate the annual heating savings
        pre:
             TODO: write this 
        post:
            self.annual_electric_savings is an np.array of $/year values
        """
        #~ self.calc_proposed_heating_savings() # NONE HERE
        self.calc_base_heating_savings()
        self.annual_heating_savings = self.base_heating_savings 

    #TODO: fix calculation as spread sheet is updated  
    def calc_base_heating_savings (self):
        """
        calculate the savings for the base heating savings
        pre:
            TODO: write this 
        post:
           self.base_heating_savings is an np.array of $/year values 
        """
        self.base_heating_savings = np.zeros(self.project_life)
        fuel_cost = self.diesel_prices + AEAA.heating_fuel_premium # $/gal
        fuel_cost = fuel_cost * (-self.loss_of_heat_recovered) # $/yr
        # += to assure the array is the right length
        self.base_heating_savings += fuel_cost + AEAA.fuel_repairs + \
                                     AEAA.fuel_OM # $/yr


    def run (self):
        """
        do the calculations

        pre:
            None
        post:
            All values will be calculated and usable
        """
        self.set_project_life_details(self.cd["it_start_year"],
                                      self.cd["it_lifetime"])
        
        self.calc_transmission_loss()
        self.calc_kWh_transmitted()
        
        it_road_needed = self.cd["it_road_needed"]
        tlc = AEAA.transmission_line_cost[it_road_needed]
        self.calc_transmission_line_cost(tlc)
        
        self.calc_loss_of_heat_recovered()
        self.calc_O_and_M()
        self.calc_communtiy_price_difference()
        
        self.calc_capital_costs()
        
        self.get_diesel_prices()
        self.ff_gen_displaced = \
            Forecast(2015).get_fossil_fuel_generation_displaced(self.start_year,
                                                                self.end_year)
        
        self.calc_annual_electric_savings()
        self.calc_annual_heating_savings()
        self.calc_annual_total_savings()
        
        self.calc_annual_costs(AEAA.interest_rate)
        self.calc_annual_net_benefit()
        
        self.calc_npv(AEAA.discount_rate, 2014)
        

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
        if isnan(self.cd["dist_to_nearest_comm"]) == False:
            self.transmission_loss = 1.0 - \
            ((1 - AEAA.loss_per_mile) ** self.cd["dist_to_nearest_comm"])
        #~ self.transmission_loss = round(self.transmission_loss, 7)

    def calc_kWh_transmitted (self):
        """
        calculate kWh transmitted over intertie

        pre:
            "it_resource_potential" value needs to be accessible and a string
            "dist_to_nearest_comm" value needs to be accessible and a number or
        nan for "N/a" values
            self.current_consumption is a number
            self.transmission_loss and self.line_losses are < 1
        post:
            self.kWH_transmitted is a number (kWh transmitted)
        """
        # kWh
        self.kWh_transmitted = 0
        if self.cd["it_resource_potential"].lower() != "low" and \
           isnan(self.cd["dist_to_nearest_comm"]) == False:
            self.kWh_transmitted = self.current_consumption * \
                                   (1+self.transmission_loss) * \
                                   (1+self.line_losses)

    def calc_transmission_line_cost (self, cost_per_mile):
        """
        calculate cost for transmission line

        pre:
            "it_cost_known" and "it_road_needed" are booleans
            "it_cost" value needs to be accessible and a number or
        nan if not available
            "dist_to_nearest_comm" value needs to be accessible and a number or
        nan for "N/a" values
            cost_per_mile, cost of transmission mile in dollars
        post:
            self.transmission_line_cost is a number($ value)
        """
        self.transmission_line_cost = self.cd["it_cost"]
        if self.cd["it_cost_known"] == False:
            self.transmission_line_cost = cost_per_mile * \
                                    self.cd["dist_to_nearest_comm"]

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
            "it_hr_installed" and "it_hr_operational" are booleans
            "dist_to_nearest_comm" value needs to be accessible and a number or
        nan for "N/a" values
            "diesel_consumed" is a positive number of gallons
            hr_precent is a decimal percent 

        post:
            self.loss_of_heat_recovered is a number(gallons)
        """
        self.loss_of_heat_recovered = 0         # gal
        if isnan(self.cd["dist_to_nearest_comm"]):
            self.loss_of_heat_recovered = float('nan')
        elif self.cd["it_hr_installed"] == True and \
             self.cd["it_hr_operational"] == True:
            # where does .15 come from
            # it's an argument now 
            self.loss_of_heat_recovered = \
                            self.cd["diesel_consumed"] * hr_percent

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
        if isnan(self.cd["dist_to_nearest_comm"]) == False:
            self.O_and_M = AEAA.O_and_M_cost * \
                            self.cd["dist_to_nearest_comm"]

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
        if isnan(self.cd["dist_to_nearest_comm"]) == False:
            self.communtiy_price_difference = \
                            self.cd["res_non-PCE_elec_cost"] -\
                            self.cd["cost_power_nearest_comm"]

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
    print round(it.benefit_npv,0)
    print round(it.cost_npv,0)
    print round(it.benefit_cost_ratio ,2)
    print round(it.net_npv,0)
    return it

