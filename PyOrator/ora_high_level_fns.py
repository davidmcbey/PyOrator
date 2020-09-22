# -------------------------------------------------------------------------------
# Name:        ora_high_level_fns.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     13/04/2017
# Licence:     <your licence>
#
#   The simulation starts using default SOC pools and plant inputs
#    The SOC pools can have any value as the steady state simulation will adjust the pool sizes according to the measured SOC
#    The value of the total annual plant inputs will also be determined by the steady state simulation, but the
#    distribution of the plant inputs should follow the cropping patterns observed in the field#
#
#    The simulation is continued for 100 years, after which time, the C in the DPM, RPM, BIO, HUM and IOM pools are summed and
#    compared to the measured soil C. The soil C pools are then re-initialised with the values
#    calculated after 100 years and the plant inputs, CPI, are adjusted according to the ratio of measured and simulated total soil C
#
# -------------------------------------------------------------------------------
# !/usr/bin/env python

__prog__ = 'ora_high_level_fns.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import os
from ora_forward_run import cn_forward_run
from ora_low_level_fns import get_rate_temp, inert_organic_carbon, carbon_lost_from_pool, summary_table_add, \
                                                        get_values_for_tstep, get_soil_vars, init_ss_carbon_pools
from ora_classes_main import MngmntSubplot
from ora_classes_carbon import CarbonChange
from ora_nitrogen_model import soil_nitrogen
from ora_water_model import get_soil_water, get_soil_water_constants, SoilWater
from ora_excel_write import retrieve_output_xls_files, generate_excel_outfiles
from ora_excel_read import ReadInputParms, ReadInputSubplots, ReadStudy, ReadWeather

# rate constant for decomposition of the pool
# ===========================================
K_DPM = 10/12;    K_RPM = 0.3/12;   K_BIO = 0.66/12;  K_HUM = 0.02/12  # per month
MAX_ITERS = 1000
SOC_MIN_DIFF = 0.0000001  # convergence criteria tonne/hectare

