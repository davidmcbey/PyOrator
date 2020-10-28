#-------------------------------------------------------------------------------
# Name:        ora_nitrogen_model.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     06/09/2020
# Licence:     <your licence>
#
# Description:
#   to enable the available water in a given depth of soil to be determined
#
#   For a given depth of soil, d (cm), the available water is calculated as the difference between the water content at
#   field capacity, Vfc(mm), and a lower limit of water content.
#
#   The lower limit for the water content is calculated from the water content at permanent wilting point, Vpwp (mm),
#   divided by a "drying potential", rdry (currently set to 2).
#
#   The volumetric water content at field capacity, Theta_fc (%) and the volumetric water content at permanent
#   wilting point, Theta_pwp (%), are defined
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_nitrogen_model.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import os

from ora_classes_nitrogen import NitrogenChange
from ora_nitrogen_fns import no3_crop_uptake, get_n_parameters, no3_immobilisation, no3_denitrific, \
                                                                            no3_leaching, loss_adjustment_ratio

from ora_nh4_fns import nh4_mineralisation, nh4_immobilisation, nh4_nitrification, nh4_volatilisation, nh4_crop_uptake

def soil_nitrogen(carbon_obj, soil_water_obj, parameters, pettmp, management, soil_vars):
    '''
    The soil organic matter pools (BIO and HUM-N) are assumed to have a constant C:N ratio (8.5 after Bradbury et al., 1993)
    '''

    n_parms = parameters.n_parms
    crop_vars = parameters.crop_vars

    # initialise the zeroth timestep
    # ==============================
    nitrogen_change = NitrogenChange()

    no3_atmos, nh4_atmos, k_nitrif, min_no3_nh4, n_d50, n_denit_max = get_n_parameters(n_parms)
    t_depth = soil_vars.t_depth

    crop_curr = management.crop_currs[0]
    c_n_rat_pi = crop_vars[crop_curr]['c_n_rat_pi']
    c_n_rat_dpm_prev, c_n_rat_rpm_prev = 2*[c_n_rat_pi]
    c_n_rat_hum_prev = 8.5      # (8.5 after Bradbury et al., 1993)

    no3_start, nh4_manure, nh4_start, nh4_fert, no3_fert, n_crop_adjust  = 6*[0]      # TODO

    wc_start = 0 # TODO

    # main temporal loop
    # ==================
    imnth = 1   # may not always be January
    for tstep in range(management.ntsteps):
        precip = pettmp['precip'][tstep]
        pet = pettmp['pet'][tstep]

        cow, c_n_rat_ow, prop_co2, rate_mod, c_n_rat_som, co2_release, \
        c_loss_bio, prop_bio, pool_c_dpm, pi_to_dpm, cow_to_dpm, c_loss_dpm, \
        pool_c_hum, prop_hum, cow_to_hum, c_loss_hum, pool_c_rpm, pi_to_rpm, \
                                                c_loss_rpm = carbon_obj.get_vals_for_tstep(tstep)
        wat_soil, wc_pwp, wc_fld_cap = soil_water_obj.get_vals_for_tstep(tstep)
        if tstep == 0:
            dpm_prev = pool_c_dpm
            rpm_prev = pool_c_rpm
            hum_prev = pool_c_hum


        # C to N ratios A2a soil N supply
        # ===============================
        dpm_inpt = pi_to_dpm + cow_to_dpm
        denom = (dpm_prev/c_n_rat_dpm_prev) + (dpm_inpt/c_n_rat_pi) + (cow_to_dpm/c_n_rat_ow)
        c_n_rat_dpm = (dpm_prev + dpm_inpt)/denom                                                   # (eq.3.3.10)
        c_n_rat_rpm = (rpm_prev + pi_to_rpm)/((rpm_prev/c_n_rat_rpm_prev) + (pi_to_rpm/c_n_rat_pi)) # (eq.3.3.11)
        c_n_rat_hum = (hum_prev + cow_to_hum)/((hum_prev/c_n_rat_hum_prev) + (cow_to_hum/c_n_rat_ow))  # (eq.3.3.12)
        c_n_rat_dpm_prev = c_n_rat_dpm
        c_n_rat_rpm_prev = c_n_rat_rpm
        c_n_rat_hum_prev = c_n_rat_hum

        # (eq.3.3.8)
        # ==========
        n_release = prop_co2* 1000 * ((c_loss_dpm/c_n_rat_dpm) + c_loss_rpm/c_n_rat_rpm +
                                                                            (c_loss_bio + c_loss_hum)/c_n_rat_som)
        # (eq.3.3.9)
        # ==========
        n_adjust = prop_bio*(c_loss_dpm*(1/c_n_rat_som - 1/c_n_rat_dpm) + c_loss_rpm*(1/c_n_rat_som - 1/c_n_rat_rpm)) \
                 + prop_hum*(c_loss_dpm*(1/c_n_rat_hum - 1/c_n_rat_dpm) + c_loss_rpm*(1/c_n_rat_hum - 1/c_n_rat_rpm))
        n_adjustment = 1000 * n_adjust
        soil_n_supply = n_release - n_adjustment    # soil N supply (kg ha-1)

        # A2b Crop N uptake
        # =================
        nut_n_fert = 0
        nut_n_min = crop_vars[crop_curr]['n_supply_min']
        nut_n_opt = crop_vars[crop_curr]['n_supply_opt']
        n_respns_coef = crop_vars[crop_curr]['n_respns_coef']

        nut_n_soil = soil_n_supply
        prop_n_opt = (nut_n_soil + nut_n_fert - nut_n_min)/(nut_n_opt - nut_n_min)  # (eq.3.3.1)

        # Ammonium N (kg/ha) NB required before nitrate due to nitrification
        # ==================================================================
        nh4_miner = nh4_mineralisation(nut_n_soil)
        nh4_immob = nh4_immobilisation(nut_n_soil, min_no3_nh4)

        nh4_total_inp = nh4_fert + nh4_miner + nh4_atmos
        nh4_nitrif = nh4_nitrification(nh4_start, nh4_total_inp, rate_mod, k_nitrif)

        # Nitrate N (kg/ha)
        # =================
        no3_nitrif = nh4_nitrif  # TODO: check
        no3_total_inp = no3_atmos + no3_fert + no3_nitrif

        nmnths_grow = crop_vars[crop_curr]['nmnths_grow']
        no3_avail = no3_start + no3_total_inp
        nh4_avail = nh4_start + nh4_total_inp
        n_crop, no3_cropup, prop_yld_opt = \
                            no3_crop_uptake(prop_n_opt, n_respns_coef, nut_n_opt, nmnths_grow, no3_avail, nh4_avail)

        # Nitrate N (kg/ha)
        # =================
        no3_immob = no3_immobilisation(nut_n_soil, nh4_immob, min_no3_nh4)
        no3_leach, wat_drain = no3_leaching(precip, wc_start, pet, wc_fld_cap, no3_start, no3_total_inp, min_no3_nh4)

        no3_denitr, n_denit_max, rate_denit_no3, rate_denit_moist, rate_denit_bio, prop_n2_wat, prop_n2_no3 = \
               no3_denitrific(imnth, t_depth, wat_soil, wc_pwp, wc_fld_cap, co2_release, no3_avail, n_denit_max, n_d50)

        # crop uptake col M
        # =================
        no3_total_loss = no3_immob + no3_leach + no3_denitr + no3_cropup
        loss_adj_rat_no3 = loss_adjustment_ratio(no3_start, no3_total_inp, no3_total_loss)
        no3_loss_adjust = loss_adj_rat_no3 * no3_total_loss

        # back to Ammonium N
        # ==================
        nh4_volat = nh4_volatilisation(precip, nh4_manure, nh4_fert)
        nh4_cropup = nh4_crop_uptake(n_crop, no3_avail, nh4_avail)

        nh4_total_loss = nh4_immob + nh4_nitrif + nh4_volat + nh4_cropup
        nh4_loss_adjust = loss_adjustment_ratio(nh4_start, nh4_total_inp, nh4_total_loss)
        nh4_end = nh4_start + nh4_total_inp - nh4_total_loss * nh4_loss_adjust

        no3_denitr_adjust = no3_denitr * loss_adj_rat_no3
        n2o_release = (1.0 - (prop_n2_wat * prop_n2_no3)) * no3_denitr_adjust  # (eq.2.4.13)

        no3_leach_adjust = no3_leach*no3_loss_adjust # A2c - Nitrate-N lost by leaching (kg ha-1)

        nh4_volat_adj = nh4_volat*no3_loss_adjust  # A2e - Volatilised N loss

        no3_end = no3_start + no3_total_inp - no3_loss_adjust

        nitrogen_change.append_vars(imnth, tstep, wat_soil, min_no3_nh4, nut_n_soil, no3_start, no3_atmos,
                    no3_fert, no3_nitrif, no3_total_inp, no3_immob, no3_leach, no3_leach_adjust,
                    no3_denitr, no3_cropup, no3_total_loss, no3_loss_adjust, loss_adj_rat_no3, no3_end, n2o_release,
                    nh4_start, nh4_fert, nh4_miner, nh4_atmos, nh4_total_inp, nh4_immob, nh4_nitrif,
                    nh4_volat, nh4_volat_adj, nh4_cropup, nh4_loss_adjust, nh4_total_loss, nh4_end)
        
        imnth += 1
        if imnth > 12:
            imnth = 1

    return nitrogen_change
