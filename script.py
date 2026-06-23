# coding: latin-1
import os
import re
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

DEFAULT_TCPIP_RESOURCES = [
    'TCPIP0::10.1.1.2::inst0::INSTR',
    'TCPIP0::10.1.1.2::5025::SOCKET',
    'TCPIP0::10.1.1.2::gpib0,17::INSTR',
]
rm = None
instrument = None

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


def ask_for_int(resource, command):
    return int(float(str(ask(resource, command)).strip()))


def configure_ascii_data_transfer(resource):
    resource.write('FORM4')


def primary_trace_values(values, expected_points, command):
    values = list(values)
    if len(values) >= expected_points * 2:
        return [values[2*x] for x in range(expected_points)]
    if len(values) == expected_points:
        return values
    raise ValueError(
        '%s returned %s values for %s points; expected %s or %s.'
        % (command, len(values), expected_points, expected_points, expected_points * 2)
    )


def safe_float(text, field_name):
    try:
        return float(str(text).replace(',', '.'))
    except ValueError:
        raise ValueError('%s must be a numeric value.' % field_name)


def optional_float(text, field_name):
    text = str(text).strip()
    if not text:
        return None
    value = safe_float(text, field_name)
    if value <= 0:
        raise ValueError('%s must be greater than zero.' % field_name)
    return value


def safe_filename(name):
    filename = re.sub(r'[<>:"/\\|?*]+', '_', str(name)).strip()
    return filename or 'measurement'


def compute_response(freq, impedance, theta, diameter_mm=None, thickness_mm=None):
    freq = np.asarray(freq, dtype=float)
    impedance = np.asarray(impedance, dtype=float)
    theta = np.asarray(theta, dtype=float)
    angle = theta*np.pi/180
    with np.errstate(divide='ignore', invalid='ignore'):
        zr = impedance*np.cos(angle)
        zi = impedance*np.sin(angle)*(-1)
        resistance = impedance/np.cos(angle)
        capacitance = zi/(zr*freq*resistance*2*np.pi)

    if diameter_mm is None or thickness_mm is None:
        er_value = np.full(freq.shape, np.nan, dtype=float)
        ei_value = np.full(freq.shape, np.nan, dtype=float)
    else:
        e0 = 8.85418782e-12
        thickness_m = thickness_mm*10**(-3)
        diameter_m = diameter_mm*10**(-3)
        area = (np.pi*(diameter_m**2))/4
        with np.errstate(divide='ignore', invalid='ignore'):
            er_value = (capacitance*thickness_m)/(e0*area)
            ei_value = er_value*np.tan((90+theta)*np.pi/180)

    return zr, zi, resistance, capacitance, er_value, ei_value


def has_permittivity_data(er_value, ei_value):
    return bool(np.any(np.isfinite(er_value)) and np.any(np.isfinite(ei_value)))


def metadata_value(value):
    return 'N/A' if value is None else value


def wait_for_operation_complete(resource):
    old_timeout = getattr(resource, 'timeout', None)
    try:
        resource.timeout = None
        resource.write('*WAI')
        ask(resource, '*OPC?')
    finally:
        resource.timeout = old_timeout


def is_tcpip_resource(address):
    return str(address).strip().upper().startswith('TCPIP')


