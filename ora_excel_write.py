#-------------------------------------------------------------------------------
# Name:        ora_excel_write.py
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

__prog__ = 'ora_excel_write.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import os
from glob import glob
from pandas import DataFrame, ExcelWriter, Series

from ora_classes_main import A1SomChange
from generate_charts_funcs import generate_charts

def generate_excel_outfiles(study, subplot, weather, complete_run):

    # concatenate weather into single entity
    # ======================================
    len_ss = len(weather.pettmp_ss['precip'])
    period_lst = len_ss*['steady state']

    len_fwd = len(weather.pettmp_fwd['precip'])
    period_lst += len_fwd*['forward run']

    precip_lst = weather.pettmp_ss['precip'] + weather.pettmp_fwd['precip']
    tair_lst = weather.pettmp_ss['tair'] + weather.pettmp_fwd['tair']
    pet_lst = weather.pettmp_ss['pet'] + weather.pettmp_fwd['pet']

    pettmp = {'period':period_lst, 'precip':precip_lst, 'tair':tair_lst, 'pet':pet_lst}

    carbon_change, nitrogen_change, soil_water = complete_run
    study_pass_name = study.study_name + '_' + subplot
    som_change_a1 = A1SomChange(pettmp, carbon_change, soil_water)
    write_excel_out(study.out_dir, som_change_a1, study_pass_name, 'A1. SOM change')

    return

def check_out_dir(form):

    # check and if necessary create output directory
    # ==============================================
    form.settings['out_dir'] = ''
    orator_path, dummy = os.path.split(form.settings['inp_dir'])
    out_dir = os.path.normpath(os.path.join(orator_path, 'outputs'))
    if not os.path.isdir(out_dir):
        try:
            os.mkdir(out_dir)
            print('Created output directory: ' + out_dir)
        except PermissionError as err:
            print('*** Error *** Could not create output directory: ' + out_dir)
            out_dir = None

    form.settings['out_dir'] = out_dir
    if out_dir is not None:
        form.w_soil_cn.setEnabled(True)

    return

def retrieve_output_xls_files(form, study_name):
    '''
    retrieve list of Excel files in the output directory

    '''
    out_dir = form.settings['out_dir']      # existence has been pre-checked in check_excel_input_fname
    xlsx_list = glob(out_dir + '/' + study_name + '*.xlsx')
    form.w_combo17.clear()
    if len(xlsx_list) > 0:
        form.w_disp_out.setEnabled(True)
        for out_xlsx in xlsx_list:
            dummy, short_fn = os.path.split(out_xlsx)
            form.w_combo17.addItem(short_fn)
    return

def write_excel_out(out_dir, output_obj, study, sheet_name):
    '''
    condition data before outputting
    '''
    func_name =  __prog__ +  ' write_excel_out'

    # make a safe name
    # ===============
    sht_abbrev = sheet_name.replace('.','').replace(' ','_')
    fname = os.path.join(out_dir, study + '_' + sht_abbrev + '.xlsx')
    if os.path.isfile(fname):
        try:
            os.remove(fname)
        except PermissionError as e:
            print(e)
            return -1

    # create data frame from dictionary
    # =================================
    data_frame = DataFrame()
    for var_name in output_obj.var_name_list:

        tmp_list = output_obj.sheet_data[var_name]

        var_fmt = output_obj.var_formats[var_name].strip('{:\.}')
        if var_fmt[-1] == 'f':
            ndecis = int(var_fmt[:-1])
            data_frame[var_name] = Series([round(val, ndecis) for val in tmp_list])
        else:
            data_frame[var_name] = Series(tmp_list)

    # write to Excel
    # ==============
    # print('Will write ' + fname)
    writer = ExcelWriter(fname)
    data_frame.to_excel(writer, sheet_name)
    writer.save()

    # reopen Excel file and write a chart
    # ===================================
    generate_charts(fname, data_frame, sheet_name)

    return 0
