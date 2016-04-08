"""
preprocessor.py
ross spicer

process data into a format for the model to use
"""
from pandas import DataFrame,read_csv, concat
import shutil
import os.path
from diagnostics import diagnostics
import numpy as np
#~ from forecast import growth
from datetime import datetime


GENERATION_AVG = .03

MODEL_FILES = {"DIESEL_PRICES": "diesel_fuel_prices.csv",
               "HDD": "hdd.csv",
               "CPI": "cpi.csv",
               "COM_BUILDING_EST": "com_building_estimates.csv",
               "COM_BUILDING_INV": "community_buildings.csv",
               "COM_BUILFING_COUNT": "com_num_buildings.csv",
               "INTERTIES": "interties.csv",
               "PRICES": "prices.csv",
               "REGION": "region.csv",
               "RES_DATA": "residential_data.csv",
               "WWW_DATA": "wastewater_data.csv",
               "POPULATION": "population.csv",
               "ELECTRICITY": "yearly_electricity_summary.csv",
               "PRICES_NONELECTRIC": 'prices_non-electric_fixed.csv',
               "COPIES":'copies.csv'}

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


class Preprocessor (object):
    def __init__ (self, com_id, data_dir, out_dir, diag = None):
        if diag == None:
            diag = diagnostics()
        self.diagnostics = diag
        self.comments_dataframe_divide = "#### #### #### #### ####\n"
        self.com_id = com_id # will be ID #
        self.community = com_id # will be name
        # join add ensure the path is a directory
        self.data_dir = os.path.join(os.path.abspath(data_dir),"")
        self.out_dir = os.path.join(os.path.abspath(out_dir),"")

    def preprocess (self):
        """
        preprocess data in to data dir

        pre:
            data dir: path to the data files from the AAEM-data dir
            out_dir: save location
            com_id: community id("Name")
        post:
            all of the files necessary to run the model are in out_dir,
        if out_dir dose not it exist it is created
        """
         # join makes it a directory not a file
        data_dir = self.data_dir
        out_dir = self.out_dir
        com_id = self.com_id
        print com_id
        try:
            os.makedirs(out_dir)
        except OSError:
            pass
        self.load_ids()
        
        self.interties()
        self.prices()

        ### copy files that still need their own preprocessor function yet
        shutil.copy(os.path.join(data_dir,"diesel_fuel_prices.csv"), out_dir)
        shutil.copy(os.path.join(data_dir,"cpi.csv"), out_dir)

        ###
        try:
            self.hdd()
        except KeyError:
            self.diagnostics.add_warning("HDD (Heating Degree-Days)",
                                ("" + self.com_id + " not found in input data"
                                 " if interties parent community will be used"))

        self.population()
        self.electricity()
        self.region()

        self.residential()
        self.residential_add_kWh_consumption_per_household()
        #~ print self.residential_data.ix['year']
        base_pop = np.float(self.population_data.ix\
                        [int(self.residential_data.ix['year'])]["population"])
        self.buildings(base_pop)
        self.wastewater()






    ## HEADER FUNCTIONS ########################################################
    def population_header (self, source):
        """
        returns the population file header
        """
        # TODO: find original source (ADEG & TotalPopulationPlace2014.xls??)
        return "# " + self.com_id + " population\n" + \
               "# generated: " + str(datetime.now()).split('.')[0] +"\n" +\
               "# Data Source: " + source + "\n" +\
               "# recorded population in a given year\n" + \
               self.comments_dataframe_divide

    def electricity_header (self, source = "PCE"):
        """
        """
        return "# " + self.com_id + " kWh Generation data\n" + \
               "# generated: " + str(datetime.now()).split('.')[0] +"\n" +\
               "# Data Source: " + source + "\n" +\
               "# generation (kWh/yr) gross generation "+\
                                                "(net generation for EIA)\n" + \
               "# consumption(kWh/yr) total kwh sold\n" + \
               "# fuel used(gal/yr) fuel used in generation\n" + \
               '# efficiency (kwh/gal) efficiency of generator/year\n' + \
               '# line loss (% as decimal) kwh lost from transmission\n' + \
               "# net generation(kWh/yr) generation without " + \
                                                  "powerhouse consumption\n" + \
               "# consumption residential (kWh/yr) residential kwh sold\n" + \
               "# consumption non-residential (kWh/yr) non-residential " + \
                                                                "kwh sold\n" + \
               "# generation <fuel source> (kWh/yr) generation from source\n"+ \
               "# Data Source: (DATA REPO)\n" +\
               self.comments_dataframe_divide

    def electricity_prices_header (self, source = "PCE"):
        """
        Function doc
        """
        return "# " + self.com_id + " electricity consumption\n" + \
               "# generated: " + str(datetime.now()).split('.')[0] +"\n" +\
               "# Data Source: " + source + "\n" +\
               "# all units are in $/kWh \n" + \
               self.comments_dataframe_divide

    def wastewater_header (self):
        """
        """
        #TODO find what assumptions mean
        #TODO check sources
        return  "# " + self.com_id + " wastewater data\n"+ \
                "# generated: " + str(datetime.now()).split('.')[0] +"\n" +\
                "# source: wastewater_data.csv" +\
                "# System Type: The system type \n"+ \
                "# SQFT: system square feet  \n"+ \
                "# HF Used: gal/yr Heating fuel used pre-retrofit\n"+ \
                "# HF w/Retro: gal/yr Heating fuel used post-retrofit\n"+ \
                "# kWh/yr: kWh/yr used pre-retrofit\n"+ \
                "# kWh/yr w/ retro: kWh/yr used post-retrofit\n"+ \
                "# Implementation Cost: cost to refit \n"+ \
                "# HR: heat recovery (units ???) \n"+ \
                "# Steam District: ??? \n"+ \
                "# -----------------------------" +\
                "# source: wastewater_assumptions.csv (AEA)" +\
                "# HDD kWh: assumption ??? \n"+ \
                "# HDD HF: an assumption ??? \n"+ \
                "# pop kWh: an assumption ??? \n"+ \
                "# pop HF: an assumption ??? \n"+ \
                self.comments_dataframe_divide

    def residential_header (self):
        """
        """
        ## original source is ss_model. where is that from?
        return  "# " + self.com_id + " residential data\n"+\
                "# generated: " + str(datetime.now()).split('.')[0] +"\n" +\
                "# Data Source: residential_data.csv"+\
                "# energy_region: region used by model \n"+\
                "# year: year of data  collected \n"+\
                "# total_occupied: # houses occupied \n"+\
                "# BEES_number: # of houses at BEES standard \n"+\
                "# BEES_avg_area: average Sq. ft. of BEES home \n"+\
                "# BEES_avg_EUI: BEES energy use intensity MMBtu/sq. ft.\n"+\
                "# BEES_total_consumption: " +\
                                "   BEES home energy consumption MMBtu \n"+\
                "# pre_number: # of houses pre-retrofit \n"+\
                "# pre_avg_area: average Sq. ft. of pre-retrofit home \n"+\
                "# pre_avg_EUI: " +\
                          "pre-retrofit energy use intensity MMBtu/sq. ft.\n"+\
                "# post_number: # of houses at post-retrofit \n"+\
                "# post_avg_area: average Sq. ft. of post-retrofithome \n"+\
                "# post_avg_EUI: post-retrofit energy use intensity "+\
                         "MMBtu/sq. ft.\n"+\
                "# post_total_consumption: "+\
                            "post-retrofit home energy consumption MMBtu \n"+\
                "# opportunity_non-Wx_HERP_BEES:  # of houses \n"+\
                "# opportunity_potential_reduction: ???? \n"+\
                "# opportunity_savings: "+\
                            "potention savings in heating Fuel(gal)\n"+\
                "# opportunity_total_percent_community_savings: ???\n"+\
                "# Total; Utility Gas; LP; Electricity; Fuel Oil; "+\
                        "Coal; Wood; Solar; Other; No Fuel Used: " +\
                                        "% of heating fuel types\n"+\
                self.comments_dataframe_divide

    def buildings_count_header (self):
        """
        """
        ## original source is AEA?
        return  "# " + self.com_id + " non-residential building count\n" + \
                "# generated: " + str(datetime.now()).split('.')[0] +"\n" +\
                "# Data Source: com_num_buildings.csv \n" +\
                self.comments_dataframe_divide


    def buildings_estimates_header (self, pop):
        """
        """
        # original source is AEA
        # what is HDD
        return  "# " + self.com_id + " non-residential building estimates\n" +\
                "# generated: " + str(datetime.now()).split('.')[0] +"\n" +\
                "# Data Source: com_building_estimates.csv \n" +\
                "# Population used for estimates " + str(pop) + "\n"+\
                "# building type: index \n" +\
                "# kWh/sf: estimate kWh/sf used for building type\n" +\
                "# Gal/sf: estimate Gal/sf Heating fuel for building type\n" +\
                "# HDD: estimate Heating Degree Day\n" +\
                "# Sqft: estimate square footage for building type\n" +\
                self.comments_dataframe_divide

    def buildings_inventory_header (self):
        """
        """
        # original source compiled by AEA
        # find units for fuel sources
        return  "# " + self.com_id + " non-residential building inventory\n" +\
                "# generated: " + str(datetime.now()).split('.')[0] +"\n" +\
                "# Data Source: non_res_buildings.csv \n" +\
                "# building type: index \n" +\
                "# Square Feet: Measured Square Footage of building\n" +\
                "# Audited: True or False \n" +\
                "# Retrofits Done: True or False \n" +\
                "# implementation cost: Cost to refit \n" +\
                "# Electric: kWh used \n" +\
                "# Electric Post: kWh used if refit\n" +\
                "# Fuel Oil: Gal fuel oil used \n" +\
                "# Fuel Oil Post: Gal fuel oil used if refit\n" +\
                "# HW District: HW  used \n" +\
                "# HW District Post: HW  used if refit\n" +\
                "# Narural Gas: natural gas used \n" +\
                "# Narural Gas Post: natural gas used if refit\n" +\
                "# Propane: Gal propane used \n" +\
                "# Propane Post: Gal propane used if refit\n" +\
                self.comments_dataframe_divide

    def interties_header (self):
        """
        """
        # original source compiled by AEA
        return  "# " + self.com_id + " intertied communities\n" +\
                "# generated: " + str(datetime.now()).split('.')[0] +"\n" +\
                "# Data Source: interties.csv \n" +\
                self.comments_dataframe_divide

    def region_header (self):
        """
        """
        # original sources?
        return  "# " + self.com_id + " regional information\n" +\
                "# generated: " + str(datetime.now()).split('.')[0] +"\n" +\
                "# Data Source: residenatial_data.csv \n" +\
                "# region: region used by model \n" +\
                "# Data Source: heating_fuel_premiums.csv\n" +\
                "# premium: heating fuel premium for region \n" +\
                self.comments_dataframe_divide

    def hdd_header (self):
        """ Function doc """
        return ("# " + self.com_id + " Heating Degree Days\n"
                "# generated: " + str(datetime.now()).split('.')[0] +"\n"
                "# Data Source: hdd.csv\n"
                "# HDD: heating degree-days per year for community (HDD/Yr)\n"
                "" + self.comments_dataframe_divide + "" )
                
    def propane_prices_header (self):
        """
        """
        return "# prices"
        

    ## PROCESS FUNCTIONS #######################################################
    def population (self, threshold = 20, end_year = 2040,
                          percent = .02, currnet_year = 2015):
        """
        create the population input file

        pre:
            in_file is the most current population file in the data-repo
            out dir is a path, com_id is a string ex "Adak"
        post:
            a file is saved, and the data frame it was generated from isreturned
        """
        in_file = os.path.join(self.data_dir,"population.csv")

        pop_data = read_csv(in_file, index_col = 0) # update to GNIS
        pop_source = "ICER's population forecast"
        try:
            pops = DataFrame(pop_data.ix[self.com_id]["2003":str(end_year)])
        except KeyError:
            in_file = os.path.join(self.data_dir,"population_neil.csv")
            pop_data = read_csv(in_file, index_col = 0) # update to GNIS
            pop_source = "Neil's Calculations"
            pops = DataFrame(pop_data.ix[self.com_id]["2003":str(end_year)])

        if (pops.values < threshold).any():
            self.diagnostics.add_warning("Population",
                                            "population < " + str(threshold))

        p = pops.T.values[0]
        k = pops.T.keys().values
        for idx in range(1,len(p)):
            #~ print idx
            hi = p[idx-1] * (1.0 + percent)
            lo = p[idx-1] * (1.0 - percent)
            if (p[idx] > hi or p[idx] < lo):
                self.diagnostics.add_note("Population",
                                            "population changes more than " +\
                                            str(percent * 100) + "% from " +\
                                            k[idx-1] +\
                                            " to " + k[idx])

        pops.columns  = ["population"]
        p_map=concat([pops[:str(currnet_year-1)].astype(bool).replace(True, "M"),
                      pops[str(currnet_year):].astype(bool).replace(True, "P")])
        p_map.columns  = [p_map.columns[0] + "_qualifier"]
        out_file = os.path.join(self.out_dir,"population.csv")
        fd = open(out_file,'w')
        fd.write(self.population_header(pop_source))
        fd.close()


        df = concat([pops,p_map],axis = 1)
        df.to_csv(out_file,mode="a")
        self.population_data = df
        self.population_data.index = self.population_data.index.astype(int)

    def wastewater (self):
        """
        preprocess wastewater data

        pre:
            data_file & assumptions_file are the most current wastewater and
        assumption files from the AAEM data repo. out dir is a path, com_id is
        a string ex "Adak"
        post:
            a file is saved in out_dir
        exceptions:
            raises a key error if the community is not in the waste water data
        or if the system type is unknown
        """
        data_file = os.path.join(self.data_dir,"ww_data.csv")
        assumptions_file =  os.path.join(self.data_dir,"ww_assumptions.csv")

        ## system type mapping From Neil
        ##Circulating/Gravity: Circulating/Gravity, Circulating/Pressure,
        ##                     Circulating/ST/DF
        ##Circulating/Vacuum: Circulating/Vacuum, Closed Haul/Vacuum
        ##Haul:  Closed Haul/Closed, Haul, Watering Point
        ##Pressure/Gravity: Pressure/Gravity, Pressure/NA, Pressure/ST/DF
        ##Washeteria/Honey Bucket: Washeteria
        ##None:  Wells/Gravity, Wells/NA, Wells/ST/DF, Wells/ST/OF

        sys_map = {
                    "Circulating/Gravity":"Circulating/Gravity",
                    "Circulating/Pressure":"Circulating/Gravity",
                    "Circulating/ST/DF":"Circulating/Gravity",
                    "Circulating/Vacuum":"Circulating/Vac",
                    "Closed Haul/Vacuum":"Circulating/Vac",
                    "Haul":"Haul",
                    "Closed Haul/Closed Haul":"Haul",
                    "Watering Point":"Haul",
                    "Pressure/Gravity": "Pressure/Gravity",
                    "Pressure/NA": "Pressure/Gravity",
                    "Pressure/ST/DF": "Pressure/Gravity",
                    "Washeteria":"Wash/HB",
                  }


        try:
            ww_d = read_csv(data_file, comment = '#',
                                                index_col = 0).ix[self.com_id]
        except KeyError:
            #~ raise StandardError, str(com_id) + " is not in " + data_file
            self.diagnostics.add_warning("Wastewater",
                                         "system not found, " + \
                                         "assuming zeros")
            ww_d = read_csv(data_file, comment = '#', index_col = 0).ix[-1]
            ww_d[:] = 0
            ww_d["System Type"] = "UNKNOWN"
            ww_d["HR Installed"] = False



        try:
            sys_type = sys_map[ww_d["System Type"]]
            ww_a = read_csv(assumptions_file, comment = '#', index_col = 0)
            ww_a = ww_a.ix[sys_type]
            ww_a["assumption type used"] = sys_type
            df = concat([ww_d,ww_a])
        except (KeyError, ValueError )as e:
            self.diagnostics.add_warning("wastewater",
                                         "system type unknown")
            ww_d['HDD kWh']	= 0.0
            ww_d['HDD HF'] = 0.0
            ww_d['pop kWh'] = 0.0
            ww_d['pop HF'] = 0.0

            ww_d["assumption type used"] = "UNKNOWN"
            #~ ww_d.to_csv(out_file, mode = 'a')
            df = ww_d

        out_file = os.path.join(self.out_dir,"wastewater_data.csv")
        fd = open(out_file,'w')
        fd.write(self.wastewater_header())
        fd.write("key,value\n")
        fd.close()

        #~ df = concat([ww_d,ww_a])
        df.to_csv(out_file, mode = 'a')
        self.wastewater_data = df

    def residential (self):
        """
        preprocess the residential data
        pre:
            fuel_file, data_file are files
            out_dir is a path
            com_id is a string
        post:
            residential data is in a file the model can use
        """
        data_file = os.path.join(self.data_dir, "res_model_data.csv")
        fuel_file = os.path.join(self.data_dir, "res_fuel_source.csv")

        fuel = read_csv(fuel_file, index_col=0, comment = "#").ix[self.com_id]
        fuel = fuel.ix[["Total", "Utility Gas", "LP", "Electricity", "Fuel Oil",
                        "Coal", "Wood", "Solar", "Other", "No fuel used"]]

        data = read_csv(data_file, index_col=0, comment = "#").ix[self.com_id]

        df = concat([data,fuel])
        del df.T["energy_region"]

        out_file = os.path.join(self.out_dir, "residential_data.csv")
        fd = open(out_file,'w')
        fd.write(self.residential_header())
        fd.write("key,value\n")
        fd.close()

        df.to_csv(out_file,mode="a")
        self.residential_data = df
        
        self.init_households = int(df.ix["total_occupied"])
        self.init_household_year = int(df.ix["year"])
        
        
    def residential_add_kWh_consumption_per_household(self):
        """
            add the average kWh/houshold consumption number to the residential
        input file
        
        pre:
            self.residential and self.electricity need to have been called
        post:
            kWh/houshold is added to res data output file
        """
        try:
            consumption_res = self.electricity_data["consumption residential"]\
                                               [self.init_household_year]
            average = consumption_res/ self.init_households 
        except AttributeError as e:
            average = "CALC_FOR_INTERTIE"
        except KeyError:
            average = np.nan
        if self.combined_com == True:
            average = "CALC_FOR_INTERTIE"
        #~ print average
        out_file = os.path.join(self.out_dir, "residential_data.csv")
        fd = open(out_file,'a')
        fd.write("average kWh per house,"+str(average)+'\n')
        fd.close()
        
        
        
        
        

    def region (self):
        """
        preprocess the regional input items
        pre:
            data_file, premium_file is are files
        post:
            regional related items are in a file the model can read
        """
        data_file = os.path.join(self.data_dir,"res_model_data.csv")
        premium_file = os.path.join(self.data_dir,"heating_fuel_premium.csv")

        region = read_csv(data_file, index_col=0,
                                        comment='#').energy_region[self.com_id]
        premium = read_csv(premium_file, index_col=0,
                                            comment='#').premium[region]

        out_file = os.path.join(self.out_dir, "region.csv")
        fd = open(out_file,'w')
        fd.write(self.region_header())
        fd.write("key,value \n")
        fd.write("region,"+ str(region) + "\n")
        fd.write("premium," + str(premium) + "\n")
        fd.close()


    def electricity(self):
        """
        """
        self.combined_com = False
        try:
            if self.com_id == "South Naknek":
                raise KeyError, "S. Naknek"
            self.electricity_process_pce()
            self.electricity_prices_pce()
        except KeyError:
            try:
                self.combined_com = False
                self.electricity_process_eia()
                self.electricity_prices_eia()
                # Valdez work around.
                if self.com_id == "Valdez":
                    val = os.path.join(self.data_dir,
                                                   "valdez_kwh_consumption.csv")
                    val = read_csv(val, comment = '#', index_col=0)
                    val["Total"] = val.sum(1)
                    val['non-res'] = val[['Commercial','Industrial']].sum(1)
                    val = concat([self.electricity_data,val],axis = 1)

                    val["consumption"] = val["Total"]
                    val["consumption residential"] = val["Residential"]
                    val["consumption non-residential"] = val["non-res"]
                    val = val[['generation','consumption',
                                             'fuel used', 'efficiency',
                                             'line loss', 'net generation',
                                             'consumption residential',
                                             'consumption non-residential',
                                             'kwh_purchased',
                                             'generation diesel',
                                             'generation hydro',
                                             'generation natural gas',
                                             'generation wind',
                                             'generation solar',
                                             'generation biomass']]
                    self.electricity_data = val
                    self.electricity_data["line loss"] = \
                                    1.0 - self.electricity_data['consumption']/\
                                         self.electricity_data['net generation']
                    out_file = os.path.join(self.out_dir,
                                              "yearly_electricity_summary.csv")

                    fd = open(out_file,'w')
                    fd.write(self.electricity_header("EIA"))
                    fd.close()

                    self.electricity_data.to_csv(out_file,mode="a")
                    self.p_key = None
                    self.diagnostics.add_note("Electricity",
                                                      "Valdez sales data added")
            except KeyError as e:
                #~ print e
                self.diagnostics.add_error("Electricity",
                        "Generation and Sales for " + str(self.com_id) +\
                        " data not in PCE or EIA")


    def electricity_prices_eia (self):
        """
        fuel prices EIA
        """
        #~ # TODO: find a way to calculate this
        con_file = os.path.join(self.data_dir, "eia_sales.csv")
        try:
            cid = self.com_id
            if cid == 'Glennallen' or cid == 'Valdez':
                cid = "Copper Valley"
            con_data = read_csv(con_file, comment='#', index_col=2).ix[cid]
        except KeyError:
            self.diagnostics.add_note("Electricity Prices (EIA)",
                                  "they need to be input in community data")
            return

        idx = con_data["Data Year"] == con_data["Data Year"].max()
        res_nonPCE_price = \
                        float(con_data[idx]['Residential Thousand Dollars']) /\
                        float(con_data[idx]['Residential Megawatthours'])

        elec_nonFuel_cost = float(con_data[idx]['Total Thousand Dollars']) /\
                           float(con_data[idx]['Total Megawatthours'])

        out_file = os.path.join(self.out_dir, "prices.csv")
        fd = open(out_file,'w')
        fd.write(self.electricity_prices_header("EIA"))
        fd.write("key,value \n")
        fd.write("res non-PCE elec cost,"+ str(res_nonPCE_price) + "\n")
        fd.write("elec non-fuel cost," + str(elec_nonFuel_cost) + "\n")
        fd.close()

    def electricity_prices_pce (self):
        """
        pre process fuel prices
        """
        in_file = os.path.join(self.data_dir,
                            "power-cost-equalization-pce-data.csv")
        data = read_csv(in_file, index_col=1, comment = "#")
        try:
            if self.com_id == "Craig":
                data = data.loc[["Craig","Craig, Klawock"]]
            else:
                data = data.ix[self.com_id]
        except KeyError:
            data = data.loc[[self.com_id+',' in s for s in data.index]]

        data = data[["year","month","residential_rate",
                     "pce_rate","effective_rate","residential_kwh_sold",
                                         "commercial_kwh_sold",
                                         "community_kwh_sold",
                                         "government_kwh_sold",
                                         "unbilled_kwh", "fuel_cost"]]

        last_year = data["year"].max()
        while len(data[data["year"] == last_year]) != 12:
            last_year -= 1


        elec_fuel_cost = (data[data["year"] == last_year]['fuel_cost'].mean()\
                     / data[data["year"] == last_year][["residential_kwh_sold",
                                         "commercial_kwh_sold",
                                         "community_kwh_sold",
                                         "government_kwh_sold",
                                         "unbilled_kwh"]].mean().sum())

        res_nonPCE_price = data[data["year"] == \
                                last_year]["residential_rate"].mean()
        elec_nonFuel_cost = res_nonPCE_price - elec_fuel_cost

        self.diagnostics.add_note("Electricity Prices PCE",
                                "calculated res non-PCE elec cost: " + \
                                 str(res_nonPCE_price))
        self.diagnostics.add_note("Electricity Prices PCE",
                                    "calculated elec non-fuel cost: " + \
                                    str(elec_nonFuel_cost))

        out_file = os.path.join(self.out_dir, "prices.csv")
        fd = open(out_file,'w')
        fd.write(self.electricity_prices_header("PCE"))
        fd.write("key,value \n")
        fd.write("res non-PCE elec cost,"+ str(res_nonPCE_price) + "\n")
        fd.write("elec non-fuel cost," + str(elec_nonFuel_cost) + "\n")
        fd.close()

    def electricity_process_eia (self):
        """
        pre process EIA electricity related values(generation, consumption, ...)
        """
        gen_file = os.path.join(self.data_dir, "eia_generation.csv" )
        con_file = os.path.join(self.data_dir, "eia_sales.csv")

        ## for sales
        cid = self.com_id
        if cid == 'Glennallen':
            cid = "Copper Valley"

        try:
            generation = read_csv(gen_file, comment = "#", index_col=3)\
                                        .loc[self.com_id] \
                                        [['Reported Fuel Type Code',
                                          'TOTAL FUEL CONSUMPTION QUANTITY',
                                          'ELECTRIC FUEL CONSUMPTION QUANTITY',
                                          'TOTAL FUEL CONSUMPTION MMBTUS',
                                          'ELEC FUEL CONSUMPTION MMBTUS',
                                          'NET GENERATION (megawatthours)',
                                          'Year']]
            if any(generation['NET GENERATION (megawatthours)'] < 0):
                self.diagnostics.add_note("EIA Electricity",
                    "Negative generation values have been set to 0")
                idx = generation['NET GENERATION (megawatthours)'] < 0
                generation['NET GENERATION (megawatthours)'][idx] = 0
            g_bool = True
        except KeyError:
            self.diagnostics.add_warning("EIA Electricity",
                                    "Generation Data not in EIA")
            g_bool = False

        try:
            sales = read_csv(con_file, comment = "#", index_col=2)\
                                                    .loc[cid]\
                                                  [["Data Year",
                                                    "Residential Megawatthours",
                                                    "Total Megawatthours"]]
            s_bool = True
        except KeyError:
            self.diagnostics.add_warning("EIA Electricity",
                                    "Consumption(sales) Data not in EIA")
            s_bool = False

        if not g_bool and not s_bool:
            raise KeyError, "Community not in EIA Data"

        # TODO add other fuel sources These two are from sitka example
        power_type_lib = {"WAT":"hydro",
                          "DFO":"diesel",
                          "WND":"wind",
                          "NG": "natural gas",
                          "WO":"bla",}

        if g_bool:
            gen_types = list(set(generation['Reported Fuel Type Code']))
            l = []
            for t in gen_types:
                temp = generation[generation['Reported Fuel Type Code'] == t].\
                                                           groupby('Year').sum()
                temp['generation ' + power_type_lib[t]] = \
                                 temp['NET GENERATION (megawatthours)'] * 1000.0

                temp2 = DataFrame(temp['generation ' + power_type_lib[t]])

                if power_type_lib[t] == "diesel":
                    temp2["fuel used"] = \
                                  temp['TOTAL FUEL CONSUMPTION QUANTITY'] * 42.0
                

                    
                l.append(temp2)
                
                
            fuel_types = concat(l, axis =1 )

            try:
                df_diesel = fuel_types[['generation diesel',"fuel used"]]
            except KeyError:
                df_diesel = DataFrame({"year":(2003,2004),
                        "generation diesel":(np.nan,np.nan),
                        "fuel used":(np.nan,np.nan)}).set_index('year')
            try:
                df_hydro = fuel_types[['generation hydro']]
            except KeyError:
                df_hydro = DataFrame({"year":(2003,2004),
                        "generation hydro":(np.nan,np.nan)}).set_index('year')
            try:
                df_gas = fuel_types[['generation natural gas']]
            except KeyError:
                df_gas = DataFrame({"year":(2003,2004),
                    "generation natural gas":(np.nan,np.nan)}).set_index('year')
            try:
                df_wind = fuel_types[['generation wind']]
            except KeyError:
                df_wind = DataFrame({"year":(2003,2004),
                        "generation wind":(np.nan,np.nan)}).set_index('year')
            try:
                df_solar = fuel_types[['generation solar']]
            except KeyError:
                df_solar = DataFrame({"year":(2003,2004),
                        "generation solar":(np.nan,np.nan)}).set_index('year')
            try:
                df_biomass = fuel_types[['generation biomass']].\
                                                               set_index('year')
            except KeyError:
                df_biomass = DataFrame({"year":(2003,2004),
                        "generation biomass":(np.nan,np.nan)}).set_index('year')

            total_generation = DataFrame(generation.groupby('Year').sum()\
                                     ['NET GENERATION (megawatthours)'])* 1000.0
            total_generation["net generation"] = \
                              total_generation['NET GENERATION (megawatthours)']
            
            try:
                total_generation["generation"] = total_generation["net generation"]+\
                      df_diesel['generation diesel'] * GENERATION_AVG
            except StandardError as w:
                print w
            
            self.diagnostics.add_note("EIA Electricity",
                        "Gross Generation assumed to be " +\
                         str((1+GENERATION_AVG)*100) + " of net generation")

        else:
            total_generation = DataFrame({"year":(2003,2004),
                    "generation":(np.nan,np.nan),
                    "net generation":(np.nan,np.nan)}).set_index('year')
            df_diesel = DataFrame({"year":(2003,2004),
                    "generation diesel":(np.nan,np.nan),
                    "fuel used":(np.nan,np.nan)}).set_index('year')
            df_hydro = DataFrame({"year":(2003,2004),
                    "generation hydro":(np.nan,np.nan)}).set_index('year')
            df_gas = DataFrame({"year":(2003,2004),
                    "generation natural gas":(np.nan,np.nan)}).set_index('year')
            df_wind = DataFrame({"year":(2003,2004),
                    "generation wind":(np.nan,np.nan)}).set_index('year')
            df_solar = DataFrame({"year":(2003,2004),
                    "generation solar":(np.nan,np.nan)}).set_index('year')
            df_biomass = DataFrame({"year":(2003,2004),
                    "generation biomass":(np.nan,np.nan)}).set_index('year')

        if s_bool:
            sales["consumption"] = sales["Total Megawatthours"] * 1000
            sales['consumption residential'] = \
                                       sales["Residential Megawatthours"] * 1000
            sales['consumption non-residential'] = sales['consumption'] - \
                                                sales['consumption residential']
            sales['year'] = sales["Data Year"]
            sales = sales[['year',"consumption",
                           'consumption residential',
                           'consumption non-residential']].set_index('year')
            if cid == "Copper Valley":
                val = os.path.join(self.data_dir, "valdez_kwh_consumption.csv")
                val = read_csv(val, comment = '#', index_col=0)
                val["Total"] = val.sum(1)
                val['non-res'] = val[['Commercial','Industrial']].sum(1)
                #~ val = concat([self.electricity_data,val],axis = 1)

                val["consumption"] = val["Total"]
                val["consumption residential"] = val["Residential"]
                val["consumption non-residential"] = val["non-res"]
                val = val[["consumption","consumption residential",
                           "consumption non-residential"]]
                sales = sales - val
        else:
            sales = DataFrame({"year":(2003,2004),
                    "consumption":(np.nan,np.nan),
                    "consumption residential":(np.nan,np.nan),
                    "consumption non-residential":(np.nan,np.nan)})\
                                                        .set_index('year')

        electricity = concat([total_generation,sales,df_diesel,df_hydro,
                                            df_gas,df_wind,df_solar,df_biomass],
                                                                       axis = 1)

        electricity['line loss'] = 1.0 - electricity['consumption']/\
                                                electricity['net generation']

        electricity['efficiency'] = electricity['generation diesel'] / \
                                                    electricity['fuel used']
        # I want some zeros
        electricity['kwh_purchased'] = electricity['generation'] -\
                                                electricity['generation']

        self.electricity_data = electricity[['generation','consumption',
                                             'fuel used', 'efficiency',
                                             'line loss', 'net generation',
                                             'consumption residential',
                                             'consumption non-residential',
                                             'kwh_purchased',
                                             'generation diesel',
                                             'generation hydro',
                                             'generation natural gas',
                                             'generation wind',
                                             'generation solar',
                                             'generation biomass']]
        out_file = os.path.join(self.out_dir, "yearly_electricity_summary.csv")

        fd = open(out_file,'w')
        fd.write(self.electricity_header("EIA"))
        fd.close()

        self.electricity_data.to_csv(out_file,mode="a")
        self.p_key = None

    def electricity_process_pce (self):
        """
        pre process PCE electricity related values(generation, consumption, ...)
        """
        ## set up files
        lib_file = os.path.join(self.data_dir, "purchased_power_lib.csv")
        in_file = os.path.join(self.data_dir,
                                "power-cost-equalization-pce-data.csv")
        ## Load Data
        data = read_csv(in_file, index_col=1, comment = "#")
        try:
            if self.com_id == "Craig":
                data = data.loc[["Craig","Craig, Klawock"]]
                self.combined_com = True
            else:
                data = data.loc[self.com_id]
        except KeyError:
            try:
                data = data.loc[[self.com_id+',' in s for s in data.index]]
                if self.intertied:
                    self.combined_com = True
            except KeyError:
                raise KeyError, "Community not in PCE data"
        data = data[["year","diesel_kwh_generated",
                     "powerhouse_consumption_kwh",
                     "hydro_kwh_generated",
                     "other_1_kwh_generated","other_1_kwh_type",
                     "other_2_kwh_generated","other_2_kwh_type",
                     'purchased_from','kwh_purchased',
                     "fuel_used_gal",
                     "residential_kwh_sold",
                     "commercial_kwh_sold",
                     "community_kwh_sold",
                     "government_kwh_sold",
                     "unbilled_kwh"]]
        #~ print data
        ## Load Purchased from library
        try:
            lib = read_csv(lib_file, index_col=0, comment = '#')
            try:
                if self.com_id == "Craig":
                    data = data.loc[["Craig","Craig, Klawock"]]
                else:
                    data = data.loc[self.com_id]
            except KeyError:
                lib = lib.loc[[self.com_id+',' in s for s in lib.index]]
        except:
             self.diagnostics.add_note("PCE Electricity",
             "Reading purchased from no utilities listed for community")

        ## Determine if and what kind of power is purchased
        try:
            sources = sorted(set(data[data["purchased_from"].notnull()]\
                                                ["purchased_from"].values))

            self.diagnostics.add_note("PCE Electricity",
                        "Utility list (alphabetized) for purchased power" + \
                        str(sources) )
            #~ print sources
            for s in sources:
                try:
                    p_key = lib[lib['purchased_from'] == s]\
                                        ['Energy Source'].values[0].lower()
                    provider = s
                except IndexError as e:
                    self.diagnostics.add_warning("PCE Electricity",
                                            "Utility " + s + \
                                            " not found in utility-power "+\
                                            "source lib not using as provider")
            self.diagnostics.add_note("PCE Electricity",
                          "Purchased from utility: " + str(s))
            self.diagnostics.add_note("PCE Electricity",
                          "Purchased energy type: " + str(p_key))
        except:
            l = len(data["purchased_from"][data["purchased_from"].notnull()])
            if l != 0:
                self.diagnostics.add_warning("PCE Electricity",
                        "Power was found to be purchased, " + \
                        "but the source or type of power could not be found")
            else:
               self.diagnostics.add_note("PCE Electricity",
                                                "No Purchased Power")
            p_key = None

        ## Determine if and what kind of power is other_1
        try:
            sources = list(data[data["other_1_kwh_type"].notnull()]\
                                        ["other_1_kwh_type"].values)
            s_set = sorted(set(sources))
            if len(s_set) == 1:
                o1_key = sources[0]
                self.diagnostics.add_note("PCE Electricity",
                        "other energy 1 type: " + str(o1_key) )
            elif len(s_set) > 1:
                o1_key = sources[0].lower()
                l = len([i for i, x in enumerate(sources) if x == o1_key])
                for k in s_set:
                    if len([i for i, x in enumerate(sources) if x == k]) > l:
                        o1_key = k.lower()

                self.diagnostics.add_warning("PCE Electricity",
                        "other energy 1 type: " + str(o1_key) + \
                        ", as it wasthe most common energy source amoung " + \
                        str(s_set) )


            if o1_key not in ('diesel', 'natural gas','wind', 'solar'):
                self.diagnostics.add_warning("PCE Electricity",
                "energy source key " + str(o1_key) + \
                                    " not recognized. Ignoring")
                o1_key = None
        except:
            o1_key = None

        ## Determine if and what kind of power is in other_2
        try:
            sources = list(data[data["other_2_kwh_type"].notnull()]\
                                        ["other_2_kwh_type"].values)
            s_set = sorted(set(sources))
            if len(s_set) == 1:
                o2_key = sources[0]
                self.diagnostics.add_note("PCE Electricity",
                        "other energy 1 type: " + str(o2_key) )
            elif len(s_set) > 1:
                o2_key = sources[0].lower()
                l = len([i for i, x in enumerate(sources) if x == o2_key])
                for k in s_set:
                    if len([i for i, x in enumerate(sources) if x == k]) > l:
                        o2_key = k.lower()

                self.diagnostics.add_warning("PCE Electricity",
                        "other energy 1 type: " + str(o2_key) + \
                        ", as it wasthe most common energy source amoung " + \
                        str(s_set) )


            if o2_key not in ('diesel', 'natural gas','wind', 'solar'):
                self.diagnostics.add_warning("PCE Electricity",
                "energy source key " + str(o2_key) + \
                                    " not recognized. Ignoring")
                o2_key = None
        except:
            o2_key = None


        ## create yearly summaries
        sums = []
        for year in set(data["year"].values):
            #take full years only
            if len(data[data["year"] == year]) != 12:
                continue
            ## sum of every value for the year
            temp = data[data["year"] == year].sum()
            ## get year as int
            temp["year"] = int(year)
            ## get gross generation
            temp['generation'] = temp[['diesel_kwh_generated',
                                        "powerhouse_consumption_kwh",
                                        "hydro_kwh_generated",
                                        "other_1_kwh_generated",
                                        "other_2_kwh_generated",
                                        "kwh_purchased"]].sum()
            ## get generation by fuel type
            temp['generation diesel'] = temp['diesel_kwh_generated']
            temp['generation hydro'] = temp['hydro_kwh_generated']
            ## for other 1
            if np.isreal(temp["other_1_kwh_generated"]) and o1_key is not None:
                val = temp["other_1_kwh_generated"]
                if o1_key == "diesel":
                    temp['generation diesel'] = temp['generation diesel'] + val
                else:
                    temp['generation ' + o1_key] = val
            ## for other 2
            if np.isreal(temp["other_2_kwh_generated"]) and o2_key is not None:
                val =  temp["other_2_kwh_generated"]
                if o2_key == "diesel":
                    temp['generation diesel'] = temp['generation diesel'] + val
                else:
                    temp['generation ' + o2_key] = val
            ## for purchased
            if np.isreal(temp["kwh_purchased"]) and p_key is not None:
                val = temp['kwh_purchased']
                if p_key == "diesel":
                    temp['generation diesel'] = temp['generation diesel'] + val
                else:
                    temp['generation ' + p_key] = val

            ## get consumption (sales) total & by type
            temp['consumption'] = temp[["residential_kwh_sold",
                                        "commercial_kwh_sold",
                                        "community_kwh_sold",
                                        "government_kwh_sold",
                                        "unbilled_kwh"]].sum().sum()
            temp['consumption residential'] = temp["residential_kwh_sold"].sum()
            temp['consumption non-residential'] = temp['consumption'] - \
                                                 temp['consumption residential']
            ## net generation
            phc = temp["powerhouse_consumption_kwh"]
            if np.isnan(phc):
                phc = temp['generation diesel'] * GENERATION_AVG
                self.diagnostics.add_note("PCE Electricity",
                        "Powerhouse consumption not found for " + \
                        str(year) +" assuming to be " +\
                        str(GENERATION_AVG*100) + "% of gross generation.")
                temp['net generation'] = temp['generation'] 
                temp['generation'] = temp['generation'] + phc
            else:
                temp['net generation'] = temp['generation'] - phc

            ## other values
            temp['fuel used'] = temp['fuel_used_gal']
            temp['line loss'] = 1.0 - temp['consumption']/temp['net generation']
            temp['efficiency'] = temp['generation'] / temp['fuel_used_gal']
            sums.append(temp)

        ## pull out diesel & hydro
        df_diesel = DataFrame(sums)[["year",
                                        'generation diesel']].set_index('year')
        df_hydro = DataFrame(sums)[["year",
                                    'generation hydro']].set_index('year')
        ## pull out or create, other fuel sources
        try:
            df_gas = DataFrame(sums)[["year",
                                    'generation natural gas']].set_index('year')
        except KeyError:
            df_gas = DataFrame({"year":(2003,2004),
                    "generation natural gas":(np.nan,np.nan)}).set_index('year')
        try:
            df_wind = DataFrame(sums)[["year",
                                       'generation wind']].set_index('year')
        except KeyError:
            df_wind = DataFrame({"year":(2003,2004),
                        "generation wind":(np.nan,np.nan)}).set_index('year')
        try:
            df_solar = DataFrame(sums)[["year",
                                        'generation solar']].set_index('year')
        except KeyError:
            df_solar = DataFrame({"year":(2003,2004),
                        "generation solar":(np.nan,np.nan)}).set_index('year')
        try:
            df_biomass = DataFrame(sums)[["year",'generation biomass']]\
                                                            .set_index('year')
        except KeyError:
            df_biomass = DataFrame({"year":(2003,2004),
                        "generation biomass":(np.nan,np.nan)}).set_index('year')

        ## data frame for all values
        df = DataFrame(sums)[['year','generation','consumption','fuel used',
                              'efficiency', 'line loss', 'net generation',
                              'consumption residential',
                              'consumption non-residential',
                              "kwh_purchased"]].set_index("year")
        df = concat([df,df_diesel,df_hydro,df_gas,df_wind,df_solar,df_biomass],
                                                                       axis = 1)
        ## save
        out_file = os.path.join(self.out_dir, "yearly_electricity_summary.csv")

        fd = open(out_file,'w')
        fd.write(self.electricity_header())
        fd.close()

        df.to_csv(out_file,mode="a")

        self.electricity_data = df
        self.purchase_type = p_key

    def interties (self):
        """
        preprocess interties

        pre:
            in_infile is the intertie data file
            out_dir is a directory
            com_id is a string
        post
            com_id's intertie data is saved to out_dir as interties.csv
        """
        self.intertied = False 
        try:
            in_file = os.path.join(self.data_dir,"interties.csv")
            data = read_csv(in_file, index_col=0,
                            comment = "#").ix[self.com_id].fillna("''")
            if data['Plant Intertied'] == 'Yes' and \
               data['Other Community on Intertie'] != "''":
                self.intertied = True
            out_file = os.path.join(self.out_dir, "interties.csv")
            fd = open(out_file,'w')
            fd.write(self.interties_header())
            fd.close()
            data.to_csv(out_file, mode = 'a')
            self.it_ids = data
            return data

        except KeyError:
            self.diagnostics.add_note("Interties",
                                                    "no intertie on community")
        

    def buildings_count (self):
        """
        Function doc
        """
        count_file = os.path.join(self.data_dir,"com_num_buildings.csv")
        try:
            data = int(read_csv(count_file ,comment = "#", index_col = 0,
                                                 header = 0).ix[self.com_id])

        except KeyError:
            try:
                data = read_csv(count_file ,comment = "#", index_col = 0,
                                                                    header = 0)
                #~ print data.index.astype(str)
                data = data.loc\
                        [[self.com_id  in s for s in data.index.astype(str)]]
                data = data.values[0][0]
            except (KeyError, IndexError):

                data = 0
                self.diagnostics.add_note("buildigns(count)",
                        "Community " + self.community + \
                        " does not have an entry in the input data, using 0")

        out_file = os.path.join(self.out_dir, "com_num_buildings.csv")
        fd = open(out_file,'w')
        fd.write(self.buildings_count_header())
        fd.write("key, value\n")
        fd.write("Buildings," + str(data) +"\n")
        fd.close()

        self.buildigns_count_data = data


    def buildings_estimates(self, pop):
        """
        """
        est_file = os.path.join(self.data_dir,"com_building_estimates.csv")
        data = read_csv(est_file ,comment = u"#",index_col = 0, header = 0)

        units = set(data.ix["Estimate units"])
        l = []
        for itm in units:
            l.append(data.T[data.ix["Estimate units"] == itm]\
                          [(data.T[data.ix["Estimate units"] == itm]\
                          ["Lower Limit"].astype(float) <= pop)]\
                          [data.ix["Estimate units"] == itm]\
                          [(data.T[data.ix["Estimate units"] == itm]\
                          ["Upper Limit"].astype(float) > pop)])

        df = concat(l).set_index("Estimate units")
        del(df["Lower Limit"])
        del(df["Upper Limit"])
        #~ del(df["Estimate units"])
        df = df.T

        out_file = os.path.join(self.out_dir, "com_building_estimates.csv")
        fd = open(out_file,'w')
        fd.write(self.buildings_estimates_header(pop))
        fd.close()
        df.to_csv(out_file,mode="a",index_label="building type")
        self.buildings_estimates_data = df

    def buildings_inventory (self):
        """
        """
        in_file = os.path.join(self.data_dir,"non_res_buildings.csv")
        try:
            data = read_csv(in_file, index_col=1, comment = "#")
            #~ data = data[data.index == self.com_id]
            data = self.get_communities_data(data)

            l = ["Square Feet","implementation cost",
                 "Electric", "Electric Post",
                 "Fuel Oil", "Fuel Oil Post",
                 "HW District", "HW District Post",
                 "Natural Gas", "Natural Gas Post",
                 "Propane", "Propane Post"]
            data[l] = data[l].replace(r'\s+', np.nan, regex=True)
            

            c = ["Building Type", "Square Feet",
                 "Audited", "Retrofits Done",
                 "implementation cost",
                 "Electric", "Electric Post",
                 "Fuel Oil", "Fuel Oil Post",
                 "HW District", "HW District Post",
                 "Natural Gas", "Natural Gas Post",
                 "Propane", "Propane Post"]
            out_file = os.path.join(self.out_dir, "community_buildings.csv")
            fd = open(out_file,'w')
            fd.write(self.buildings_inventory_header())
            fd.close()
            data[c].to_csv(out_file, mode="a", index=False)
            self.buildings_inventory_data = data[c]
        except KeyError as e :
            self.diagnostics.add_error("buildings(inventory)",
                                "Community " + self.community + \
                                " does not have an entry in the input data" +\
                                " cannot generate model input file "+\
                                "'community_buildings.csv'" )
            self.buildings_inventory_data = None
            out_file = os.path.join(self.out_dir, "community_buildings.csv")
            fd = open(out_file,'w')
            fd.write(self.buildings_inventory_header())
            fd.write('"Building Type","Square Feet","Audited",'
                     '"Retrofits Done","implementation cost","Electric",'
                     '"Electric Post","Fuel Oil","Fuel Oil Post",'
                     '"HW District","HW District Post","Natural Gas",'
                     '"Natural Gas Post","Propane","Propane Post"\n')
            fd.close()


    def buildings (self, population):
        """ Function doc """
        self.buildings_count()
        self.buildings_estimates(population)
        self.buildings_inventory()

    def hdd (self):
        """ Function doc """
        in_file = os.path.join(self.data_dir, "hdd.csv")
        hdd = read_csv(in_file, index_col=0,
                       comment = "#", header=0).ix[self.com_id].values[0]
        out_file = os.path.join(self.out_dir, "hdd.csv")
        fd = open(out_file,'w')
        fd.write(self.hdd_header())
        fd.write("key, value\n")
        fd.write("HDD," + str(hdd) +"\n")
        fd.close()

    def prices (self):
        """
        """
        out_file = os.path.join(self.out_dir, "prices_non-electric_fixed.csv")
        fd = open(out_file,'w')
        fd.write(self.hdd_header())
        fd.write("fuel, price\n")
        fd.write("Propane," + str(self.prices_propane()) +"\n")
        fd.write("Biomass," + str(self.prices_biomass()) +"\n")
        fd.close()
        
        
        ## update the way diesel works at some point
        #~ self.prices_diesel()
        

    def prices_propane (self):
        """
        """
        #~ print self.com_id
        in_file = os.path.join(self.data_dir, "propane_price_estimates.csv")
        data = read_csv(in_file, index_col=0,comment = "#", header=0)
        if len(self.get_communities_data(data)['Source'])==0:
            self.diagnostics.add_warning("prices-propane", "not found")
            return 0
            
        self.diagnostics.add_note("prices-propane", "price source: " +\
                      str(self.get_communities_data(data)['Source']))
        return float(self.get_communities_data(data)['Propane ($/gallon)'])
        
    def prices_diesel (self):
        """
        """
        in_file = os.path.join(self.data_dir, "diesel_fuel_prices.csv")
        data = read_csv(in_file, index_col=3, comment="#", header=0)
        data = self.get_communities_data(data)
        try:
            keys = data.keys()[3:]
            data = np.array(data.values[0][3:], dtype = np.float64)
       
        except IndexError:
            data = read_csv(in_file, index_col=3, comment="#", header=0)
            keys = data.keys()[3:]
            data = np.array(data.mean().values[2:], dtype = np.float64)
            
        return DataFrame({"year":keys,"price diesel":data}).set_index("year")
    
    def prices_biomass (self):
        """
        """
        in_file = os.path.join(self.data_dir, "biomass_price_estimates.csv")
        data = read_csv(in_file, index_col=0,comment = "#", header=0)
        
        if len(self.get_communities_data(data)['Source'])==0:
            self.diagnostics.add_warning("prices-biomass", "not found")
            return 0
        self.diagnostics.add_warning("prices-biomass", "price source: " +\
                      str(self.get_communities_data(data)['Source']))
        try:
            val = float(self.get_communities_data(data)['Biomass ($/Cord)'])         
        except ValueError:
            self.diagnostics.add_note("prices-biomass", 
                                        "is N/a treating as $0")
            val = 0
        if np.isnan(val):
            self.diagnostics.add_note("prices-biomass", 
                                        "is N/a treating as $0")
            val = 0 
        return val
        
    def get_communities_data(self, dataframe):
        """
            pull the data for a community out of a data frame with multiple 
        communities. 
        """
        #~ dataframe = dataframe.ix[self.id_list]
        #~ print self.id_list
        #~ print dataframe
        
        #~ return dataframe.ix[dataframe.index[dataframe.T.any()]]  
        for idx in self.id_list:
            try:
                temp = DataFrame(dataframe.ix[idx])
                if len(temp.T) == 1:
                    return temp.T
                return temp
            except (IndexError, KeyError) as e:
                continue
        return dataframe.ix[-1]
    
    def load_ids (self):
        """
            for a community get a list of alternate id's and potential synonyms 
        for the id.
        """
        in_file = os.path.join(self.data_dir, "community_list.csv")
        data = read_csv(in_file, comment = '#')
        ids = data.ix[data.index[data.T[data.T==self.com_id].any()]]
        region = ids['Energy Region'].values[0]
        ids = ids[ids.keys()[ids.keys()!='Energy Region']].set_index("Model ID")
        self.energy_region = region
        self.id_df = ids
        self.id_list = ids.values[0].tolist()