def resource_manager(simulation=False, py_backend=False):
    if simulation:
        return visa.ResourceManager('@sim')
    if py_backend:
        return visa.ResourceManager('@py')
    return visa.ResourceManager()


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
        self.populate_default_tcpip_resources()
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
            ui.label_11: 'D opt. (mm):',
            ui.label_12: 't opt. (mm):',
            ui.btn_plot_permi: 'eps (geom)',
            ui.btn_plot_ZT: 'Z/Theta',
            ui.btn_plot_RC: 'R/C',
            ui.label_29: 'Start:',
            ui.label_28: 'Stop:',
            ui.label_31: 'Points:',
            ui.var_log_4: 'Log',
            ui.checkbox_ptavg_4: 'Average',
            ui.label_34: 'Avg.:',
            ui.label_38: 'Sample ID',
            ui.label_35: 'D opt. (mm):',
            ui.label_36: 't opt. (mm):',
            ui.label_43: 'Sample ID',
            ui.label_46: 'Start:',
            ui.label_45: 'Stop:',
            ui.label_48: 'Points:',
            ui.label_52: 'Average:',
            ui.label_51: 'Avg.:',
            ui.label_40: 'D opt. (mm):',
            ui.label_41: 't opt. (mm):',
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
            label.setFixedWidth(220)

        for radio in [ui.var_log, ui.var_lin, ui.var_log_2, ui.var_lin_2, ui.var_log_4, ui.var_lin_4]:
            radio.setFixedWidth(80)
            radio.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        for layout in [ui.horizontalLayout_15, ui.horizontalLayout_8, ui.horizontalLayout_31]:
            layout.setSpacing(8)
            layout.setStretch(0, 0)
            layout.setStretch(1, 0)
            layout.setStretch(2, 0)

        ui.horizontalLayout_15.insertSpacing(1, 28)
        ui.horizontalLayout_8.insertSpacing(1, 28)
        ui.horizontalLayout_31.insertSpacing(1, 28)

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
        ui.combobox_equipamentos.setEditable(True)
        ui.combobox_equipamentos.setMinimumWidth(270)
        ui.tabWidget.setTabText(ui.tabWidget.indexOf(ui.tab), 'Connection')
        ui.tabWidget.setTabText(ui.tabWidget.indexOf(ui.tab_2), 'Analysis')
        ui.tabWidget.setTabText(ui.tabWidget.indexOf(ui.tab_3), 'Program')

    # Metodos
    def populate_default_tcpip_resources(self):
        existing = [
            self.ui.combobox_equipamentos.itemText(index)
            for index in range(self.ui.combobox_equipamentos.count())
        ]
        for address in DEFAULT_TCPIP_RESOURCES:
            if address not in existing:
                self.ui.combobox_equipamentos.addItem(address)

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
        diametro = None
        espessura = None
        with open(file_path) as arquivo:
            for line in arquivo:
                normalized_line = line.strip()
                normalized_key = normalized_line.split()[0] if normalized_line.split() else ''
                normalized_key_lower = normalized_key.lower()
                if normalized_key in ('#D(mm)', '#D'):
                    value = line.rstrip('\n').split()[-1]
                    if value.upper() != 'N/A':
                        diametro = safe_float(value, 'Sample diameter')
                if normalized_key in ('#d(mm)', '#d'):
                    value = line.rstrip('\n').split()[-1]
                    if value.upper() != 'N/A':
                        espessura = safe_float(value, 'Sample thickness')
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
        d = None if espessura is None else espessura*10**(-3)
        D = None if diametro is None else diametro*10**(-3)
        Zr, Zi, R, C, er, ei = compute_response(Freq, Z, Theta, diametro, espessura)
        self.ui.btn_plot_ZrZi.setEnabled(True)
        self.ui.btn_plot_ZT.setEnabled(True)
        self.ui.btn_plot_permi.setEnabled(has_permittivity_data(er, ei))
        self.ui.btn_plot_RC.setEnabled(True)
        self.ui.groupBox__amostra.setEnabled(True)
        self.ui.groupBox_analise.setEnabled(True)
        self.ui.amostra_id.setText(amostra)
        self.ui.LineEdit_SavePath.setText(path)
        self.ui.tbox_diametro.setText('' if diametro is None else str(diametro))
        self.ui.tbox_espessura.setText('' if espessura is None else str(espessura))
        self.ui.spin_freq_inicial.setValue(int(Freq[0]))
        self.ui.spin_freq_final.setValue(int(Freq[-1]))
        self.ui.num_pontos.setValue(int(nop))
        if has_permittivity_data(er, ei):
            self.plot_erei()
        else:
            self.plot_ZT()
        self.update_table(np.ndarray.tolist(Freq), np.ndarray.tolist(Z), np.ndarray.tolist(Theta),
                          np.ndarray.tolist(er), np.ndarray.tolist(ei))

    def instrument_detection(self):
        global rm
        try:
            is_simulation = self.ui.checkbox_pyvisasim.checkState()
            rm = resource_manager(simulation=is_simulation)
            equipaments = list(rm.list_resources())
            self.ui.combobox_equipamentos.clear()
            self.ui.combobox_equipamentos.addItems(equipaments)
            if not is_simulation:
                self.populate_default_tcpip_resources()
        except Exception:
            self.ui.combobox_equipamentos.clear()
            self.populate_default_tcpip_resources()
            self.show_error(
                'VISA detection error',
                'Could not detect VISA instruments. Ethernet addresses were added manually.',
                traceback.format_exc()
                + '\n\nFor Ethernet, try TCPIP0::10.1.1.2::inst0::INSTR first. '
                + 'If the system VISA backend is not available, install pyvisa-py or verify '
                + 'the Keysight/NI VISA driver installation.',
            )

    def instrument_connection(self):
        global instrument, rm
        address = str(self.ui.combobox_equipamentos.currentText()).strip()
        if not address:
            self.show_error(
                'Connection error',
                'No VISA address selected.',
            )
            return
        try:
            try:
                rm
            except NameError:
                rm = resource_manager(
                    simulation=self.ui.checkbox_pyvisasim.checkState()
                )
            instrument = rm.open_resource(unicode(address))
        except Exception:
            first_error = traceback.format_exc()
            if is_tcpip_resource(address) and not self.ui.checkbox_pyvisasim.checkState():
                try:
                    rm = resource_manager(py_backend=True)
                    instrument = rm.open_resource(unicode(address))
                except Exception:
                    self.show_error(
                        'Connection error',
                        'Could not connect to the selected TCPIP instrument.',
                        'Tried the system VISA backend and pyvisa-py.\n\n'
                        'System VISA error:\n'
                        + first_error
                        + '\n\npyvisa-py error:\n'
                        + traceback.format_exc(),
                    )
                    return
            else:
                self.show_error(
                    'Connection error',
                    'Could not connect to the selected instrument.',
                    'Please verify that the equipment is turned on, connected, and that the required VISA driver is installed.\n\n'
                    + first_error,
                )
                return
        try:
            if is_tcpip_resource(address) and address.upper().endswith('::SOCKET'):
                instrument.write_termination = '\n'
                instrument.read_termination = '\n'
            instrument.timeout = 10000
            instrument_name = ask(instrument, '*IDN?')
            self.ui.label_inst_name.setText(instrument_name)
            self.ui.group_calibration.setEnabled(True)
        except Exception:
            instrument = None
            self.show_error(
                'Instrument query error',
                'Connected to the resource, but could not read the instrument identification.',
                traceback.format_exc(),
            )


    def open_calibration(self):
        try:
            self._open_calibration()
        except Exception:
            self.show_error(
                'Open compensation error',
                'Could not complete the OPEN compensation.',
                traceback.format_exc(),
            )

    def _open_calibration(self):
        if instrument is None:
            self.show_error(
                'Instrument error',
                'Instrument not connected or not recognized.',
            )
            return
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
        try:
            self._short_calibration()
        except Exception:
            self.show_error(
                'Short compensation error',
                'Could not complete the SHORT compensation.',
                traceback.format_exc(),
            )

    def _short_calibration(self):
        if instrument is None:
            self.show_error(
                'Instrument error',
                'Instrument not connected or not recognized.',
            )
            return
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

    def optional_geometry(self):
        diametro = optional_float(self.ui.tbox_diametro.text(), 'Sample diameter')
        espessura = optional_float(self.ui.tbox_espessura.text(), 'Sample thickness')
        if (diametro is None) != (espessura is None):
            raise ValueError(
                'Provide both D and t to calculate permittivity, or leave both blank for generic impedance analysis.'
            )
        return diametro, espessura

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
        try:
            self.optional_geometry()
        except ValueError as error:
            warning = QtGui.QMessageBox()
            warning.setIcon(QtGui.QMessageBox.Warning)
            warning.setText(str(error))
            warning.addButton('Ok', QtGui.QMessageBox.AcceptRole)
            warning.exec_()
            self.ui.tbox_diametro.hasFocus()
            return False
        return True


    def run_analysis(self):
        try:
            self._run_analysis()
        except Exception:
            self.show_error(
                'Acquisition error',
                'The instrument sweep finished, but the data could not be collected or processed.',
                traceback.format_exc(),
            )

    def _run_analysis(self):
        if instrument is None:
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
        diametro, espessura = self.optional_geometry()
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
        configure_ascii_data_transfer(instrument)
        instrument.write('TRAC A')
        nop = ask_for_int(instrument, 'POIN?')
        Z_data = ask_for_values(instrument, 'OUTPDTRC?')
        Z = primary_trace_values(Z_data, nop, 'OUTPDTRC? TRAC A')
        instrument.write('TRAC B')
        Theta_data = ask_for_values(instrument, 'OUTPDTRC?')
        Theta = primary_trace_values(Theta_data, nop, 'OUTPDTRC? TRAC B')
        Freq = ask_for_values(instrument, 'OUTPSWPRM?')
        if len(Freq) != nop:
            raise ValueError(
                'OUTPSWPRM? returned %s frequency values for %s points.'
                % (len(Freq), nop)
            )
        Z = np.asarray(Z)
        Theta = np.asarray(Theta)
        Freq = np.asarray(Freq)
        #stats = instrument.ask_for_values('MEASTAT?')
        d = None if espessura is None else espessura*10**(-3)
        D = None if diametro is None else diametro*10**(-3)
        Zr, Zi, R, C, er, ei = compute_response(Freq, Z, Theta, diametro, espessura)
        if has_permittivity_data(er, ei):
            self.plot_erei()
        else:
            self.plot_ZT()
        self.update_table(Freq, Z, Theta, np.ndarray.tolist(er), np.ndarray.tolist(ei))
        path = str(self.ui.LineEdit_SavePath.text())
        filename = safe_filename(id_amostra)
        M = np.c_[np.asarray(Freq), np.asarray(Z), np.asarray(Theta), er, ei]
        np.savetxt(os.path.join(path, '%s.txt' % filename), M, fmt='%1.4e',
                   delimiter='\t',
                   header='#Freq(Hz)\t Z(ohms)\t Phase(degrees) \t er_Re \t er_Im',
                   comments='#Sample %s\n#d(mm)  %s\n#D(mm) %s \n#Sweep  %s \n#Voltage  %s'
                            % (
                                id_amostra,
                                metadata_value(espessura),
                                metadata_value(diametro),
                                sweepcmd,
                                self.ui.spinbox_tensao.value(),
                            ))
        self.ui.btn_plot_ZrZi.setEnabled(True)
        self.ui.btn_plot_ZT.setEnabled(True)
        self.ui.btn_plot_permi.setEnabled(has_permittivity_data(er, ei))
        self.ui.btn_plot_RC.setEnabled(True)

    def dynamic_analysis(self):
        try:
            self._dynamic_analysis()
        except Exception:
            self.show_error(
                'Acquisition error',
                'The dynamic sweep finished, but the data could not be collected or processed.',
                traceback.format_exc(),
            )

    def _dynamic_analysis(self):
        #message = QtGui.QMessageBox()
        #message.setText('Fun\E7\E3o ainda em constru\E7\E3o.')
        #message.setDetailedText('Por favor, utilize o modo padr\E3o de an\E1lise por enquanto.')
        #message.exec_()
        #return
        if instrument is None:
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
        diametro, espessura = self.optional_geometry()
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
        configure_ascii_data_transfer(instrument)
        instrument.write('TRAC A')
        nop = ask_for_int(instrument, 'POIN?')
        Z_data = ask_for_values(instrument, 'OUTPDTRC?')
        Z = primary_trace_values(Z_data, nop, 'OUTPDTRC? TRAC A')
        instrument.write('TRAC B')
        Theta_data = ask_for_values(instrument, 'OUTPDTRC?')
        Theta = primary_trace_values(Theta_data, nop, 'OUTPDTRC? TRAC B')
        Freq = ask_for_values(instrument, 'OUTPSWPRM?')
        if len(Freq) != nop:
            raise ValueError(
                'OUTPSWPRM? returned %s frequency values for %s points.'
                % (len(Freq), nop)
            )
        Z = np.asarray(Z)
        Theta = np.asarray(Theta)
        Freq = np.asarray(Freq)
        #stats = instrument.ask_for_values('MEASTAT?')
        d = None if espessura is None else espessura*10**(-3)
        D = None if diametro is None else diametro*10**(-3)
        Zr, Zi, R, C, er, ei = compute_response(Freq, Z, Theta, diametro, espessura)
        if has_permittivity_data(er, ei):
            self.plot_erei()
        else:
            self.plot_ZT()
        self.update_table(Freq, Z, Theta, np.ndarray.tolist(er), np.ndarray.tolist(ei))
        path = str(self.ui.LineEdit_SavePath.text())
        filename = safe_filename(id_amostra)
        M = np.c_[np.asarray(Freq), np.asarray(Z), np.asarray(Theta), er, ei]
        np.savetxt(os.path.join(path, '%s.txt' % filename), M, fmt='%1.4e',
                   delimiter='\t',
                   header='#Freq(Hz)\t Z(ohms)\t Phase(degrees) \t er_Re \t er_Im',
                   comments='#sample %s\n#d(mm) = %s\n#D(mm) = %s \n#sweep = %s \n#voltage = %s'
                            % (
                                id_amostra,
                                metadata_value(espessura),
                                metadata_value(diametro),
                                sweepcmd,
                                self.ui.spinbox_tensao.value(),
                            ))
        self.ui.btn_plot_ZrZi.setEnabled(True)
        self.ui.btn_plot_ZT.setEnabled(True)
        self.ui.btn_plot_permi.setEnabled(has_permittivity_data(er, ei))
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
        try:
            er_data = er
            ei_data = ei
        except NameError:
            self.show_error(
                'Permittivity unavailable',
                'No measurement data is loaded.',
            )
            return
        if not has_permittivity_data(er_data, ei_data):
            self.show_error(
                'Permittivity unavailable',
                'Permittivity requires both D and t. Leave them blank for generic impedance analysis and use Z/Theta, R/C, or Zr/Zi plots.',
            )
            return
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
