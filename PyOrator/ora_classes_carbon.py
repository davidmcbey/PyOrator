#-------------------------------------------------------------------------------
# Name:        ora_classes_carbon.py
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

__prog__ = 'ora_classes_carbon.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from math import ceil

class CarbonChange(object, ):

    def __init__(self, run_type):
        """
        A1. Change in soil organic matter
        """
        self.title = 'CarbonChange'
        self.run_type = run_type
        self.data = {}

        var_name_list = list(['month', 'rate_mod', 'c_pi_mnth', 'cow', 'c_n_rat_ow',
                                        'pool_c_dpm', 'pi_to_dpm', 'cow_to_dpm', 'c_loss_dpm',
                                        'pool_c_rpm', 'pi_to_rpm', 'c_loss_rpm',
                                        'pool_c_bio', 'c_input_bio', 'c_loss_bio',
                                        'pool_c_hum', 'cow_to_hum', 'c_input_hum', 'c_loss_hum',
                                        'pool_c_iom', 'ioc_to_iom', 'tot_soc_simul', 'co2_release'])
        for var_name in var_name_list:
            self.data[var_name] = []

        self.var_name_list = var_name_list

    def get_last_tstep_pools(self):
        '''
        TODO: these variables are currently hard coded:
             c_n_rat_ow = 0.5; prop_co2 = 0.5;  prop_bio =  0.5; prop_hum = 0.5;  c_n_rat_som = 10
        '''
        pool_c_dpm = self.data['pool_c_dpm'][-1]
        pool_c_rpm = self.data['pool_c_rpm'][-1]
        pool_c_hum = self.data['pool_c_hum'][-1]
        pool_c_bio = self.data['pool_c_bio'][-1]
        pool_c_iom = self.data['pool_c_iom'][-1]

        c_input_bio = self.data['c_input_bio'][-1]
        c_input_hum = self.data['c_input_hum'][-1]
        c_loss_dpm = self.data['c_loss_dpm'][-1]
        c_loss_rpm = self.data['c_loss_rpm'][-1]
        c_loss_hum = self.data['c_loss_hum'][-1]
        c_loss_bio = self.data['c_loss_bio'][-1]

        tot_soc_simul = self.data['tot_soc_simul'][-1]      # TODO

        last_tstep_vars = (pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom, tot_soc_simul,
                                        c_input_bio , c_input_hum, c_loss_dpm, c_loss_rpm, c_loss_hum, c_loss_bio)

        return last_tstep_vars

    def get_vals_for_tstep(self, tstep):
        '''
        TODO: these variables are currently hard coded:
             c_n_rat_ow = 0.5; prop_co2 = 0.5;  prop_bio =  0.5; prop_hum = 0.5;  c_n_rat_som = 10
        '''
        rate_mod = self.data['rate_mod'][tstep]
        cow = self.data['cow'][tstep]
        c_n_rat_ow = 0.5  # TODO
        # c_n_rat_ow = self.data['c_n_rat_ow'][tstep]

        prop_co2 = 0.5  # TODO
        # prop_co2 = self.data['prop_co2'][tstep]

        co2_release = self.data['co2_release'][tstep]
        c_n_rat_som = 10 # TODO
        # c_n_rat_som = self.data['c_n_rat_som'][tstep]

        c_loss_bio = self.data['c_loss_bio'][tstep]
        prop_bio =  0.5  # TODO
        # prop_bio = self.data['prop_bio'][tstep]

        pool_c_dpm = self.data['pool_c_dpm'][tstep]
        pi_to_dpm = self.data['pi_to_dpm'][tstep]
        cow_to_dpm = self.data['cow_to_dpm'][tstep]
        c_loss_dpm = self.data['c_loss_dpm'][tstep]

        pool_c_rpm = self.data['pool_c_rpm'][tstep]
        pi_to_rpm = self.data['pi_to_rpm'][tstep]
        c_loss_rpm = self.data['c_loss_rpm'][tstep]

        pool_c_hum = self.data['pool_c_hum'][tstep]
        # prop_hum = self.data['prop_hum'][tstep]
        prop_hum = 0.5  # TODO

        cow_to_hum = self.data['cow_to_hum'][tstep]
        c_loss_hum = self.data['c_loss_hum'][tstep]

        return cow, c_n_rat_ow, prop_co2, rate_mod, c_n_rat_som, co2_release, \
                            c_loss_bio, prop_bio, pool_c_dpm, pi_to_dpm, cow_to_dpm, c_loss_dpm,  \
                            pool_c_hum, prop_hum, cow_to_hum, c_loss_hum, pool_c_rpm, pi_to_rpm, c_loss_rpm

    def append_vars(self, month, rate_mod, c_pi_mnth, cow, c_n_rat_ow,
                                                pool_c_dpm, pi_to_dpm, cow_to_dpm, c_loss_dpm,
                                                pool_c_rpm, pi_to_rpm, c_loss_rpm,
                                                pool_c_bio, c_input_bio, c_loss_bio,
                                                pool_c_hum, cow_to_hum, c_input_hum, c_loss_hum,
                                                pool_c_iom, ioc_to_iom, tot_soc_simul, co2_release):
        '''
        add one set of values for this timestep to each of lists
        columns refer to A1. SOM change sheet
        '''

        # rate modifier start of each month cols D, G and H
        # ==================================================
        for var in ['month', 'rate_mod', 'c_pi_mnth', 'cow', 'c_n_rat_ow']:
            self.data[var].append(eval(var))

        # DPM pool cols K to M
        # ====================
        for var in ['pool_c_dpm', 'cow_to_dpm', 'pi_to_dpm', 'c_loss_dpm']:
            self.data[var].append(eval(var))

        # RPM pool cols N to P
        # ====================
        for var in ['pool_c_rpm', 'pi_to_rpm', 'c_loss_rpm']:
            self.data[var].append(eval(var))

        # BIO pool cols Q to S
        # ====================
        for var in ['pool_c_bio', 'c_input_bio', 'c_loss_bio']:
            self.data[var].append(eval(var))

        # HUM pool cols K to M
        # ====================
        for var in ['pool_c_hum', 'cow_to_hum', 'c_input_hum', 'c_loss_hum']:
            self.data[var].append(eval(var))

        # IOM pool cols X to AA
        # =====================
        for var in ['pool_c_iom', 'ioc_to_iom', 'tot_soc_simul', 'co2_release']:
            self.data[var].append(eval(var))
