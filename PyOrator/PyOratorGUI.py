#-------------------------------------------------------------------------------
# Name:
# Purpose:     Creates a GUI with five adminstrative levels plus country
# Author:      Mike Martin
# Created:     11/12/2015
# Licence:     <your licence>
# Decription:
#       if climate weather sets and HWSD data are not found then use spreadsheet only for input data
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'PyOratorGUI.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

import sys
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QWidget, QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QLineEdit, \
                                QComboBox, QRadioButton, QButtonGroup, QPushButton, QCheckBox, QFileDialog
import subprocess
from time import sleep

from initialise_pyorator import read_config_file, initiation, write_config_file
from ora_economics_model import test_economics_algorithms
from ora_livestock_model import test_livestock_algorithms
from ora_high_level_fns import test_soil_cn_algorithms
from ora_excel_read import check_excel_input_file

class Form(QWidget):

    def __init__(self, parent=None):

        super(Form, self).__init__(parent)

        self.version = 'PyOrator_v2'
        initiation(self)
        # define two vertical boxes, in LH vertical box put the painter and in RH put the grid
        # define horizon box to put LH and RH vertical boxes in
        hbox = QHBoxLayout()
        hbox.setSpacing(10)

        # left hand vertical box consists of png image
        # ============================================
        lh_vbox = QVBoxLayout()

        # LH vertical box contains image only
        lbl20 = QLabel()
        pixmap = QPixmap(self.settings['fname_png'])
        lbl20.setPixmap(pixmap)

        lh_vbox.addWidget(lbl20)

        # add LH vertical box to horizontal box
        hbox.addLayout(lh_vbox)

        # right hand box consists of combo boxes, labels and buttons
        # ==========================================================
        rh_vbox = QVBoxLayout()

        # The layout is done with the QGridLayout
        grid = QGridLayout()
        grid.setSpacing(10)	# set spacing between widgets

        # line 0
        # ======
        w_study = QLabel()
        grid.addWidget(w_study, 1, 0, 1, 5)
        self.w_study = w_study

        lbl03a = QLabel('')     # spacer
        grid.addWidget(lbl03a, 3, 0)

        # row 13
        # ======
        w_inp_xls = QPushButton("Excel inputs file")
        helpText = 'Select a directory of Orator Excel inputs files'
        w_inp_xls.setToolTip(helpText)
        grid.addWidget(w_inp_xls, 13, 0)
        w_inp_xls.clicked.connect(self.fetchInpExcel)

        w_lbl13 = QLabel('')
        grid.addWidget(w_lbl13, 13, 1, 1, 5)
        self.w_lbl13 = w_lbl13

        # for message from check_xls_fname
        # ================================
        w_lbl14 = QLabel('')
        grid.addWidget(w_lbl14, 14, 0, 1, 5)
        self.w_lbl14 = w_lbl14

        # spacer
        # ======
        lblspace = QLabel()
        grid.addWidget(lblspace, 16, 0, )

        # line 17: display output
        # ========================
        w_disp_out = QPushButton('Display output')
        helpText = 'Simulation start and end years determine the number of growing seasons to simulate\n' \
                   + 'CRU datasets run to 2100 whereas EObs datasets run to 2017'
        w_disp_out.setToolTip(helpText)
        w_disp_out.clicked.connect(self.displayXlsxOutputClicked)
        self.w_disp_out = w_disp_out
        grid.addWidget(w_disp_out, 17, 0)

        w_combo17 = QComboBox()
        self.w_combo17 = w_combo17
        grid.addWidget(w_combo17, 17, 1, 1, 6)

        grid.addWidget(lblspace, 18, 0, )  # spacer

        # line 19
        # =======
        w_economics = QPushButton('Economics')
        helpText = 'Runs ORATOR economics model'
        w_economics.setToolTip(helpText)
        # w_economics.setEnabled(False)
        w_economics.clicked.connect(self.runEconomicsClicked)
        grid.addWidget(w_economics, 19, 0)
        self.w_economics = w_economics

        w_livestock = QPushButton('Livestock')
        helpText = 'Runs ORATOR livestock model'
        w_livestock.setToolTip(helpText)
        # w_livestock.setEnabled(False)
        w_livestock.clicked.connect(self.runLivestockClicked)
        grid.addWidget(w_livestock, 19, 1)
        self.w_livestock = w_livestock

        w_soil_cn = QPushButton('Soil C and N')
        helpText = 'Runs ORATOR soil carbon and nitrogen code'
        w_soil_cn.setToolTip(helpText)
        w_soil_cn.setEnabled(False)
        w_soil_cn.clicked.connect(self.runSoilCnClicked)
        grid.addWidget(w_soil_cn, 19, 2)
        self.w_soil_cn = w_soil_cn

        w_optimise = QPushButton('Optimise')
        helpText = 'Optimisation - not ready'
        w_optimise.setToolTip(helpText)
        w_optimise.setEnabled(False)
        w_optimise.clicked.connect(self.runOptimiseClicked)
        grid.addWidget(w_optimise, 19, 3)
        self.w_optimise = w_optimise

        w_exit = QPushButton("Exit", self)
        helpText = 'Close GUI - the configuration file will be saved'
        w_exit.setToolTip(helpText)
        grid.addWidget(w_exit, 19, 6)
        w_exit.clicked.connect(self.exitClicked)

        # add grid to RH vertical box
        # ===========================
        rh_vbox.addLayout(grid)

        # vertical box goes into horizontal box
        hbox.addLayout(rh_vbox)

        # the horizontal box fits inside the window
        self.setLayout(hbox)

        # posx, posy, width, height
        self.setGeometry(100, 100, 500, 400)
        self.setWindowTitle('Run ORATOR analysis')

        # reads and set values from last run
        # ==================================
        read_config_file(self)

    def displayXlsxOutputClicked(self):

        excel_file = self.settings['out_dir'] + '\\' + self.w_combo17.currentText()
        exe_path = self.settings['exe_path']
        junk = subprocess.Popen(list([exe_path, excel_file]), stdout=subprocess.DEVNULL)
        '''
        import signal
        os.kill(junk.pid, signal.SIGTERM)
        '''

    def runEconomicsClicked(self):

        test_economics_algorithms(self)

    def runOptimiseClicked(self):

        pass

    def runLivestockClicked(self):

        test_livestock_algorithms(self)

    def runSoilCnClicked(self):

        test_soil_cn_algorithms(self)

    def fetchInpExcel(self):
        """
        QFileDialog returns a tuple for Python 3.5, 3.6
        """
        fname = self.w_lbl13.text()
        fname, dummy = QFileDialog.getOpenFileName(self, 'Open file', fname, 'Excel files (*.xlsx)')
        if fname != '':
            self.w_lbl13.setText(fname)
            self.w_lbl14.setText(check_excel_input_file(self, fname))

    def cancelClicked(self):

        self.close_down()

    def exitClicked(self):

        # write last GUI selections
        write_config_file(self)

        self.close_down()

    def close_down(self):
        '''
        exit cleanly
        '''

        # close various files
        # ===================
        if hasattr(self, 'fobjs'):
            for key in self.fobjs:
                self.fobjs[key].close()

        # close logging
        # =============
        try:
            self.lgr.handlers[0].close()
        except AttributeError:
            pass

        sleep(2)
        self.close()

    def saveClicked(self):

        func_name =  __prog__ + ' saveClicked'

        write_config_file(self) # write last GUI selections

def main():
    """

    """
    app = QApplication(sys.argv)  # create QApplication object
    form = Form() # instantiate form
    # display the GUI and start the event loop if we're not running batch mode
    form.show()             # paint form
    sys.exit(app.exec_())   # start event loop

if __name__ == '__main__':
    main()
