# coding: latin-1
import os
import sys
import tempfile
import traceback
import warnings

from numpy import random

os.environ.setdefault(
    "MPLCONFIGDIR",
    os.path.join(tempfile.gettempdir(), "ImpedanceAnalyze4294A-matplotlib"),
)

import numpy as np
import matplotlib
matplotlib.use("Qt5Agg")
try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
    from PyQt5 import QtCore, QtGui, QtWidgets
    QtGui.QMainWindow = QtWidgets.QMainWindow
    QtGui.QWidget = QtWidgets.QWidget
    QtGui.QApplication = QtWidgets.QApplication
    QtGui.QMessageBox = QtWidgets.QMessageBox
    QtGui.QFileDialog = QtWidgets.QFileDialog
    QtCore.QVariant = lambda value=None: value
except ImportError:
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
    from PyQt4 import QtCore, QtGui
import matplotlib.pyplot as plt
try:
    import visa
except ImportError:
    import pyvisa as visa
from interface import Ui_MainWindow

__author__ = 'giovanirech'

try:
    unicode
except NameError:
    unicode = str

try:
    xrange
except NameError:
    xrange = range


def ask(resource, command):
    if hasattr(resource, 'ask'):
        return resource.ask(command)
    return resource.query(command)


def ask_for_values(resource, command):
    if hasattr(resource, 'ask_for_values'):
        return resource.ask_for_values(command)
    return resource.query_ascii_values(command)


def wait_for_operation_complete(resource):
    old_timeout = getattr(resource, 'timeout', None)
    try:
        resource.timeout = None
        resource.write('*WAI')
        ask(resource, '*OPC?')
    finally:
        resource.timeout = old_timeout


def clear_figure(figure):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore',
            message='Attempt to set non-positive xlim on a log-scaled axis will be ignored.',
            category=UserWarning,
        )
        figure.clear()