def preprocess (data_dir, out_dir, com_id, dev = False):
    """ Function doc """
    #print com_id
    diag = diagnostics()

    pp = preprocess_no_intertie(data_dir,
                        os.path.join(out_dir,com_id.replace(" ","_")), com_id,
                                                                    diag, dev)
    try:
        if pp.it_ids["Plant Intertied"].lower() == "yes":

            ids = pp.it_ids[['Other Community on Intertie',
                             'Other Community on Intertie.1',
                             'Other Community on Intertie.2',
                             'Other Community on Intertie.3',
                             'Other Community on Intertie.4',
                             'Other Community on Intertie.5',
                             'Other Community on Intertie.6'
                           ]].values
            ids = ids[ids != "''"].tolist()


            ids = [com_id] + ids

            if len(ids) >1 :
                diag = diagnostics()
                diag.add_note("preprocessor",
                                 "Includes dianostis for " + str(ids))
                pp = preprocess_intertie(data_dir, out_dir, ids, diag)

            pp = ids
        else:
            pp = [com_id]
    except AttributeError:
        pp = [com_id]

    diag.save_messages(os.path.join(out_dir,
                               str(com_id.replace(" ","_")) + "_preprocessor_diagnostis.csv"))
    return pp




def preprocess_no_intertie (data_dir, out_dir, com_id, diagnostics, dev = False):
    """
    """
    if os.path.exists(os.path.join(out_dir))and not dev:
        return False
    pp = Preprocessor(com_id, data_dir,out_dir, diagnostics)
    pp.preprocess()
    
    copied_data = { "yearly electric summary":False,
                    "interties" : False,
                    'prices': False,
                    'HDD': False
                }
    
    f_path = os.path.join(out_dir,'copies.csv')
    if not os.path.exists(f_path):
    
        fd = open(f_path,'w')
        fd.write("# a list of copied data for the child community")
        fd.close()
        DataFrame(copied_data,["copied"]).T.to_csv(f_path,mode='a')
    
    
   
    return pp

