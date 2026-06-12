import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5 import QtWidgets

import script


class FakeInstrument:
    def __init__(self):
        self.timeout = 1000
        self.commands = []

    def write(self, command):
        self.commands.append(command)

    def query(self, command):
        self.commands.append(command)
        if command == 'POIN?':
            return '2'
        return '1'

    def query_ascii_values(self, command):
        self.commands.append(command)
        if command == 'OUTPDTRC?':
            return [1000.0, 0.0, 2000.0, 0.0]
        if command == 'OUTPSWPRM?':
            return [100.0, 1000.0]
        return []


def assert_group_gap(first, second, minimum=10):
    gap = second.y() - (first.y() + first.height())
    assert gap >= minimum, '%s overlaps %s: gap=%s' % (
        first.objectName(),
        second.objectName(),
        gap,
    )


def assert_radio_gap(log_radio, linear_radio, expected=8):
    gap = linear_radio.geometry().x() - (log_radio.geometry().x() + log_radio.width())
    assert gap == expected, 'unexpected radio gap: %s' % gap


def main():
    app = QtWidgets.QApplication([])
    window = script.StartQT4()

    assert window.minimumWidth() >= 1180
    assert window.minimumHeight() >= 760
    assert window.ui.tabWidget.tabText(0) == 'Connection'
    assert window.ui.label.text() == 'Connected:'
    assert window.ui.tableView.height() >= 180

    assert_group_gap(window.ui.groupBox, window.ui.groupBox_analise_2)
    assert_group_gap(window.ui.groupBox_analise_2, window.ui.group_calibration)
    assert_group_gap(window.ui.groupBox__amostra, window.ui.groupBox_analise)
    assert_group_gap(window.ui.groupBox_analise, window.ui.btn_run)
    assert_group_gap(window.ui.groupBox__amostra_2, window.ui.groupBox_analise_3)
    for tab_index, log_radio, linear_radio in [
        (0, window.ui.var_log_2, window.ui.var_lin_2),
        (1, window.ui.var_log, window.ui.var_lin),
        (2, window.ui.var_log_4, window.ui.var_lin_4),
    ]:
        window.ui.tabWidget.setCurrentIndex(tab_index)
        app.processEvents()
        assert_radio_gap(log_radio, linear_radio)

    window.ui.checkbox_pyvisasim.setChecked(True)
    window.instrument_detection()
    assert window.ui.combobox_equipamentos.count() > 0

    original_get_open_file_name = script.QtGui.QFileDialog.getOpenFileName
    script.QtGui.QFileDialog.getOpenFileName = lambda *args, **kwargs: (os.path.join('samples', 'sample1.txt'), '*.txt')
    try:
        window.ui.actionImportar_Dados.trigger()
    finally:
        script.QtGui.QFileDialog.getOpenFileName = original_get_open_file_name

    assert window.ui.amostra_id.text() == 'RC_RC_0'
    assert window.ui.num_pontos.value() == 400
    assert window.ax1.get_xlabel() == 'Frequency (Hz)'
    assert window.table_model.headerdata == ['Freq (Hz)', 'Z (Ohms)', 'Phase (deg)', "eps'", "eps''"]

    script.instrument = FakeInstrument()
    window.ui.amostra_id.setText('audit_fake')
    window.ui.LineEdit_SavePath.setText(tempfile.gettempdir())
    window.ui.tbox_diametro.setText('1.0')
    window.ui.tbox_espessura.setText('1.0')
    window.ui.num_pontos.setValue(2)
    window.ui.spin_freq_inicial.setValue(100)
    window.ui.spin_freq_final.setValue(1000)
    window.run_analysis()

    output_path = os.path.join(tempfile.gettempdir(), 'audit_fake.txt')
    assert os.path.exists(output_path)
    assert window.ui.tableView.model().rowCount(None) == 2
    os.remove(output_path)

    print('smoke test ok')
    app.quit()


if __name__ == '__main__':
    main()