class StartQT4(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(StartQT4, self).__init__(parent)
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.apply_layout_fixes()
        self.showMaximized()
        # Conexao de elementos da interface grafica
        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ui.btn_detectar.clicked.connect(self.instrument_detection)
        self.ui.btn_conectar.clicked.connect(self.instrument_connection)
        self.ui.btn_opencal.clicked.connect(self.open_calibration)
        self.ui.btn_shortcal.clicked.connect(self.short_calibration)
        self.ui.btn_run.clicked.connect(self.run_analysis)
        self.ui.toolbtn_savepath.clicked.connect(self.get_save_path)
        self.ui.btn_plot.clicked.connect(self.plot_test)
        self.ui.btn_plot_permi.clicked.connect(self.plot_erei)
        self.ui.btn_plot_RC.clicked.connect(self.plot_RC)
        self.ui.btn_plot_ZT.clicked.connect(self.plot_ZT)
        self.ui.btn_plot_ZrZi.clicked.connect(self.plot_ZrZi)
        self.ui.actionImportar_Dados.triggered.connect(self.importar_dados)
        self.ui.blt_skipcal.clicked.connect(self.skip_calibration)
        self.is_open_calibrated = False
        self.is_short_calibrated = False
        layout = self.ui.verticalLayout
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def apply_layout_fixes(self):
        self.setMinimumSize(1180, 760)
        ui = self.ui

        # The original PyQt4 UI uses fixed geometry. PyQt5/Windows fonts need a
        # more room to avoid clipped labels, squeezed fields, and overlapping
        # group boxes.
        left_x = 10
        left_width = 410
        content_x = 440
        content_width = 710

        # Connection tab.
        ui.groupBox.setGeometry(left_x, 10, left_width, 170)
        ui.groupBox_analise_2.setGeometry(left_x, 195, left_width, 285)
        ui.group_calibration.setGeometry(left_x, 495, left_width, 80)

        # Analysis tab.
        ui.groupBox__amostra.setGeometry(left_x, 10, left_width, 275)
        ui.groupBox_analise.setGeometry(left_x, 300, left_width, 285)
        ui.btn_run.setGeometry(left_x + 10, 600, left_width - 20, 32)
        ui.layoutWidget.setGeometry(content_x, 10, content_width, 350)
        ui.layoutWidget1.setGeometry(content_x + 20, 378, content_width - 40, 34)
        ui.tableView.setGeometry(content_x + 20, 425, content_width - 40, 190)

        # Program tab.
        ui.groupBox__amostra_2.setGeometry(left_x, 10, left_width, 275)
        ui.groupBox_analise_3.setGeometry(left_x, 300, left_width, 285)
        ui.listWidget.setGeometry(content_x, 10, 340, 520)
        ui.frame.setGeometry(content_x + 360, 10, 350, 520)
        ui.pushButton.setGeometry(content_x, 545, 170, 32)
        ui.commandLinkButton.setGeometry(content_x + 410, 540, 280, 50)

        text_updates = {
            ui.label: 'Connected:',
            ui.label_15: 'Start:',
            ui.label_14: 'Stop:',
            ui.label_17: 'Points:',
            ui.var_log_2: 'Log',
            ui.checkbox_ptavg_2: 'Average',
            ui.label_20: 'Avg.:',
            ui.label_4: 'Start:',
            ui.label_5: 'Stop:',
            ui.label_6: 'Points:',
            ui.var_log: 'Log',
            ui.checkbox_ptavg: 'Average',
            ui.label_10: 'Avg.:',
            ui.label_2: 'Sample ID',
            ui.label_11: 'D (mm):',
            ui.label_12: 't (mm):',
            ui.btn_plot_permi: 'eps vs f',
            ui.btn_plot_ZT: 'Z/Theta',
            ui.btn_plot_RC: 'R/C',
            ui.label_29: 'Start:',
            ui.label_28: 'Stop:',
            ui.label_31: 'Points:',
            ui.var_log_4: 'Log',
            ui.checkbox_ptavg_4: 'Average',
            ui.label_34: 'Avg.:',
            ui.label_38: 'Sample ID',
            ui.label_35: 'D (mm):',
            ui.label_36: 't (mm):',
            ui.label_43: 'Sample ID',
            ui.label_46: 'Start:',
            ui.label_45: 'Stop:',
            ui.label_48: 'Points:',
            ui.label_52: 'Average:',
            ui.label_51: 'Avg.:',
            ui.label_40: 'D (mm):',
            ui.label_41: 't (mm):',
            ui.pushButton: 'Delete',
            ui.commandLinkButton: 'Start Program',
        }

        for widget, text in text_updates.items():
            widget.setText(text)

        for label in [
            ui.label_4, ui.label_5, ui.label_6, ui.label_8, ui.label_9, ui.label_10,
            ui.label_15, ui.label_14, ui.label_17, ui.label_19, ui.label_18, ui.label_20,
            ui.label_29, ui.label_28, ui.label_31, ui.label_33, ui.label_32, ui.label_34,
        ]:
            label.setMinimumWidth(80)

        for label in [ui.label_7, ui.label_16, ui.label_30]:
            label.setFixedWidth(170)

        for radio in [ui.var_log, ui.var_lin, ui.var_log_2, ui.var_lin_2, ui.var_log_4, ui.var_lin_4]:
            radio.setFixedWidth(100)
            radio.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        for layout in [ui.horizontalLayout_15, ui.horizontalLayout_8, ui.horizontalLayout_31]:
            layout.setSpacing(8)
            layout.setStretch(0, 0)
            layout.setStretch(1, 0)
            layout.setStretch(2, 0)

        ui.horizontalLayout_15.setAlignment(ui.var_log_2, QtCore.Qt.AlignLeft)
        ui.horizontalLayout_15.setAlignment(ui.var_lin_2, QtCore.Qt.AlignLeft)
        ui.horizontalLayout_8.setAlignment(ui.var_log, QtCore.Qt.AlignLeft)
        ui.horizontalLayout_8.setAlignment(ui.var_lin, QtCore.Qt.AlignLeft)
        ui.horizontalLayout_31.setAlignment(ui.var_log_4, QtCore.Qt.AlignLeft)
        ui.horizontalLayout_31.setAlignment(ui.var_lin_4, QtCore.Qt.AlignLeft)
        ui.horizontalLayout_2.setAlignment(ui.horizontalLayout_8, QtCore.Qt.AlignLeft)

        for field in [
            ui.spin_freq_inicial, ui.spin_freq_final, ui.num_pontos,
            ui.spinbox_tensao, ui.spinbox_banda, ui.spin_ptavg,
            ui.spin_freq_inicial_2, ui.spin_freq_final_2, ui.num_pontos_2,
            ui.spinbox_tensao_2, ui.spinbox_banda_2, ui.spin_ptavg_2,
            ui.spin_freq_inicial_4, ui.spin_freq_final_4, ui.num_pontos_4,
            ui.spinbox_tensao_4, ui.spinbox_banda_4, ui.spin_ptavg_4,
        ]:
            field.setMinimumWidth(150)

        for button in [
            ui.btn_detectar, ui.btn_conectar, ui.btn_shortcal, ui.btn_opencal,
            ui.blt_skipcal, ui.btn_plot_permi, ui.btn_plot_ZT, ui.btn_plot_RC,
            ui.btn_plot_ZrZi, ui.pushButton,
        ]:
            button.setMinimumHeight(28)

        ui.btn_conectar.setMaximumWidth(120)
        ui.commandLinkButton.setMinimumWidth(300)
        ui.tableView.setAlternatingRowColors(True)
        ui.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        ui.tableView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        ui.tableView.horizontalHeader().setStretchLastSection(True)
        ui.tableView.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignCenter)
        ui.tableView.verticalHeader().setDefaultSectionSize(22)
        ui.tabWidget.setTabText(ui.tabWidget.indexOf(ui.tab), 'Connection')
        ui.tabWidget.setTabText(ui.tabWidget.indexOf(ui.tab_2), 'Analysis')
        ui.tabWidget.setTabText(ui.tabWidget.indexOf(ui.tab_3), 'Program')

    # Metodos
    def skip_calibration(self):
        warning = QtGui.QMessageBox()
        warning.setText('Are you sure you want to skip calibration? Without geometry compensation, the collected data'
                        'may be contaminated with the effect of resistivity and capacitance of the accessories, cables and conections.')
        warning.setIcon(QtGui.QMessageBox.Warning)
        warning.addButton('Continue', QtGui.QMessageBox.AcceptRole)
        warning.addButton('Cancel', QtGui.QMessageBox.RejectRole)
        warning.exec_()
        btnclicked = warning.clickedButton().text()
        if btnclicked == 'Continue':
            self.ui.groupBox_analise.setEnabled(True)
            self.ui.groupBox__amostra.setEnabled(True)
            self.ui.btn_run.setEnabled(True)
        else:
            pass

    def show_error(self, title, text, detail=None):
        message = QtGui.QMessageBox(self)
        message.setIcon(QtGui.QMessageBox.Critical)
        message.setWindowTitle(title)
        message.setText(text)
        if detail:
            message.setDetailedText(detail)
        message.addButton('Ok', QtGui.QMessageBox.AcceptRole)
        message.exec_()

    def importar_dados(self, *args):
        try:
            file_path, _ = QtGui.QFileDialog.getOpenFileName(
                self,
                'Select the file',
                '',
                'Text files (*.txt);;All files (*)',
            )
            self.import_data_file(file_path)
        except Exception:
            self.show_error(
                'Import error',
                'Could not import the selected data file.',
                traceback.format_exc(),
            )

    def import_data_file(self, file_path):
        file_path = str(file_path)
        if not file_path:
            return

        path = os.path.dirname(file_path)
        data = np.genfromtxt(file_path, skip_header=0)
        if data.ndim == 1:
            data = data.reshape(1, -1)

        amostra = 'Identifiction not found'
        diametro = 1
        espessura = 1
        with open(file_path) as arquivo:
            for line in arquivo:
                normalized_line = line.strip()
                normalized_key = normalized_line.split()[0] if normalized_line.split() else ''
                normalized_key_lower = normalized_key.lower()
                if normalized_key in ('#D(mm)', '#D'):
                    diametro = float(line.rstrip('\n').split()[-1])
                if normalized_key in ('#d(mm)', '#d'):
                    espessura = float(line.rstrip('\n').split()[-1])
                if normalized_key_lower == '#sample':
                    amostra = ' '.join(line.rstrip('\n').split()[1:])
                if normalized_key_lower == '#sweep':
                    if line.rstrip('\n').split()[-1].lower() == 'lin':
                        self.ui.var_lin.setChecked(True)
                    else:
                        self.ui.var_log.setChecked(True)
        global Zr, Zi, R, C, er, ei, d, D, Theta, Freq, Z
        nop = len(data[:, 0])
        Freq = data[:, 0]
        Z = data[:, 1]
        Theta = data[:, 2]
        e0 = 8.85418782e-12
        d = espessura*10**(-3)
        D = diametro*10**(-3)
        # er = (2*d*np.cos(np.asarray(Theta)*np.pi/180))/(e0*np.asarray(Z)*np.asarray(Freq)*(D**2)*(np.pi*np.pi)*np.tan(np.asarray(Theta)*np.pi/180))
        A = (np.pi*(D**2))/4
        Zr = Z*np.cos(np.asarray(Theta)*np.pi/180)
        Zi = Z*np.sin(np.asarray(Theta)*np.pi/180)*(-1)
        R = Z/np.cos(np.asarray(Theta)*np.pi/180)
        C = Zi/(Zr*np.asarray(Freq)*R*2*np.pi)

        er = (C*d)/(e0*A)
        ei = er*np.tan((90+np.asarray(Theta))*np.pi/180)
        # ei = er*np.tan((90+np.asarray(Theta))*np.pi/180
        self.ui.btn_plot_ZrZi.setEnabled(True)
        self.ui.btn_plot_ZT.setEnabled(True)
        self.ui.btn_plot_permi.setEnabled(True)
        self.ui.btn_plot_RC.setEnabled(True)
        self.ui.groupBox__amostra.setEnabled(True)
        self.ui.groupBox_analise.setEnabled(True)
        self.ui.amostra_id.setText(amostra)
        self.ui.LineEdit_SavePath.setText(path)
        self.ui.tbox_diametro.setText(str(diametro))
        self.ui.tbox_espessura.setText(str(espessura))
        self.ui.spin_freq_inicial.setValue(int(Freq[0]))
        self.ui.spin_freq_final.setValue(int(Freq[-1]))
        self.ui.num_pontos.setValue(int(nop))
        self.plot_erei()
        self.update_table(np.ndarray.tolist(Freq), np.ndarray.tolist(Z), np.ndarray.tolist(Theta),
                          np.ndarray.tolist(er), np.ndarray.tolist(ei))

    def instrument_detection(self):
        global rm
        try:
            is_simulation = self.ui.checkbox_pyvisasim.checkState()
            if is_simulation:
                rm = visa.ResourceManager('@sim')
            else:
                rm = visa.ResourceManager()
            equipaments = list(rm.list_resources())
            self.ui.combobox_equipamentos.clear()
            self.ui.combobox_equipamentos.addItems(equipaments)
        except Exception:
            self.show_error(
                'VISA detection error',
                'Could not detect VISA instruments.',
                traceback.format_exc(),
            )

    def instrument_connection(self):
        global instrument
        address = self.ui.combobox_equipamentos.currentText()
        try:
            instrument = rm.open_resource(unicode(address))
        except Exception:
            self.show_error(
                'Connection error',
                'Could not connect to the selected instrument.',
                'Please verify that the equipment is turned on, connected, and that the required VISA driver is installed.\n\n'
                + traceback.format_exc(),
            )
            return
        try:
            instrument_name = ask(instrument, '*IDN?')
            self.ui.label_inst_name.setText(instrument_name)
            self.ui.group_calibration.setEnabled(True)
        except Exception:
            self.show_error(
                'Instrument query error',
                'Connected to the resource, but could not read the instrument identification.',
                traceback.format_exc(),
            )


    def open_calibration(self):
        instrument.write('HOLD')
        warning = QtGui.QMessageBox()
        warning.setText('Please, set the accessory to the OPEN configuration')
        warning.setIcon(QtGui.QMessageBox.Information)
        warning.addButton('Continue', QtGui.QMessageBox.AcceptRole)
        warning.addButton('Cancel', QtGui.QMessageBox.RejectRole)
        warning.exec_()
        response = warning.clickedButton().text()
        if response == 'Continue':
            instrument.write('E4TP OFF')
            instrument.write('TRGS INT')
            instrument.write('ESNB 1')
            instrument.write('*SRE 4')
            instrument.write('*CLS')
            instrument.write('COMA')
            wait_for_operation_complete(instrument)
            complete = QtGui.QMessageBox()
            complete.setText('OPEN compensation complete.')
            complete.setIcon(QtGui.QMessageBox.Information)
            complete.addButton('OK', QtGui.QMessageBox.AcceptRole)
            complete.exec_()
            self.is_open_calibrated = True
            if self.is_open_calibrated and self.is_short_calibrated:
                self.ui.groupBox_analise.setEnabled(True)
                self.ui.groupBox__amostra.setEnabled(True)
                self.ui.btn_run.setEnabled(True)
        else:
            pass

    def short_calibration(self):
        instrument.write('HOLD')
        warning = QtGui.QMessageBox()
        warning.setText('Please, set the accessory to the SHORT configuration')
        warning.setIcon(QtGui.QMessageBox.Information)
        warning.addButton('Continue', QtGui.QMessageBox.AcceptRole)
        warning.addButton('Cancel', QtGui.QMessageBox.RejectRole)
        warning.exec_()
        response = warning.clickedButton().text()
        if response == 'Continue':
            instrument.write('E4TP OFF')
            instrument.write('TRGS INT')
            instrument.write('ESNB 1')
            instrument.write('*SRE 4')
            instrument.write('*CLS')
            instrument.write('COMB')
            wait_for_operation_complete(instrument)
            complete = QtGui.QMessageBox()
            complete.setText('SHORT compensation complete.')
            complete.setIcon(QtGui.QMessageBox.Information)
            complete.addButton('OK', QtGui.QMessageBox.AcceptRole)
            complete.exec_()
            self.is_short_calibrated = True
            if self.is_open_calibrated and self.is_short_calibrated:
                self.ui.groupBox_analise.setEnabled(True)
                self.ui.groupBox__amostra.setEnabled(True)
                self.ui.btn_run.setEnabled(True)
        else:
            pass

    def get_save_path(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, 'Select destination folder')
        self.ui.LineEdit_SavePath.setText(path)

    def no_blank_fields(self):
        if str(self.ui.amostra_id.text()) == '':
            warning = QtGui.QMessageBox()
            warning.setIcon(QtGui.QMessageBox.Warning)
            warning.setText('You need t provide a identification to your sample.')
            warning.addButton('Ok', QtGui.QMessageBox.AcceptRole)
            warning.exec_()
            self.ui.amostra_id.hasFocus()
            return False
        if str(self.ui.LineEdit_SavePath.text()) == '':
            warning = QtGui.QMessageBox()
            warning.setIcon(QtGui.QMessageBox.Warning)
            warning.setText('Select a destination folder to save the colected data.')
            warning.addButton('Ok', QtGui.QMessageBox.AcceptRole)
            warning.exec_()
            return False
        if str(self.ui.tbox_diametro.text()) == '' or str(self.ui.tbox_espessura.text()) == '':
            warning = QtGui.QMessageBox()
            warning.setIcon(QtGui.QMessageBox.Warning)
            warning.setText('You need to provide the sample dimensions for permittivity and capacitance computations')
            warning.addButton('Ok', QtGui.QMessageBox.AcceptRole)
            warning.exec_()
            self.ui.tbox_diametro.hasFocus()
            return False
        return True


    def run_analysis(self):
        try:
            instrument
        except NameError:
            errorbox = QtGui.QMessageBox()
            errorbox.setIcon(QtGui.QMessageBox.Critical)
            errorbox.setText('Instrument no recognized or not connected.')
            errorbox.addButton('Ok', QtGui.QMessageBox.AcceptRole)
            errorbox.exec_()
            return
        if not(self.no_blank_fields()):
            return
        if self.ui.var_lin.isChecked():
            sweepcmd = 'LIN'
        else:
            sweepcmd = 'LOG'

        if self.ui.checkbox_ptavg.isChecked():
            paver = 'ON'
        else:
            paver = 'OFF'
        id_amostra = self.ui.amostra_id.text()
        diametro = float(self.ui.tbox_diametro.text())
        espessura = float(self.ui.tbox_espessura.text())
        instrument.write('STAR %s' %self.ui.spin_freq_inicial.value())
        instrument.write('STOP %s' %self.ui.spin_freq_final.value())
        instrument.write('POIN %s' %self.ui.num_pontos.value())
        instrument.write('POWMOD VOLT')
        instrument.write('POWE %s' %self.ui.spinbox_tensao.value())
        instrument.write('SWPT %s' %sweepcmd)
        instrument.write('BWFACT %s' %self.ui.spinbox_banda.value())
        instrument.write('PAVERFACT %s' %self.ui.spin_ptavg.value())
        instrument.write('PAVER %s' %paver)
        instrument.write('MEASTAT %s' %paver)
        instrument.write('MEAS IMPH')
        instrument.write('SING')
        instrument.write('TRGS INT')
        instrument.write('ESNB 1')
        instrument.write('*SRE 4')
        instrument.write('*CLS')
        wait_for_operation_complete(instrument)
        instrument.write('TRAC A')
        instrument.write('AUTO')
        instrument.write('TRAC B')
        instrument.write('AUTO')
        global Zr, Zi, R, C, er, ei, d, D, Theta, Freq, Z
        instrument.write('FORM5')
        instrument.write('TRAC A')
        nop = ask(instrument, 'POIN?')
        Z_data = ask_for_values(instrument, 'OUTPDTRC?')
        Z = [0] * int(nop)
        for x in range(0, int(nop)):
            Z[x] = Z_data[2*x]
        instrument.write('TRAC B')
        Theta_data = ask_for_values(instrument, 'OUTPDTRC?')
        Theta = [0] * int(nop)
        for x in range(0, int(nop)):
            Theta[x] = Theta_data[2*x]
        Freq = ask_for_values(instrument, 'OUTPSWPRM?')
        Z = np.asarray(Z)
        Theta = np.asarray(Theta)
        Freq = np.asarray(Freq)
        #stats = instrument.ask_for_values('MEASTAT?')
        e0 = 8.85418782e-12
        d = espessura*10**(-3)
        D = diametro*10**(-3)
        # er = (2*d*np.cos(np.asarray(Theta)*np.pi/180))/(e0*np.asarray(Z)*np.asarray(Freq)*(D**2)*(np.pi*np.pi)*np.tan(np.asarray(Theta)*np.pi/180))
        A = (np.pi*(D**2))/4
        Zr = Z*np.cos(np.asarray(Theta)*np.pi/180)
        Zi = Z*np.sin(np.asarray(Theta)*np.pi/180)*(-1)
        R = Z/np.cos(np.asarray(Theta)*np.pi/180)
        C = Zi/(Zr*np.asarray(Freq)*R*2*np.pi)

        er = (C*d)/(e0*A)
        ei = er*np.tan((90+np.asarray(Theta))*np.pi/180)
        # ei = er*np.tan((90+np.asarray(Theta))*np.pi/180
        self.plot_erei()
        self.update_table(Freq, Z, Theta, np.ndarray.tolist(er), np.ndarray.tolist(ei))
        path = str(self.ui.LineEdit_SavePath.text())
        filename = str(id_amostra)
        M = np.c_[np.asarray(Freq), np.asarray(Z), np.asarray(Theta), er, ei]
        np.savetxt(os.path.join(path, '%s.txt' % filename), M, fmt='%1.4e',
                   delimiter='\t',
                   header='#Freq(Hz)\t Z(ohms)\t Phase(degrees) \t er_Re \t er_Im',
                   comments='#Sample %s\n#d(mm)  %s\n#D(mm) %s \n#Sweep  %s \n#Voltage  %s'
                            % (id_amostra, espessura, diametro, sweepcmd, self.ui.spinbox_tensao.value()))
        self.ui.btn_plot_ZrZi.setEnabled(True)
        self.ui.btn_plot_ZT.setEnabled(True)
        self.ui.btn_plot_permi.setEnabled(True)
        self.ui.btn_plot_RC.setEnabled(True)

    def dynamic_analysis(self):
        #message = QtGui.QMessageBox()
        #message.setText('Fun\E7\E3o ainda em constru\E7\E3o.')
        #message.setDetailedText('Por favor, utilize o modo padr\E3o de an\E1lise por enquanto.')
        #message.exec_()
        #return
        try:
            instrument
        except NameError:
            errorbox = QtGui.QMessageBox()
            errorbox.setIcon(QtGui.QMessageBox.Critical)
            errorbox.setText('Instrument not connected or not recognized.')
            errorbox.addButton('Ok', QtGui.QMessageBox.AcceptRole)
            errorbox.exec_()
            return
        if not(self.no_blank_fields()):
            return
        if self.ui.var_lin.isChecked():
            sweepcmd = 'LIN'
        else:
            sweepcmd = 'LOG'

        if self.ui.checkbox_ptavg.isChecked():
            paver = 'ON'
        else:
            paver = 'OFF'
        id_amostra = self.ui.amostra_id.text()
        diametro = float(self.ui.tbox_diametro.text())
        espessura = float(self.ui.tbox_espessura.text())
        instrument.write('STAR %s' %self.ui.spin_freq_inicial.value())
        instrument.write('STOP %s' %self.ui.spin_freq_final.value())
        instrument.write('POIN %s' %self.ui.num_pontos.value())
        instrument.write('POWMOD VOLT')
        instrument.write('POWE %s' %self.ui.spinbox_tensao.value())
        instrument.write('SWPT %s' %sweepcmd)
        instrument.write('BWFACT %s' %self.ui.spinbox_banda.value())
        instrument.write('PAVERFACT %s' %self.ui.spin_ptavg.value())
        instrument.write('PAVER %s' %paver)
        instrument.write('MEASTAT %s' %paver)
        instrument.write('MEAS IMPH')
        instrument.write('MAN')
        instrument.write('TRGS INT')
        instrument.write('ESNB 1')
        instrument.write('*SRE 4')
        instrument.write('*CLS')
        wait_for_operation_complete(instrument)
        instrument.write('TRAC A')
        instrument.write('AUTO')
        instrument.write('TRAC B')
        instrument.write('AUTO')
        global Zr, Zi, R, C, er, ei, d, D, Theta, Freq, Z
        instrument.write('FORM5')
        instrument.write('TRAC A')
        nop = ask(instrument, 'POIN?')
        Z_data = ask_for_values(instrument, 'OUTPDTRC?')
        Z = [0] * int(nop)
        for x in range(0, int(nop)):
            Z[x] = Z_data[2*x]
        instrument.write('TRAC B')
        Theta_data = ask_for_values(instrument, 'OUTPDTRC?')
        Theta = [0] * int(nop)
        for x in range(0, int(nop)):
            Theta[x] = Theta_data[2*x]
        Freq = ask_for_values(instrument, 'OUTPSWPRM?')
        Z = np.asarray(Z)
        Theta = np.asarray(Theta)
        Freq = np.asarray(Freq)
        #stats = instrument.ask_for_values('MEASTAT?')
        e0 = 8.85418782e-12
        d = espessura*10**(-3)
        D = diametro*10**(-3)
        # er = (2*d*np.cos(np.asarray(Theta)*np.pi/180))/(e0*np.asarray(Z)*np.asarray(Freq)*(D**2)*(np.pi*np.pi)*np.tan(np.asarray(Theta)*np.pi/180))
        A = (np.pi*(D**2))/4
        Zr = Z*np.cos(np.asarray(Theta)*np.pi/180)
        Zi = Z*np.sin(np.asarray(Theta)*np.pi/180)*(-1)
        R = Z/np.cos(np.asarray(Theta)*np.pi/180)
        C = Zi/(Zr*np.asarray(Freq)*R*2*np.pi)

        er = (C*d)/(e0*A)
        ei = er*np.tan((90+np.asarray(Theta))*np.pi/180)
        # ei = er*np.tan((90+np.asarray(Theta))*np.pi/180
        self.plot_erei()
        self.update_table(Freq, Z, Theta, np.ndarray.tolist(er), np.ndarray.tolist(ei))
        path = str(self.ui.LineEdit_SavePath.text())
        filename = str(id_amostra)
        M = np.c_[np.asarray(Freq), np.asarray(Z), np.asarray(Theta), er, ei]
        np.savetxt(os.path.join(path, '%s.txt' % filename), M, fmt='%1.4e',
                   delimiter='\t',
                   header='#Freq(Hz)\t Z(ohms)\t Phase(degrees) \t er_Re \t er_Im',
                   comments='#sample %s\n#d(mm) = %s\n#D(mm) = %s \n#sweep = %s \n#voltage = %s'
                            % (id_amostra, espessura, diametro, sweepcmd, self.ui.spinbox_tensao.value()))
        self.ui.btn_plot_ZrZi.setEnabled(True)
        self.ui.btn_plot_ZT.setEnabled(True)
        self.ui.btn_plot_permi.setEnabled(True)
        self.ui.btn_plot_RC.setEnabled(True)

        # path = str(self.ui.LineEdit_SavePath.text())
        # filename = str(id_amostra)
        # M = np.c_[np.asarray(Freq), np.asarray(Z), np.asarray(Theta), er, ei]
        # np.savetxt('%s\%s.txt' % (path, filename), M, fmt='%1.4e',
        #           delimiter='\t',
        #           header='Freq(Hz)\t Z(ohms)\t Phase(degrees) \t er_Re \t er_Im',
        #           comments='#Amostra %s\n #d = %s \n #D = %s \n' % (id_amostra, espessura, diametro))

    def plot_test(self):
        data = [random.random() for i in range(10)]

        # create an axis
        ax = self.fig.add_subplot(111)

        # discards the old graph
        # plot data
        ax.plot(data, '*-')

        # refresh canvas
        self.canvas.draw()
        self.update_table(data, data, data, data, data)

    def plot_erei(self):
        self.plot_data(Freq, 'Frequency (Hz)', er, r"$\epsilon'$", ei, r"$\epsilon''$", 'log')

    def plot_RC(self):
        self.plot_data(Freq, 'Frequency (Hz)', R, 'R (Ohms)', C, 'C (F)', 'log')

    def plot_ZT(self):
        self.plot_data(Freq, 'Frequency (Hz)', Z, 'Impedance (Ohms)', Theta, 'Phase (degrees)', 'log')

    def plot_ZrZi(self):
        clear_figure(self.fig)
        self.ax1 = self.fig.add_subplot(111)
        self.ax1.plot(Zr, Zi, 'blue')
        self.ax1.set_title(self.ui.amostra_id.text(), fontsize='12')
        self.ax1.grid(which='both')
        self.ax1.set_xlabel('Real Impedance', fontsize='10')
        self.ax1.set_ylabel('Imaginary Impedance', fontsize='14', color='blue')
        self.ax1.set_xlim(min(Zr), max(Zr))
        self.fig.subplots_adjust(left=0.12, right=0.96, bottom=0.18, top=0.90)
        self.canvas.draw()

    def plot_data(self, x, labelx, y1, labely1, y2, labely2, xscale):
        """

        :rtype : object
        """
        clear_figure(self.fig)
        x = np.asarray(x)
        self.ax1 = self.fig.add_subplot(111)
        self.ax1.plot(x, y1, 'blue')
        self.ax1.set_title(self.ui.amostra_id.text(), fontsize='12')
        self.ax2 = self.ax1.twinx()
        self.ax2.plot(x, y2, 'green')
        self.ax1.grid(which='both')
        self.ax1.set_xlabel(labelx, fontsize='10', labelpad=8)
        self.ax1.set_ylabel(labely1, fontsize='14', color='blue')
        self.ax2.set_ylabel(labely2, fontsize='14', color='green')
        if xscale == 'log' and np.any(x <= 0):
            xscale = 'linear'
        self.ax1.set_xscale(xscale)
        self.ax2.set_xscale(xscale)
        self.ax1.set_xlim(x[0], x[-1])
        for i in self.ax1.get_yticklabels():
            i.set_color('blue')
        for i in self.ax2.get_yticklabels():
            i.set_color('green')
        self.fig.subplots_adjust(left=0.12, right=0.88, bottom=0.24, top=0.90)
        # plt.savefig('%s.png' %file_name.value, dpi = 300)
        # self.ui.plot_window.
        self.canvas.draw()

    def update_table(self, freq, imped, teta, er, ei):
        data = [freq, imped, teta, er, ei]
        header = ['Freq (Hz)', 'Z (Ohms)', 'Phase (deg)', "eps'", "eps''"]
        self.table_model = MyTableModel(data, header, parent=self)
        self.ui.tableView.setModel(self.table_model)
        # set row height
        nrows = len(data[0])
        for row in xrange(nrows):
            self.ui.tableView.setRowHeight(row, 22)
        available_width = max(620, self.ui.tableView.viewport().width() - 20)
        column_ratios = [0.20, 0.22, 0.17, 0.20, 0.21]
        for col, ratio in enumerate(column_ratios):
            self.ui.tableView.setColumnWidth(col, int(available_width * ratio))

class MyTableModel(QtCore.QAbstractTableModel):
    def __init__(self, datain, headerdata, parent=None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.arraydata = datain
        self.headerdata = headerdata
        self.rows = range(0, len(datain[0]))

    def rowCount(self, parent):
        return len(self.arraydata[0])

    def columnCount(self, parent):
        return len(self.arraydata)

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        return QtCore.QVariant(self.arraydata[index.column()][index.row()])

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self.headerdata[col])
        return QtCore.QVariant()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = StartQT4()
    myapp.show()
    sys.exit(app.exec_())