def preprocess_intertie (data_dir, out_dir, com_ids, diagnostics):
    """ Function doc """
    parent = com_ids[0]
    pp_data = []
    parent_dir = os.path.join(out_dir, parent.replace(" ","_"))
    #~ print com_ids
    for com in com_ids:

        #~ print com
        pp = Preprocessor(com, data_dir,os.path.join(out_dir,
                                            com.replace(" ","_")), diagnostics)
        pp.preprocess()
        pp_data.append(pp)
        
        
        copied_data = { "yearly electric summary":False,
                    "interties":False,
                    'prices':False,
                    'HDD' :False
                }

        f_path = os.path.join(out_dir,com.replace(" ","_"),
                                            "yearly_electricity_summary.csv")
        if com != parent and not os.path.exists(f_path):
            #print com + " adding data - electricity"
            shutil.copy(os.path.join(parent_dir,
                                    "yearly_electricity_summary.csv")
                                    ,os.path.join(out_dir,com.replace(" ","_")))
            copied_data["yearly electric summary"] = True
            diagnostics.add_warning("Intertie update (electricity)",
                                    ("" + com + " is using it's "
                                     "parent's (" + parent + ""
                                     ") yearly_electricity_summary"))

        f_path = os.path.join(out_dir, com, "prices.csv")
        if com != parent and not os.path.exists(f_path):
            #print com + " adding data- prices"
            shutil.copy(os.path.join(parent_dir,
                                    "prices.csv")
                                    ,os.path.join(out_dir,com.replace(" ","_")))
            copied_data["prices"] = True
            diagnostics.add_warning("Intertie update (prices)",
                                    ("" + com + " is using it's "
                                     "parent's (" + parent + ""
                                     ") prices"))
                                     
        if com != parent and os.path.exists(f_path):
            #~ print com
            p_file = os.path.join(parent_dir, "prices.csv")
            parent_prices = read_csv(p_file, comment = '#', index_col = 0)
            prices = read_csv(f_path, comment = '#', index_col = 0)
            for i in prices.index:
                val = float(parent_prices.ix[i])
                if np.isnan(float(prices.ix[i])):
                    prices.ix[i] = val
                    diagnostics.add_warning("Intertie update (prices )",
                                    ("" + com + " is using it's "
                                     "parent's (" + parent + ""
                                     ") " + str(i)))
            
            fd = open(f_path, 'r')
            text = ""
            while True:
                l = fd.readline()    
                if l[0] != '#':
                    break
                text += l 
            fd.close()
            fd = open(f_path, 'w')
            fd.write(text)
            fd.close()
            prices.to_csv(f_path,mode='a')
            
            
                
        f_path = os.path.join(out_dir,com,"hdd.csv")
        if com != parent and not os.path.exists(f_path):
            #print com + " adding data- hdd"
            copied_data["HDD"] = True
            shutil.copy(os.path.join(parent_dir,
                                    "hdd.csv")
                                    ,os.path.join(out_dir,com.replace(" ","_")))
            diagnostics.add_warning("Intertie update (HDD)",
                                    ("" + com + " is using it's "
                                     "parent's (" + parent + ""
                                     ") Heating degree days "))

        f_path = os.path.join(out_dir,com.replace(" ","_"),"interties.csv")
        if com != parent and not os.path.exists(f_path):
            #print com + " adding data - electricity"
            shutil.copy(os.path.join(parent_dir,
                                    "interties.csv")
                                    ,os.path.join(out_dir,com.replace(" ","_")))
            copied_data["interties"] = True
            diagnostics.add_warning("Intertie update (interties)",
                                    ("" + com + " has copy of parents intertie"
                                     " info(interties.csv)" ))
    
        # save which files were copied
        f_path = os.path.join(out_dir,com.replace(" ","_"),'copies.csv')
        fd = open(f_path,'w')
        fd.write("# a list of copied data for the child community")
        fd.close()
        
        DataFrame(copied_data,["copied"]).T.to_csv(f_path,mode='a')
    
    
    # for intertie
    #   generation = generation(parent) +
    #             (generation(child) - kWh_purchased(child)) for each child
    #   net_generation = net_generation(parent) +
    #             (net_generation(child) - kWh_purchased(child)) for each child
    #
    #   for consumption[res, non-res, total] & generation by fuel type
    #       field = field(parent) +
    #                   (field (child) - kWh_purchased(child)) for each child
    #
    #   line loss = consumption(intertie) / net generation(intertie)

    # make Deep copy of parent city
    population = pp_data[0].population_data.copy(True)
    electricity = pp_data[0].electricity_data.copy(True)
    for idx in range(len(pp_data)):
        if idx == 0:
            continue

        population['population'] = population['population'] + \
                                    pp_data[idx].population_data['population']

        #   try, except for communities that don't exist on their own such as
        # oscarville, which is bethel,oscarville
        try:
            temp = pp_data[idx].electricity_data
            electricity['generation'] = electricity['generation'].fillna(0) +\
                (temp['generation'].fillna(0) - temp['kwh_purchased'].fillna(0))
            electricity['net generation'] = \
                        electricity['net generation'].fillna(0) +\
                            (temp['net generation'].fillna(0) - \
                                temp['kwh_purchased'].fillna(0))
            for key in ['consumption', 'consumption residential',
                        'consumption non-residential', 'generation diesel',
                        'generation hydro', 'generation natural gas',
                        'generation wind', 'generation solar',
                        'generation biomass',
                       ]:
                #~ print "loop"
                try:
                    if pp_data[idx].purchase_type == key.split(' ')[1]:
                        electricity[key] = electricity[key].fillna(0) + \
                            (temp[key].fillna(0) - \
                                temp['kwh_purchased'].fillna(0))
                        continue
                except (IndexError, AttributeError):
                    electricity[key] = electricity[key].fillna(0) + \
                                                            temp[key].fillna(0)
                #~ print key
                #~ print electricity[key]
        except AttributeError:
            pass
    electricity['line loss'] = 1.0 - \
                        electricity['consumption']/electricity['net generation']

    total_HH = 0 
    for idx in range(len(pp_data)):
        com = pp_data[idx].com_id
        total_HH += pp_data[idx].init_households
        
    consumption_res = electricity["consumption residential"]\
                                               [pp_data[0].init_household_year]
    average = consumption_res/total_HH
    for com in com_ids:
        f_path = os.path.join(out_dir,com.replace(" ","_"),
                                                "residential_data.csv")

        fd = open(f_path,"r")
        text = fd.read()
        fd.close()
        
        if text.find("CALC_FOR_INTERTIE") == -1:
            continue
            
        diagnostics.add_note("Intertie update (Res avg kWh/household)",
                                ("" + com + " is using the intertie value of"
                                " " + str(average) + " for KWh/household"))
        text = text.replace("CALC_FOR_INTERTIE",str(average))
        fd = open(f_path,"w")
        fd.write(text)
        fd.close()
    

    out_dir = os.path.join(out_dir,com_ids[0].replace(" ","_") +'_intertie')
    try:
            os.makedirs(out_dir)
    except OSError:
            pass


    diagnostics.add_note("Intertie (population)",
        "the intertie population is the sum of all populations on intertie")
    out_file = os.path.join(out_dir, 'population.csv')
    population.to_csv(out_file)

    diagnostics.add_note("Intertie(yearly_electricity_summary)",
        ("for generation and consumption values in intertie: "
         "value = value(parent) + (value(child) - "
         "kWh_purchased(child)) for each child"))
    diagnostics.add_note("Intertie(yearly_electricity_summary)",
        "Line Loss is recalulated from new totals")
    out_file = os.path.join(out_dir,'yearly_electricity_summary.csv')
    electricity.to_csv(out_file)

    

    diagnostics.add_note("Intertie(diesel_fuel_prices)", "from parent")
    shutil.copy(os.path.join(parent_dir,"diesel_fuel_prices.csv"), out_dir)
    diagnostics.add_note("Intertie(hdd)", "from parent")
    shutil.copy(os.path.join(parent_dir,"hdd.csv"), out_dir)
    diagnostics.add_note("Intertie(cpi)", "from parent (constant for state)")
    shutil.copy(os.path.join(parent_dir,"cpi.csv"), out_dir)
    diagnostics.add_note("Intertie(com_bulding_estimates)", "from parent")
    shutil.copy(os.path.join(parent_dir,"com_building_estimates.csv"), out_dir)
    diagnostics.add_note("Intertie(community_buildigns)", "from parent")
    shutil.copy(os.path.join(parent_dir,"community_buildings.csv"), out_dir)
    diagnostics.add_note("Intertie(com_num_buildings)", "from parent")
    shutil.copy(os.path.join(parent_dir,"com_num_buildings.csv"), out_dir)
    diagnostics.add_note("Intertie(interties)", "from parent")
    shutil.copy(os.path.join(parent_dir,"interties.csv"), out_dir)
    diagnostics.add_note("Intertie(prices)", "from parent")
    shutil.copy(os.path.join(parent_dir,"prices.csv"), out_dir)
    diagnostics.add_note("Intertie(region)", "from parent")
    shutil.copy(os.path.join(parent_dir,"region.csv"), out_dir)
    diagnostics.add_note("Intertie(residential_dat)", "from parent")
    shutil.copy(os.path.join(parent_dir,"residential_data.csv"), out_dir)
    diagnostics.add_note("Intertie(wastewater_data)", "from parent")
    shutil.copy(os.path.join(parent_dir,"wastewater_data.csv"), out_dir)
    shutil.copy(os.path.join(parent_dir,
            MODEL_FILES["PRICES_NONELECTRIC"]),out_dir)                  
    shutil.copy(os.path.join(parent_dir,
            MODEL_FILES["COPIES"]),out_dir)    

    return pp_data
