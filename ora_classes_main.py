#-------------------------------------------------------------------------------
# Name:        ora_classes_main.py
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

__prog__ = 'ora_classes_main.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from math import ceil

from ora_nitrogen_fns import no3_crop_uptake, loss_adjustment_ratio, no3_immobilisation, no3_leaching, \
                                                                                                no3_denitrific
from ora_nh4_fns import nh4_nitrification, nh4_mineralisation, nh4_immobilisation, nh4_volatilisation, nh4_crop_uptake

from ora_low_level_fns import populate_org_fert

class MngmntSubplot(object, ):
    '''

    '''
    def __init__(self, crop_mngmnt, ora_parms, pi_tonnes_ss = None):
        """
        determine temporal extent of the management
        should list indices correspond to the months?
        """
        self.crop_mngmnt = crop_mngmnt

        last_crop = crop_mngmnt[-1]

        nyears = ceil(last_crop.harvest_mnth/12)
        ntsteps = nyears * 12
        np1 = ntsteps + 1
        irrig = np1*[0]
        org_fert = np1*[None]
        fert_n_list = np1*[None]
        pi_prop_list = np1*[0]     # plant input proportions
        pi_tonnes_list = np1*[0]   # plant input - will be overwritten
        crop_names = np1 * [None]
        crop_currs = np1 * [None]

        # populate list of current crops
        # ==============================
        imnth_last = len(crop_currs)
        for crop in reversed(crop_mngmnt):
            crop_current = crop.crop_lu
            imnth_sow = crop.sowing_mnth
            crop_currs[imnth_sow:imnth_last] = [crop_current for indx in range(imnth_sow, imnth_last)]
            imnth_last = imnth_sow

        crop_currs[0:imnth_sow] = [crop_current for indx in range(0, imnth_sow)]      # make sure no gaps

        for crop in crop_mngmnt:
            crop_name = crop.crop_lu  # e.g. Maize
            pi_tonnes = ora_parms.crop_vars[crop_name]['pi_tonnes']
            pi_prop = ora_parms.crop_vars[crop_name]['pi_prop']
            sow_mnth = crop.sowing_mnth
            harv_mnth = crop.harvest_mnth

            # TODO: this does not seem Pythonic
            # =================================
            for indx, imnth in enumerate(range(sow_mnth, harv_mnth + 1)):

                crop_names[imnth] = crop_name
                pi_prop_list[imnth] = pi_prop[indx]
                pi_tonnes_list[imnth] = pi_tonnes[indx]



            for imnth in crop.irrig:
                irrig[imnth] = crop.irrig[imnth]

            org_fert[crop.ow_mnth] = {'ow_type': crop.ow_type, 'amount': crop.ow_amount}
            fert_n_list[crop.fert_mnth] = {'fert_type': crop.fert_type, 'fert_n': crop.fert_n}

        self.nyears = nyears
        self.ntsteps = ntsteps
        self.irrig = irrig[1:]
        self.fert_n = fert_n_list[1:]
        self.org_fert = populate_org_fert(org_fert[1:])
        self.crop_names = crop_names[1:]

        if pi_tonnes_ss is None:
            self.pi_tonnes = pi_tonnes_list[1:]      # required for seeding steady state
        else:
            self.pi_tonnes = pi_tonnes_ss   # use plant inputs from steady state

        self.pi_props  = pi_prop_list[1:]
        self.crop_currs = crop_currs[1:]

class A1SomChange(object, ):

    def __init__(self, pettmp, carbon_obj, soil_water_obj):
        """
        A1. Change in soil organic matter
        """
        self.title = 'SOM_change'

        self.sheet_data = {}

        var_format_dict = {'period':'{:3d}', 'month':'{:d}', 'tstep':'{:d}', 'air_temp':'{:.2f}',
                           'wat_soil':'{:.2f}', 'r_mod':'{:.2f}', 'pi':'{:.2f}', 'cow':'{:.2f}',
                           'dpm':'{:.2f}', 'dpm_inpt':'{:.2f}', 'dpm_loss':'{:.2f}',
                           'rpm':'{:.2f}', 'rpm_inpt':'{:.2f}', 'rpm_loss':'{:.2f}',
                           'bio':'{:.2f}', 'bio_inpt':'{:.2f}', 'bio_loss':'{:.2f}',
                           'hum':'{:.2f}', 'cow_to_hum':'{:.2f}', 'hum_inpt':'{:.2f}', 'hum_loss':'{:.2f}',
                           'iom':'{:.2f}', 'iom_inpt':'{:.2f}', 'total':'{:.2f}', 'co2_release':'{:.2f}'}

        var_name_list = list(var_format_dict.keys())
        for var_name in var_name_list:
            self.sheet_data[var_name] = []

        self.var_name_list = var_name_list
        self.var_formats   = var_format_dict

        ntsteps = len(pettmp['tair'])
        nyears = int(ntsteps/12)

        self.sheet_data['period'] = pettmp['period']    # steady state or forward

        self.sheet_data['month'] = nyears*[tstep + 1 for tstep in range(12)]  # col D
        self.sheet_data['tstep'] = [tstep + 1 for tstep in range(ntsteps)]
        self.sheet_data['wat_soil'] = soil_water_obj.data['wat_soil']  # col F

        self.sheet_data['air_temp'] = pettmp['tair']

        self.sheet_data['r_mod'] = carbon_obj.data['rate_mod']    # col G
        self.sheet_data['pi'] = carbon_obj.data['c_pi_mnth']       # col H
        self.sheet_data['cow'] = carbon_obj.data['cow']             # col I
        self.sheet_data['dpm'] = carbon_obj.data['pool_c_dpm']  # col K
        self.sheet_data['dpm_inpt'] \
                    = [carbon_obj.data['pi_to_dpm'][i] + carbon_obj.data['cow_to_dpm'][i] for i in range(ntsteps)]

        self.sheet_data['dpm_loss'] = carbon_obj.data['c_loss_dpm']  # col M
        self.sheet_data['rpm'] = carbon_obj.data['pool_c_rpm']
        self.sheet_data['rpm_inpt'] = carbon_obj.data['pi_to_rpm']
        self.sheet_data['rpm_loss'] = carbon_obj.data['c_loss_rpm']
        self.sheet_data['bio'] = carbon_obj.data['pool_c_bio']
        self.sheet_data['bio_inpt'] = carbon_obj.data['c_input_bio']
        self.sheet_data['bio_loss'] = carbon_obj.data['c_loss_bio']
        self.sheet_data['hum'] = carbon_obj.data['pool_c_hum']
        self.sheet_data['cow_to_hum'] = carbon_obj.data['cow_to_hum']
        self.sheet_data['hum_inpt'] = carbon_obj.data['c_input_hum']
        self.sheet_data['hum_loss'] = carbon_obj.data['c_loss_hum']
        self.sheet_data['iom'] = carbon_obj.data['pool_c_iom']
        self.sheet_data['iom_inpt'] = carbon_obj.data['ioc_to_iom']  # col M
        self.sheet_data['total'] = carbon_obj.data['tot_soc_simul']  # col Z
        self.sheet_data['co2_release'] = carbon_obj.data['co2_release']  # col AA co2 due to aerobic decomp - Loss as CO2 (t ha-1)
