#-------------------------------------------------------------------------------
# Name:        ora_classes_nitrogen.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     26/12/2019
# Licence:     <your licence>
# Definitions:
#   spin_up
#
# Description:
#
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_classes_nitrogen.py'
__version__ = '0.0.0'

# Version history
# ---------------
#

class NitrogenChange(object,):
    '''

    '''
    def __init__(self):
        """
        A2. Mineral N
        """
        self.title = 'NitrogenChange'
        self.data = {}


        # Nitrate and Ammonium N (kg/ha) inputs and losses
        # ================================================
        var_name_list = list(['imnth', 'tstep',  'wat_soil', 'no3_start', 'no3_atmos', 'no3_fert', 'no3_nitrif', 
                        'no3_total_inp', 'no3_immob', 'no3_leach', 'no3_leach_adj', 'no3_denitr', 'no3_cropup',
                        'no3_total_loss', 'no3_loss_adj', 'loss_adj_rat_no3', 'no3_end',  'n2o_release',
                        'nh4_start', 'nh4_atmos', 'nh4_fert', 'nh4_miner',
                        'nh4_total_inp', 'nh4_immob', 'nh4_nitrif', 'nh4_volat', 'nh4_volat_adj',
                        'nh4_cropup', 'nh4_total_loss',
                        'nh4_loss_adj', 'nh4_end'])

        for var_name in var_name_list:
            self.data[var_name] = []

        self.var_name_list = var_name_list

    def append_vars(self, imnth, tstep, wat_soil, min_no3_nh4, nut_n_soil, no3_start, no3_atmos,
                    no3_fert, no3_nitrif, no3_total_inp, no3_immob, no3_leach, no3_leach_adj,
                    no3_denitr, no3_cropup, no3_total_loss, no3_loss_adj, loss_adj_rat_no3, no3_end, n2o_release,
                    nh4_start, nh4_fert, nh4_miner, nh4_atmos, nh4_total_inp, nh4_immob, nh4_nitrif,
                    nh4_volat, nh4_volat_adj, nh4_cropup, nh4_loss_adj, nh4_total_loss, nh4_end):
        '''
        add one set of values for this timestep to each of lists
        nut_n_soil   soil N supply
        n_crop     crop N demand
        columns refer to A2. Mineral N sheet
        '''

        # Nitrate and Ammonium at start of each imnth cols D, E and Q
        # ===========================================================
        for var in ['imnth', 'no3_start', 'nh4_start']:
            self.data[var].append(eval(var))

        # Ammonium N (kg/ha) cols R to W
        # ==============================
        for var in ['nh4_atmos', 'nh4_fert', 'nh4_miner', 'nh4_total_inp', 'nh4_immob', 'nh4_nitrif']:
            self.data[var].append(eval(var))

        # Ammonium N cols X to AB
        # =======================
        for var in ['nh4_volat', 'nh4_volat_adj', 'nh4_cropup', 'nh4_total_loss','nh4_loss_adj','nh4_end']:
            self.data[var].append(eval(var))

        # Nitrate N (kg/ha) cols F to L
        # =============================
        for var in ['no3_atmos','no3_fert','no3_nitrif','no3_total_inp', 'n2o_release']:
            self.data[var].append(eval(var))

        # Nitrate N (kg/ha) cols H to L
        # =============================
        for var in ['no3_nitrif', 'no3_total_inp', 'no3_immob', 'no3_leach', 'no3_leach_adj', 'no3_denitr']:
            self.data[var].append(eval(var))

        # crop uptake
        # ===========
        for var in ['no3_cropup', 'no3_total_loss', 'no3_loss_adj', 'loss_adj_rat_no3', 'no3_end']:
            self.data[var].append(eval(var))

