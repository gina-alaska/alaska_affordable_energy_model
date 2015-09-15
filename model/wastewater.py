"""
wastewater.py
Water & Wastewater Systems

ross spicer
created: 2015/09/09

    python mock-up of eff(W & WW) tab. 
"""

## Wastewater assumptions

## heating degree days - kWh?
HDD_KWH = {"Circulating/Gravity": 3.93236229561503,
           "Circulating/Vac": 11.4132439375221,
           "Haul": 0,
           "Pressure/Gravity": -0.848162217309015,
           "Wash/HB": -0.528728194855285,
           }

## heating degree days - Gallons HF?
HDD_HF = {"Circulating/Gravity": 0.544867662390884,
           "Circulating/Vac": -0.297715988257898,
           "Haul": 0,
           "Pressure/Gravity": 2.2408614639956,
           "Wash/HB": 0.17155240756494,
           }

## Population - kWh?
POP_KWH = {"Circulating/Gravity": 54.4093002543652,
           "Circulating/Vac": 161.481419074818,
           "Haul": 69.7824047085659,
           "Pressure/Gravity": 263.448648548957,
           "Wash/HB": 144.393961746201,
           }
           
## Population - Gallons HF?
POP_HF = {"Circulating/Gravity": 3.57835240238995,
           "Circulating/Vac": 23.8252508422151,
           "Haul": 7.06151797216891,
           "Pressure/Gravity": -78.7469560579852,
           "Wash/HB": 22.3235825717145,
           }

RES_NONPCE_eligible = 0.83 # $ --- From Community Data


class WaterWastewaterSystems (object):
    """
    this class mocks up the Eff(w & ww) tab in the spreed sheet
    """
    
    def __init__ (self, hdd, population, system_type, 
                  energy_use_known, heat_recovery, audit_preformed):
        """ 
        Class initialiser 
        
        pre-conditions:
            hdd(int) is the number of heating degree days. Population(int) is 
        the population of the town. system_type(string) is one of the system 
        types used as keys to the assumption libraries. 
        energy_use_known, heat_recovery, audit_preformed(string) are set 
        to 'yes' or 'no'
        
        Post-conditions: 
            The class members are set to the initila values.
        """
        self.hdd = hdd #degree(F or c?)/ day
        self.pop = population # number of people
        self.system_type = system_type 
        self.energy_use_known = energy_use_known
        self.heat_recovery = heat_recovery
        self.audit_preformed = audit_preformed
        
    def run (self):
        """
        runs the model for the inputs section of the wastewater tab
        pre-conditions:
            Class should have be set up properly, as described in __init__ 
        post-conditions:
            All of the "estimates" will be numbers. Estimates are 
        self.electricity, self.heating_fuel, self.savings_electricity, 
        self.savings_heating_fuel, self.post_savings_electricity, and
        self.post_savings_heating_fuel
        """
        # change the 'yes'/'no' to booleans?
        if self.energy_use_known == "yes":
            self.set_actual_energy_consumption()
        elif self.energy_use_known == "no":
            self.estimate_heating_fuel_consumption()
            self.estimate_electricty_consumption()
        
        if self.audit_preformed == "yes":
            self.set_actual_energy_savings()
        elif self.audit_preformed == "no":
            self.estimate_electricty_savings()
            self.estimate_heating_fuel_savings()
            self.estimate_audit_cost()
    
        self.calc_post_savings_values()
        

    def set_actual_energy_consumption (self):
        """ 
        set the "pre" estimates to actual values
        
        pre-conditions:
            None <- probably not true if this did something
        post-conditions:
            self.electricity and self.heading_fuel are numbers 
        """
        # actual values come from somewhere? if available
        # numbers are manley #s for now
        self.electricity = 6211 # kWh
        self.heating_fuel = 628 # Gallons

        
    def estimate_heating_fuel_consumption (self):
        """
        estimate the the heating fuel consumption
        
        pre:
            None
        post:
            self.heating fuel will be a number (Gallons HF)
        """
        heat_recovery_multiplier = 1.0
        if self.heat_recovery == "yes":
            heat_recovery_multiplier = 0.5
        
        
        self.heating_fuel = (self.hdd * HDD_HF[self.system_type] + \
                                self.pop * POP_HF[self.system_type]) * \
                                heat_recovery_multiplier
    
    def estimate_electricty_consumption (self):
        """
        estimate the the electricity consumption
        
        pre:
            None
        post:
            self.heating fuel will be a number (kWh)
        """
        self.electricity = (self.hdd * HDD_KWH[self.system_type] + \
                                self.pop * POP_KWH[self.system_type])
        return self.electricity
    
    def set_actual_energy_savings (self):
        """ 
        set the actual enegry savings. 
        
        pre-conditions:
            None <- probably not true if this did something
        post-conditions:
            self.savings_electricity and self.savings_heading_fuel are numbers 
        """
        # actual values come from somewhere? if available
        # numbers are manley #s for now
        self.savings_electricity = 1553 #(kWh)
        self.savings_heating_fuel = 220 #(gallons HF)
        
    def estimate_electricty_savings (self):
        """
        estimate electricity savings
        
        pre:
            self.electricity is a number
        post: 
            self.savings_electricity is a number (kWh)
        """
        self.savings_electricity = self.electricity * .25
        
    def estimate_heating_fuel_savings (self):
        """
        estimate heating fuel savings
        
        pre:
            self.heating_fuel is a number
        post: 
            self.savings_heating_fuel is a number (Gallons HF)
        """
        self.savings_heating_fuel = self.heating_fuel * .35
        
    def set_actual_audit_cost (self):
        """
            if this is available it has to come from somewhere, but that is 
        not clear
        """
        pass
    
    
    def estimate_audit_cost (self):
        """ 
        estimate the aduit cost 
        pre:
            self.pop is an int 
        post:
            self.audit cost is a number ($ ammount)
        """
        self.audit_cost = 10000 + self.pop * 450 
        
    def calc_post_savings_values (self):
        """
            calculate the post savings estimates for heating fuel and 
        electricity consumption 
        
        pre:
            self.electricity, self.savings_electricty, self.heating_fuel, and
        self.savings_heating_fuel are numbers(kWh, kWh, Gallons HF, Gallons HF)
        post:
            post_savings_electricity is a number (kWh)
            post_savings_heating_fuel is a number (Gallons)
        """
        self.post_savings_electricity = self.electricity - \
                                        self.savings_electricity
        self.post_savings_heating_fuel = self.heating_fuel - \
                                         self.savings_heating_fuel
        
    def print_savings_chart (self):
        """
            print the savings chart to see the values in a way similar to  the 
        spread sheet.
        pre:
            the "estimates" should be numbers calling self.run() will do this
        """
        print "\tEst. Pre\tEst. Post\tEst. Savings"
        print "kWH\t" + str(int(round(self.electricity))) + "\t\t" + \
              str(int(round(self.post_savings_electricity))) + "\t\t" + \
              str(int(round(self.savings_electricity)))
        print "kWH\t" + str(int(round(self.heating_fuel))) + "\t\t" +\ 
              str(int(round(self.post_savings_heating_fuel))) + "\t\t" +\
              str(int(round(self.savings_heating_fuel)))
        
def test ():
    """
    tests the class using the manley data.
    """
    ww = WaterWastewaterSystems(14593, 89, "Haul", 'no', 'no', 'no')
    # or
    #~ww = WaterWastewaterSystems(hdd=14593,population=89,system_type="Haul",
                           #~ energy_use_known='no',heat_recovery='no',
                           #~ audit_preformed='no')
    ww.run()
    ww.print_savings_chart()
    return ww # return the object for further testing

