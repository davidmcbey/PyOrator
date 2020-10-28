#-------------------------------------------------------------------------------
# Name:        ora_livestock_model.py
# Purpose:     functions for livestock model
# Author:      Dave Mcbey
# Created:     03/08/2020
# Licence:     <your licence>
# defs:
#   test_livestock_algorithms
#
# Description:
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_livestock_model.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import os
from pandas import DataFrame
from ora_excel_read import read_livestock_data, read_livestock_supp_data, read_africa_animal_prod
from ora_crop_model import test_crop_algorithms


def test_livestock_algorithms(form):

    xls_inp_fname = os.path.normpath(form.w_lbl13.text())
    if not os.path.isfile(xls_inp_fname):
        print('Excel input file ' + xls_inp_fname + 'must exist')
        return

    # Use functions to create dataframe/feed_avail_dic with data from ORATOR excel inputs
    lv_data = read_livestock_data(xls_inp_fname)
    supp_info = read_livestock_supp_data(xls_inp_fname)
    an_prod = read_africa_animal_prod(xls_inp_fname)

    # Dictionary to give neatly formatted name for each livestock type (so it can be saved easily)
    form_name_dic = {'Dairy cattle': 'Dairy cattle',
                     'Beef cattle': 'Beef cattle',
                     'Goats / sheep for milk': 'Goats and Sheep for milk',
                     'Goats / sheep for meat': 'Goats and Sheep for meat',
                     'Pigs': 'Pigs',
                     'Poultry': 'Poultry',
                     }

    # Create list with lv_data column names in, so that I can use them for loc search
    # below
    lv_column_list = lv_data.columns.values.tolist()

    # Create iterable so we can skip 1st item ("Finkile Peasant") using "next"
    # and create list of all an_prod livestock type
    iter_lv_column_list = iter(lv_column_list)
    an_prod_list = an_prod.loc[:, 'Unnamed: 1'].tolist()
    next(iter_lv_column_list)

    # Now iterate through, checking each livestock that has been input is on an_prod
    # dataframe. If it is, add it to list so we can create Livestock instance for
    # each one
    livestock_checked = []
    livestock_missing_data = []
    for animal in iter_lv_column_list:
        if animal in an_prod_list:
            livestock_checked.append(animal)
        else:
            livestock_checked.append('n/a')
            livestock_missing_data.append(animal)

    # Import crop production data from ora_crop_model. Take name of crop and production compared to steady state
    # per month. Add this to list to allow calculation of feed availability change
    crop_list = (test_crop_algorithms(form))
    feed_avail_change = DataFrame()
    n = 1
    for crop in crop_list:
        crop_rotations = list(crop.crop_rotation_info)
        feed_avail_change[f'area_{n}_crop'] = crop_rotations
        prod_comp_ss_mon = list(crop.yield_atyp_mon)
        feed_avail_change[f'area_{n}_yield_change'] = prod_comp_ss_mon
        n += 1
    feed_avail_dic = feed_avail_change.to_dict(orient='records')

    # Iterate through feed_avail_dic to aggregate all data per month. This involves matching crops,
    # adding yield change from that crop to total, then dividing total by number of areas (total tallied in
    # 'crop_x_count' var below
    total_crop_A_change = 0
    total_crop_B_change = 0
    total_crop_C_change = 0
    total_crop_D_change = 0
    total_crop_E_change = 0

    for dic in feed_avail_dic:
        crop_A_count = 0
        crop_B_count = 0
        crop_C_count = 0
        crop_D_count = 0
        crop_E_count = 0

        crop_A_name = dic['area_1_crop']
        total_crop_A_change = dic['area_1_yield_change']
        crop_A_count += 1
        dic.update({"Crop_A_name": crop_A_name})
        dic.update({"Crop_A_tot_yield_change_month": total_crop_A_change})

        if dic['area_2_crop'] == dic['area_1_crop']:
            total_crop_A_change = (dic['area_1_yield_change'] + dic['area_2_yield_change'])
            crop_A_count += 1
            dic.update({"Crop_A_tot_yield_change_month":total_crop_A_change})
        else:
            crop_B_name = dic['area_2_crop']
            total_crop_B_change = dic['area_2_yield_change']
            crop_B_count += 1
            dic.update({"Crop_B_name": crop_B_name})
            dic.update({"Crop_B_tot_yield_change_month":total_crop_B_change})

        if dic['area_3_crop'] == dic['area_1_crop']:
            total_crop_A_change = (total_crop_A_change + dic['area_3_yield_change'])
            crop_A_count += 1
            dic.update({"Crop_A_tot_yield_change_month":total_crop_A_change})
        elif dic['area_3_crop'] == dic['area_2_crop']:
            total_crop_B_change = (total_crop_B_change + dic['area_3_yield_change'])
            crop_B_count += 1
            dic.update({"Crop_B_tot_yield_change_month": total_crop_B_change})
        else:
            total_crop_C_change = dic['area_3_yield_change']
            crop_C_name = dic['area_3_crop']
            crop_C_count += 1
            dic.update({"Crop_C_name": crop_C_name})
            dic.update({"Crop_C_tot_yield_change_month":total_crop_C_change})

        if dic['area_4_crop'] == dic['area_1_crop']:
            total_crop_A_change = (total_crop_A_change + dic['area_4_yield_change'])
            crop_A_count += 1
            dic.update({"Crop_A_tot_yield_change_month":total_crop_A_change})
        elif dic['area_4_crop'] == dic['area_2_crop']:
            total_crop_B_change = (total_crop_B_change + dic['area_4_yield_change'])
            crop_B_count += 1
            dic.update({"Crop_B_tot_yield_change_month": total_crop_B_change})
        elif dic['area_4_crop'] == dic['area_3_crop']:
            total_crop_C_change = (total_crop_C_change + dic['area_4_yield_change'])
            crop_C_count += 1
            dic.update({"Crop_C_tot_yield_change_month": total_crop_C_change})
        else:
            crop_D_name = dic['area_4_crop']
            dic.update({"Crop_D_name": crop_D_name})
            total_crop_D_change = dic['area_4_yield_change']
            crop_D_count += 1
            dic.update({"Crop_D_tot_yield_change_month":total_crop_D_change})

        if dic['area_5_crop'] == dic['area_1_crop']:
            total_crop_A_change = (total_crop_A_change + dic['area_5_yield_change'])
            crop_A_count += 1
            dic.update({"Crop_A_tot_yield_change_month":total_crop_A_change})
        elif dic['area_5_crop'] == dic['area_2_crop']:
            total_crop_B_change = (total_crop_B_change + dic['area_5_yield_change'])
            crop_B_count += 1
            dic.update({"Crop_B_tot_yield_change_month": total_crop_B_change})
        elif dic['area_5_crop'] == dic['area_3_crop']:
            total_crop_C_change = (total_crop_C_change + dic['area_5_yield_change'])
            crop_C_count += 1
            dic.update({"Crop_C_tot_yield_change_month": total_crop_C_change})
        elif dic['area_5_crop'] == dic['area_4_crop']:
            total_crop_D_change = (total_crop_D_change + dic['area_5_yield_change'])
            crop_D_count += 1
            dic.update({"Crop_D_tot_yield_change_month": total_crop_D_change})
        else:
            crop_E_name = dic['area_5_crop']
            dic.update({"Crop_E_name": crop_E_name})
            total_crop_E_change = dic['area_5_yield_change']
            crop_E_count += 1
            dic.update({"Crop_E_tot_yield_change_month":total_crop_E_change})

        if crop_A_count != 0:
            crop_A_tot = (total_crop_A_change / crop_A_count)
            dic.update({"Crop_A_tot_yield_change_month": crop_A_tot})
        if crop_B_count != 0:
            crop_B_tot = (total_crop_B_change / crop_B_count)
            dic.update({"Crop_B_tot_yield_change_month": crop_B_tot})
        if crop_C_count != 0:
            crop_C_tot = (total_crop_C_change / crop_C_count)
            dic.update({"Crop_C_tot_yield_change_month": crop_C_tot})
        if crop_D_count != 0:
            crop_D_tot = (total_crop_D_change / crop_D_count)
            dic.update({"Crop_D_tot_yield_change_month": crop_D_tot})
        if crop_E_count != 0:
            crop_E_tot = (total_crop_E_change / crop_E_count)
            dic.update({"Crop_E_tot_yield_change_month": crop_E_tot})

    # Remove all data apart from totals for the month, then return this list of dictionaries. add number showing month
    month = 1
    for dic in feed_avail_dic:
        del dic['area_1_crop']
        del dic['area_1_yield_change']
        del dic['area_2_crop']
        del dic['area_2_yield_change']
        del dic['area_3_crop']
        del dic['area_3_yield_change']
        del dic['area_4_crop']
        del dic['area_4_yield_change']
        del dic['area_5_crop']
        del dic['area_5_yield_change']
        dic.update({'month' : month})
        month += 1

    class Livestock:
        """Information on different types of livestock"""

        def __init__(self, name, region, system):
            self.name = name
            self.region = region
            self.system = system

        def get_prod_info_new(self):
            """Pull information on average production values"""
            self.prod_info = (an_prod.loc[
                (an_prod['Unnamed: 1'] == self.name) & (an_prod['Unnamed: 4'] == self.system) & (
                            an_prod['Livestock production system'] == self.region)])
            prod_info = self.prod_info

            milk_egg_prod_per_head = float(prod_info["Milk"])
            meat_prod_per_head = float(prod_info["Meat"])
            manure_prod_per_head = float(prod_info["Manure dry matter"])
            n_excreted_per_head = float(prod_info["Excreted N"])

            self.milk_egg_prod_per_head = milk_egg_prod_per_head
            self.meat_prod_per_head = meat_prod_per_head
            self.manure_prod_per_head = manure_prod_per_head
            self.n_excreted_per_head = n_excreted_per_head
            return milk_egg_prod_per_head, meat_prod_per_head, manure_prod_per_head, n_excreted_per_head

        def get_total_prod(self):
            """Get number of livestock and then give total production for typical year"""

            # Search through input data to match animal type with column header,
            # and pull number of animals from 1st row
            number = (lv_data.loc[0, self.name])

            # Multiply number of animals by average values for region/system etc.
            tot_mil_egg_prod = self.milk_egg_prod_per_head * number
            tot_meat_prod = self.meat_prod_per_head * number
            tot_manure_prod = self.manure_prod_per_head * number
            tot_n_excreted = self.n_excreted_per_head * number

            total_prod_dic = {"Total milk and egg production": tot_mil_egg_prod, "Total meat production": tot_meat_prod,
                              "Total manure production": tot_manure_prod, "Total N excreted": tot_n_excreted, }
            self.number = number
            self.tot_prod_dic = total_prod_dic
            self.tot_mil_egg_prod = tot_mil_egg_prod
            self.tot_meat_prod = tot_meat_prod
            self.tot_manure_prod = tot_manure_prod
            self.tot_n_excreted = tot_n_excreted
            return total_prod_dic

        def get_feed_info(self):
            """Pull information on feed types and %s for each livestock type"""
            # Search through input data file to match animal type with column header, then pull info for each feed type
            feed_avail_strat = (lv_data.loc[1, self.name])
            feed_type_1 = (lv_data.loc[2, self.name])
            feed_type_1_pcnt = (lv_data.loc[3, self.name])
            feed_type_2 = (lv_data.loc[4, self.name])
            feed_type_2_pcnt = (lv_data.loc[5, self.name])
            feed_type_3 = (lv_data.loc[6, self.name])
            feed_type_3_pcnt = (lv_data.loc[7, self.name])
            feed_type_4 = (lv_data.loc[8, self.name])
            feed_type_4_pcnt = (lv_data.loc[9, self.name])
            feed_type_5 = (lv_data.loc[10, self.name])
            feed_type_5_pcnt = (lv_data.loc[11, self.name])
            bought_in_feed_pcnt = (lv_data.loc[12, self.name])

            # Create dic to store all this info, removing zero values
            feed_type_temp = {feed_type_1: feed_type_1_pcnt, feed_type_2: feed_type_2_pcnt,
                              feed_type_3: feed_type_3_pcnt, feed_type_4: feed_type_4_pcnt,
                              feed_type_5: feed_type_5_pcnt, }
            feed_type_dic = {}
            for feed, feed_pct in feed_type_temp.items():
                if feed != 'None':
                    feed_type_dic.update({feed: feed_pct})
            feed_type_dic.update({'Off-farm': bought_in_feed_pcnt})

            self.feed_type_dic = feed_type_dic
            self.feed_avail_strat = feed_avail_strat
            self.feed_type_1 = feed_type_1
            self.feed_type_1_pcnt = feed_type_1_pcnt
            self.feed_type_2 = feed_type_2
            self.feed_type_2_pcnt = feed_type_2_pcnt
            self.feed_type_3 = feed_type_3
            self.feed_type_3_pcnt = feed_type_3_pcnt
            self.feed_type_4 = feed_type_4
            self.feed_type_4_pcnt = feed_type_4_pcnt
            self.feed_type_5 = feed_type_5
            self.feed_type_5_pcnt = feed_type_5_pcnt
            self.bought_in_feed_pcnt = bought_in_feed_pcnt
            return feed_type_dic

        def get_neat_name(self):
            """Convert name to one that can automatically be saved as filename"""
            for key, value in form_name_dic.items():
                if self.name == key:
                    form_name = value
            self.neat_name = form_name

        def calc_feed_supply(self):
            """Calculate the change in available feed for the animal per month for 10 years"""
            harv_change = feed_avail_dic
            ten_yr_month_feed = []
            temp_feed_pcnt = 0
            for dic in harv_change:
                monthly_feed = {'Total_feed_%_obtained': 0, }
                monthly_feed.update({'month': dic['month']})
                try:
                    dic['Crop_A_name'] in self.feed_type_dic
                except KeyError:
                    pass
                else:
                    if dic['Crop_A_name'] in self.feed_type_dic:
                        for key, value in self.feed_type_dic.items():
                            if key == dic['Crop_A_name']:
                                temp_feed_pcnt = value
                        monthly_feed['Total_feed_%_obtained'] += (dic['Crop_A_tot_yield_change_month'] * temp_feed_pcnt)
                        monthly_feed.update({dic['Crop_A_name']: dic['Crop_A_tot_yield_change_month']})
                    else:
                        pass
                try:
                    dic['Crop_B_name'] in self.feed_type_dic
                except KeyError:
                    pass
                else:
                    if dic['Crop_B_name'] in self.feed_type_dic:
                        for key, value in self.feed_type_dic.items():
                            if key == dic['Crop_B_name']:
                                temp_feed_pcnt = value
                        monthly_feed['Total_feed_%_obtained'] += (dic['Crop_B_tot_yield_change_month'] * temp_feed_pcnt)
                        monthly_feed.update({dic['Crop_B_name']: dic['Crop_B_tot_yield_change_month']})
                    else:
                        pass
                try:
                    dic['Crop_C_name'] in self.feed_type_dic
                except KeyError:
                    pass
                else:
                    if dic['Crop_C_name'] in self.feed_type_dic:
                        for key, value in self.feed_type_dic.items():
                            if key == dic['Crop_C_name']:
                                temp_feed_pcnt = value
                        monthly_feed['Total_feed_%_obtained'] += (dic['Crop_C_tot_yield_change_month'] * temp_feed_pcnt)
                        monthly_feed.update({dic['Crop_C_name']: dic['Crop_C_tot_yield_change_month']})
                    else:
                        pass
                try:
                    dic['Crop_D_name'] in self.feed_type_dic
                except KeyError:
                    pass
                else:
                    if dic['Crop_D_name'] in self.feed_type_dic:
                        for key, value in self.feed_type_dic.items():
                            if key == dic['Crop_D_name']:
                                temp_feed_pcnt = value
                        monthly_feed['Total_feed_%_obtained'] += (dic['Crop_D_tot_yield_change_month'] * temp_feed_pcnt)
                        monthly_feed.update({dic['Crop_D_name']: dic['Crop_D_tot_yield_change_month']})
                    else:
                        pass
                try:
                    dic['Crop_E_name'] in self.feed_type_dic
                except KeyError:
                    pass
                else:
                    if dic['Crop_E_name'] in self.feed_type_dic:
                        for key, value in self.feed_type_dic.items():
                            if key == dic['Crop_E_name']:
                                temp_feed_pcnt = value
                        monthly_feed['Total_feed_%_obtained'] += (dic['Crop_E_tot_yield_change_month'] * temp_feed_pcnt)
                        monthly_feed.update({dic['Crop_E_name']: dic['Crop_E_tot_yield_change_month']})
                    else:
                        pass

                try:
                    'Off-farm' in self.feed_type_dic
                except KeyError:
                    pass
                else:
                    monthly_feed['Total_feed_%_obtained'] += self.feed_type_dic['Off-farm']

                ten_yr_month_feed.append(monthly_feed)

            self.monthly_feed = ten_yr_month_feed

        def get_atypical_years_prod(self):
            """Calculate production for atypical years"""

            monthly_feed = self.monthly_feed
            atyp_milk_prod = []
            atyp_meat_prod = []
            atyp_man_prod = []
            atyp_N_excr = []

            if self.feed_avail_strat == "1. Buy/sell":
                for i in range(0, 119):
                    atyp_milk_prod.append(self.tot_mil_egg_prod)
                    atyp_meat_prod.append(self.tot_meat_prod)
                    atyp_man_prod.append(self.tot_manure_prod)
                    atyp_N_excr.append(self.tot_n_excreted)

            elif self.feed_avail_strat == '2. On farm production':

                for month in monthly_feed:
                    atyp_milk_prod.append(((month['Total_feed_%_obtained'] / 100) * self.tot_mil_egg_prod))
                    atyp_meat_prod.append(((month['Total_feed_%_obtained'] / 100) * self.tot_meat_prod))
                    atyp_man_prod.append(((month['Total_feed_%_obtained'] / 100) * self.tot_manure_prod))
                    atyp_N_excr.append(((month['Total_feed_%_obtained'] / 100) * self.tot_n_excreted))

            self.atyp_milk_prod = atyp_milk_prod
            self.atyp_meat_prod = atyp_meat_prod
            self.atyp_man_prod = atyp_man_prod
            self.atyp_N_excr = atyp_N_excr

    # create Livestock instances from the livestock_checked list and add to new list
    livestock_list = []
    for animal in livestock_checked:
        if animal != 'n/a':
            animal = Livestock(name=animal, region=supp_info['Region'], system=supp_info['System'])
            livestock_list.append(animal)

    for livestock in livestock_list:
        livestock.get_prod_info_new()
        livestock.get_neat_name()
        livestock.get_total_prod()
        livestock.get_feed_info()
        livestock.calc_feed_supply()
        livestock.get_atypical_years_prod()

    print("\nThe following livestock types have been simulated:\n")
    for livestock in livestock_list:
        print(f"\t{livestock.neat_name}")
    print('\nThe following livestock types lack sufficient supplementary data, and were not simulated:\n')
    for livestock in livestock_missing_data:
        print(f'\t{livestock}')

    return livestock_list
