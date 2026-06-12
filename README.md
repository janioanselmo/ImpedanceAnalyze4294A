# ImpedanceAnalyze4294A

Interface gráfica em Python/PyQt4 para aquisição, importação e análise de espectros de impedância com o analisador Keysight/Agilent 4294A.

---

## 🇧🇷 PT-BR

### Visão Geral

O **ImpedanceAnalyze4294A** é uma interface desktop baseada no projeto ImpedSpec para controle do analisador de impedância Keysight/Agilent 4294A, aquisição de espectros e visualização de propriedades elétricas de materiais dielétricos e circuitos.

A aplicação permite detectar/conectar o instrumento via VISA, executar calibração aberta/curta, configurar varreduras de frequência, coletar impedância/fase e calcular grandezas derivadas como resistência, capacitância, permissividade real e permissividade imaginária.

### Funcionalidades

- Interface gráfica em PyQt4.
- Detecção de instrumentos via VISA/PyVISA.
- Suporte a simulação por `pyvisa-sim`.
- Conexão com analisador Keysight/Agilent 4294A.
- Calibração **open** e **short** antes da aquisição.
- Configuração de frequência inicial/final, número de pontos, tensão, banda e média.
- Varredura linear ou logarítmica.
- Aquisição de impedância (`Z`) e fase (`Theta`).
- Cálculo de `Zr`, `Zi`, `R`, `C`, `epsilon'` e `epsilon''`.
- Importação de arquivos `.txt` gerados pelo próprio software.
- Visualização de gráficos: permissividade, `R/C`, `Z/Theta` e plano `Zr/Zi`.
- Exportação dos dados medidos em arquivo texto.

### Estrutura

| Arquivo | Descrição |
|---|---|
| `script.py` | Script principal da aplicação e rotinas de aquisição/análise |
| `interface.py` | Interface Python gerada a partir do arquivo `.ui` pelo `pyuic4` |
| `InterfaceImpedSpec.ui` | Layout Qt editável no Qt Designer |
| `requirements.txt` | Dependências Python instaláveis por `pip` |
| `run_windows.bat` | Criação de ambiente virtual, instalação de dependências e execução no Windows |
| `run_linux_mac.sh` | Criação de ambiente virtual, instalação de dependências e execução no Linux/macOS |
| `sample1.txt` | Arquivo de exemplo para importação |
| `sample2.txt` | Arquivo de exemplo para importação |
| `sample3.txt` | Arquivo de exemplo para importação |
| `LICENSE` | Licença GPL-3.0 |

### Dependências

Este projeto é legado e depende de bibliotecas do ecossistema Python 2/PyQt4:

```text
numpy
matplotlib
astropy
docutils
pyvisa
pyvisa-sim
PyQt4
```

Também é necessário ter os drivers do analisador 4294A instalados e corretamente reconhecidos pelo sistema operacional.

### Instalação

Em ambientes compatíveis com PyQt4:

```bash
pip install -r requirements.txt
```

No Fedora, o ambiente original indicava:

```bash
sudo dnf install pyqt4-devel
sudo dnf install python-matplotlib-qt
```

Em sistemas atuais, PyQt4 pode não estar disponível nos repositórios padrão. Nesse caso, use um ambiente legado compatível ou avalie portar a interface para PyQt5/PySide antes de executar em produção.

### Execução

```bash
python script.py
```

No Windows, também é possível criar o ambiente virtual, instalar dependências e executar com:

```bat
run_windows.bat
```

No Linux/macOS:

```bash
./run_linux_mac.sh
```

Para testar sem instrumento físico, habilite o modo de simulação na interface quando o ambiente `pyvisa-sim` estiver configurado.

### Uso Básico

1. Abra a aplicação com `python script.py`.
2. Detecte os instrumentos VISA disponíveis.
3. Selecione e conecte o analisador 4294A.
4. Execute a calibração **open** e **short** ou pule a calibração quando apropriado para teste.
5. Configure a amostra, faixa de frequência, número de pontos e parâmetros de aquisição.
6. Execute a análise.
7. Visualize os gráficos e salve os dados medidos.

### Formato dos Dados

Os arquivos exportados/importados armazenam colunas numéricas de frequência, impedância, fase e grandezas derivadas. Os arquivos `sample*.txt` podem ser usados para validar a importação e os gráficos sem conexão com o equipamento.

### Observações Técnicas