def _cn_steady_state(parameters, weather, management, soil_vars, study, subplot):
    '''

    '''
    run_mode = 'steady state'
    pettmp = weather.pettmp_ss

    t_depth, t_bulk, t_pH_h2o, tot_soc_meas, prop_hum, prop_bio, prop_co2 = get_soil_vars(soil_vars)
    pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom, tot_soc_simul = init_ss_carbon_pools(tot_soc_meas)

    summary_table = summary_table_add(pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom, management.pi_tonnes)

    # water content at initial and first time step
    # ============================================
    wc_t0, wc_t1, imnth = 3*[0]
    wc_fld_cap, wc_pwp = get_soil_water_constants(soil_vars)

    c_input_bio, c_input_hum, c_loss_dpm, c_loss_rpm, c_loss_hum, c_loss_bio = 6*[0]

    ntsteps = management.ntsteps

    converge_flag = False
    for iteration in range(MAX_ITERS):
        pi_tonnes = management.pi_tonnes
        carbon_change = CarbonChange('steady state')
        soil_water = SoilWater()

        for tstep in range(ntsteps):

            tair, precip, pet, irrig, c_pi_mnth, c_n_rat_ow, rat_dpm_rpm, cow, rat_dpm_hum_ow, prop_iom_ow, \
                            max_root_dpth = get_values_for_tstep(pettmp, management, parameters, tstep)

            wat_soil, wc_t0, wc_t1 = get_soil_water(tstep, precip, pet, irrig, wc_fld_cap, wc_pwp, wc_t0, wc_t1)

            rate_mod, rate_moist = get_rate_temp(tair, t_pH_h2o, wc_fld_cap, wc_pwp, wat_soil)

            # plant inputs and losses (t ha-1) passed to the DPM pool
            # =======================================================
            pi_to_dpm = c_pi_mnth * rat_dpm_rpm/(1.0 + rat_dpm_rpm)                       # (eq.2.1.10)
            cow_to_dpm = cow * rat_dpm_hum_ow * (1.0 - prop_iom_ow)/(1 + rat_dpm_hum_ow)  # (eq.2.1.12)
            pool_c_dpm += pi_to_dpm + cow_to_dpm - c_loss_dpm
            pool_c_dpm = max(0, pool_c_dpm)

            # RPM pool
            # ========
            pi_to_rpm = c_pi_mnth * 1.0 / (1.0 + rat_dpm_rpm)   # (eq.2.1.11)
            pool_c_rpm += pi_to_rpm - c_loss_rpm

            # BIO pool
            # ========
            pool_c_bio += c_input_bio - c_loss_bio

            # HUM pool
            # ========
            cow_to_hum = cow * (1 - prop_iom_ow)/(1 + rat_dpm_hum_ow)  # (eq.2.1.13)
            pool_c_hum += cow_to_hum + c_input_hum - c_loss_hum

            # IOM pool
            # ========
            ioc_to_iom = inert_organic_carbon(prop_iom_ow, cow)  # add any IOM from organic waste added to the soil
            pool_c_iom += ioc_to_iom

            # carbon losses
            # =============
            c_loss_dpm = carbon_lost_from_pool(pool_c_dpm, K_DPM, rate_mod)
            c_loss_rpm = carbon_lost_from_pool(pool_c_rpm, K_RPM, rate_mod)
            c_loss_bio = carbon_lost_from_pool(pool_c_bio, K_BIO, rate_mod)
            c_loss_hum = carbon_lost_from_pool(pool_c_hum, K_HUM, rate_mod)
            c_loss_total = c_loss_dpm + c_loss_rpm + c_loss_hum + c_loss_bio

            c_input_bio = prop_bio * c_loss_total
            c_input_hum = prop_hum * c_loss_total
            co2_release = prop_co2 * c_loss_total        # co2 due to aerobic decomp - Loss as CO2 (t ha-1)

            carbon_change.append_vars(imnth, rate_mod, c_pi_mnth, cow, c_n_rat_ow,
                                      pool_c_dpm, pi_to_dpm, cow_to_dpm, c_loss_dpm,
                                      pool_c_rpm, pi_to_rpm, c_loss_rpm,
                                      pool_c_bio, c_input_bio, c_loss_bio,
                                      pool_c_hum, cow_to_hum, c_input_hum, c_loss_hum,
                                      pool_c_iom, ioc_to_iom, tot_soc_simul, co2_release)

            soil_water.append_vars(t_depth, max_root_dpth, precip, pet, irrig, wc_pwp, wat_soil, wc_fld_cap)

        # after steady state period has completed adjust plant inputs
        # ===========================================================
        tot_soc_simul = pool_c_dpm + pool_c_rpm + pool_c_bio + pool_c_hum + pool_c_iom
        pcnt_c = tot_soc_simul/(t_depth * t_bulk)
        rat_meas_simul_soc = tot_soc_meas/tot_soc_simul
        management.pi_tonnes = [val*rat_meas_simul_soc for val in pi_tonnes]   # (eq.2.1.1)

        # check for convergence
        # =====================
        diff_abs = abs(tot_soc_meas - tot_soc_simul)
        if  diff_abs < SOC_MIN_DIFF:
            print('Simulated and Measured SOC: {}\t*** converged *** after {} iterations'
                                                                        .format(round(tot_soc_simul, 3), iteration + 1))

            # overwrite plant inputs with adjusted values
            # ===========================================
            management.pi_tonnes = pi_tonnes
            summary_table_add(pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom, pi_tonnes, summary_table)
            converge_flag = True
            break

    if converge_flag:
        nitrogen_change = soil_nitrogen(carbon_change, soil_water, parameters, pettmp, management, soil_vars)
        steady_state = (carbon_change, nitrogen_change, soil_water)
    else:
        steady_state = None
        print('Simulated SOC: {}\tMeasured SOC: {}\t *** failed to converge *** after iterations: {}'
              .format(round(tot_soc_simul, 3), tot_soc_meas, iteration + 1))

    return steady_state

def test_soil_cn_algorithms(form):
    """
    retrieve weather and soil
    """
    func_name = __prog__ + '\ttest_soil_cn_algorithms'

    xls_inp_fname = os.path.normpath(form.w_lbl13.text())
    if not os.path.isfile(xls_inp_fname):
        print('Excel input file ' + xls_inp_fname + 'must exist')
        return

    # read input Excel workbook
    # =========================
    print('Loading: ' + xls_inp_fname)
    study = ReadStudy(xls_inp_fname, form.settings['out_dir'])
    ora_parms = ReadInputParms(xls_inp_fname)
    if ora_parms.ow_parms is None:
        return
    ora_weather = ReadWeather(xls_inp_fname, study.latitude)
    ora_subplots = ReadInputSubplots(xls_inp_fname, ora_parms.crop_vars)

    # process each subplot
    # ====================
    for subplot in ora_subplots.soil_all_areas:

        soil_vars = ora_subplots.soil_all_areas[subplot]

        mngmnt_ss = MngmntSubplot(ora_subplots.crop_mngmnt_ss[subplot], ora_parms)
        steady_state = _cn_steady_state(ora_parms, ora_weather, mngmnt_ss, soil_vars, study, subplot)
        if steady_state is None:
            print('Skipping forward run for ' + subplot)
            continue

        pi_tonnes = steady_state[0].data['c_pi_mnth']

        mngmnt_fwd = MngmntSubplot(ora_subplots.crop_mngmnt_fwd[subplot], ora_parms, pi_tonnes)
        complete_run = cn_forward_run(ora_parms, ora_weather, mngmnt_fwd, soil_vars, steady_state)

        # outputs only
        # ============
        if study.output_excel:
            generate_excel_outfiles(study, subplot, ora_weather, complete_run)
        print()

    # update GUI with new Excel output files
    # ======================================
    if study.output_excel:
        retrieve_output_xls_files(form, study.study_name)

    print('Finished with ' + func_name)
    return