- O código usa `matplotlib` com backend `Qt4Agg`.
- O arquivo `interface.py` é gerado automaticamente; alterações visuais devem ser feitas em `InterfaceImpedSpec.ui` e regeneradas com `pyuic4`.
- O comando de regeneração é:

```bash
pyuic4 InterfaceImpedSpec.ui -o interface.py
```

- Publicações que usem resultados obtidos com este software devem citar o software e os trabalhos associados ao ImpedSpec.
- Revise a compatibilidade de drivers VISA antes de conectar o equipamento em um novo computador.

### Licença

Distribuído sob **GNU General Public License v3.0 ou posterior**. Veja [`LICENSE`](./LICENSE).

---

## 🇺🇸 English

### Overview

**ImpedanceAnalyze4294A** is a desktop GUI based on the ImpedSpec project for controlling the Keysight/Agilent 4294A impedance analyzer, acquiring impedance spectra, and visualizing electrical properties of dielectric materials and circuits.

The application can detect/connect the instrument through VISA, run open/short calibration, configure frequency sweeps, acquire impedance/phase data, and compute derived quantities such as resistance, capacitance, real permittivity and imaginary permittivity.

### Features

- PyQt4 graphical interface.
- Instrument detection through VISA/PyVISA.
- `pyvisa-sim` support.
- Connection to the Keysight/Agilent 4294A impedance analyzer.
- **Open** and **short** calibration before acquisition.
- Start/stop frequency, point count, voltage, bandwidth and averaging configuration.
- Linear or logarithmic sweep.
- Impedance (`Z`) and phase (`Theta`) acquisition.
- Calculation of `Zr`, `Zi`, `R`, `C`, `epsilon'` and `epsilon''`.
- Import of `.txt` files generated by the software.
- Plot views for permittivity, `R/C`, `Z/Theta` and the `Zr/Zi` plane.
- Export of measured data to text files.

### Structure

| File | Description |
|---|---|
| `script.py` | Main application script and acquisition/analysis routines |
| `interface.py` | Python UI generated from the `.ui` file with `pyuic4` |
| `InterfaceImpedSpec.ui` | Qt layout editable in Qt Designer |
| `requirements.txt` | Python dependencies installable with `pip` |
| `run_windows.bat` | Virtual environment setup, dependency installation and Windows launcher |
| `run_linux_mac.sh` | Virtual environment setup, dependency installation and Linux/macOS launcher |
| `sample1.txt` | Sample file for import |
| `sample2.txt` | Sample file for import |
| `sample3.txt` | Sample file for import |
| `LICENSE` | GPL-3.0 license |

### Dependencies

This is a legacy project and depends on the Python 2/PyQt4 ecosystem:

```text
numpy
matplotlib
astropy
docutils
pyvisa
pyvisa-sim
PyQt4
```

The 4294A drivers must also be installed and correctly recognized by the operating system.

### Installation

In PyQt4-compatible environments:

```bash
pip install -r requirements.txt
```

On Fedora, the original environment used:

```bash
sudo dnf install pyqt4-devel
sudo dnf install python-matplotlib-qt
```

On current systems, PyQt4 may not be available from default repositories. Use a compatible legacy environment or consider porting the UI to PyQt5/PySide before production use.

### Running

```bash
python script.py
```

On Windows, you can also create the virtual environment, install dependencies and run with:

```bat
run_windows.bat
```

On Linux/macOS:

```bash
./run_linux_mac.sh
```

To test without physical hardware, enable the simulation mode in the interface when `pyvisa-sim` is configured.

### Basic Use

1. Start the application with `python script.py`.
2. Detect available VISA instruments.
3. Select and connect the 4294A analyzer.
4. Run **open** and **short** calibration, or skip calibration when appropriate for testing.
5. Configure sample data, frequency range, point count and acquisition parameters.
6. Run the analysis.
7. Inspect plots and save measured data.

### Data Format

Exported/imported files store numeric columns for frequency, impedance, phase and derived quantities. The `sample*.txt` files can be used to validate import and plotting without connecting the instrument.

### Technical Notes

- The code uses `matplotlib` with the `Qt4Agg` backend.
- `interface.py` is generated automatically; visual changes should be made in `InterfaceImpedSpec.ui` and regenerated with `pyuic4`.
- Regeneration command:

```bash
pyuic4 InterfaceImpedSpec.ui -o interface.py
```

- Publications using results obtained with this software should cite the software and the related ImpedSpec papers.
- Check VISA driver compatibility before connecting the instrument on a new computer.

### License

Distributed under the **GNU General Public License v3.0 or later**. See [`LICENSE`](./LICENSE).
