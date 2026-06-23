# ImpedanceAnalyze4294A

Interface gráfica em Python/PyQt5 para aquisição, importação e análise de espectros de impedância com o analisador Keysight/Agilent 4294A.

---

## 🇧🇷 PT-BR

### Visão Geral

O **ImpedanceAnalyze4294A** é uma interface desktop baseada no projeto ImpedSpec para controle do analisador de impedância Keysight/Agilent 4294A, aquisição de espectros e visualização de propriedades elétricas de materiais dielétricos e circuitos.

A aplicação permite detectar/conectar o instrumento via VISA, executar calibração aberta/curta, configurar varreduras de frequência, coletar impedância/fase e calcular grandezas derivadas como resistência, capacitância, permissividade real e permissividade imaginária.

### Funcionalidades

- Interface gráfica em PyQt5.
- Ajustes de layout em runtime para evitar rótulos cortados, campos comprimidos e grupos sobrepostos em ambientes PyQt5/Windows.
- Tabela de resultados com área ampliada, linhas alternadas, cabeçalhos compactos e colunas proporcionais.
- Gráficos com margens ajustadas para manter rótulos de eixos visíveis.
- Controles de varredura `Log`/`Linear` alinhados de forma consistente nas três abas.
- Controles de varredura `Log`/`Linear` deslocados para a direita e alinhados abaixo da coluna de valores numéricos.
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
| `interface.py` | Interface Python gerada originalmente a partir do arquivo `.ui` e adaptada para PyQt5 |
| `InterfaceImpedSpec.ui` | Layout Qt editável no Qt Designer |
| `requirements.txt` | Dependências Python instaláveis por `pip` |
| `run_windows.bat` | Criação de ambiente virtual, instalação de dependências e execução no Windows |
| `run_linux_mac.sh` | Criação de ambiente virtual, instalação de dependências e execução no Linux/macOS |
| `samples/sample1.txt` | Arquivo de exemplo para importação |
| `samples/sample2.txt` | Arquivo de exemplo para importação |
| `samples/sample3.txt` | Arquivo de exemplo para importação |
| `LICENSE` | Licença GPL-3.0 |

### Dependências

Este projeto foi modernizado para execução com Python 3/PyQt5:

```text
numpy
matplotlib
pyvisa
pyvisa-sim
PyQt5
```

Também é necessário ter os drivers do analisador 4294A instalados e corretamente reconhecidos pelo sistema operacional.

#### Driver VISA

`pyvisa` é apenas a biblioteca Python usada pela aplicação. Para conectar a um instrumento físico, o computador também precisa de um backend/driver VISA instalado no sistema, como **NI-VISA** ou **Keysight IO Libraries Suite**.

Esse driver permite que o sistema operacional detecte e exponha instrumentos GPIB, USB ou LAN para a aplicação. Ele não pode ser instalado pelo `requirements.txt`, porque não é um pacote Python comum; deve ser instalado pelo instalador do fabricante.

O `pyvisa-sim` serve apenas para testes sem instrumento real. Nesse modo simulado, você não precisa de NI-VISA ou Keysight IO Libraries, mas também não haverá comunicação com o 4294A físico.

Recomendação prática:

- Se estiver usando uma interface/adaptador Keysight/Agilent, instale a versão mais recente do **Keysight IO Libraries Suite** compatível com seu Windows.
- Se estiver usando uma interface/adaptador National Instruments, instale a versão mais recente do **NI-VISA** compatível com seu Windows.
- Evite instalar dois backends VISA ao mesmo tempo sem necessidade. Quando isso for inevitável, confirme no utilitário do fabricante qual backend está ativo para GPIB/USB/LAN.

### Instalação

Em ambientes Python 3:

```bash
pip install -r requirements.txt
```

No Fedora, instale os pacotes Qt/VISA necessários ao sistema conforme seu ambiente:

```bash
sudo dnf install python3-qt5
```

Também é necessário ter os drivers VISA do instrumento instalados para conexão com hardware real.

### Execução

```bash
python script.py
```

No Windows, também é possível criar o ambiente virtual, instalar dependências e executar com:

```bat
run_windows.bat
```

Para uma máquina sem internet, baixe as dependências em uma máquina conectada:

```bat
python -m pip download -r requirements.txt -d offline\wheels
```

Copie o repositório inteiro, incluindo a pasta `offline\wheels`, para a máquina do equipamento e execute:

```bat
install_offline_windows.bat
```

As wheels precisam ser compatíveis com a versão e arquitetura do Python instalado na máquina offline. Use Python 64-bit e, se possível, a mesma versão usada para criar a pasta `offline\wheels`. O guia resumido fica em `offline/README_OFFLINE.md`.

No Linux/macOS:

```bash
./run_linux_mac.sh
```

Para testar sem instrumento físico, habilite o modo de simulação na interface quando o ambiente `pyvisa-sim` estiver configurado.

### Diagnóstico de conexão VISA

Antes de usar a interface com o equipamento real, teste se o Windows está expondo o instrumento para o PyVISA:

```bash
python scripts/visa_diagnostic.py
```

Se aparecer `Could not locate a VISA implementation`, falta instalar um backend VISA do sistema, como Keysight IO Libraries Suite ou NI-VISA. Depois de instalar o driver e conectar o adaptador/instrumento, rode o comando de novo. O recurso esperado para GPIB normalmente terá o formato:

```text
GPIB0::17::INSTR
```

Para testar um endereço específico:

```bash
python scripts/visa_diagnostic.py GPIB0::17::INSTR
```

O teste só está correto quando a resposta de `*IDN?` identifica o analisador Keysight/Agilent 4294A.

#### Conexão Ethernet em `10.1.1.2`

Se o equipamento ou ponte Ethernet/GPIB usa IP fixo `10.1.1.2`, o computador também precisa estar na mesma rede. Configure a placa Ethernet do Windows com um IP livre, por exemplo:

```text
IP:      10.1.1.1
Máscara: 255.255.255.0
Gateway: em branco
DNS:     em branco
```

Depois teste os formatos TCPIP mais comuns:

```bash
python scripts/visa_diagnostic.py --py TCPIP0::10.1.1.2::inst0::INSTR
python scripts/visa_diagnostic.py --py TCPIP0::10.1.1.2::5025::SOCKET
python scripts/visa_diagnostic.py --py TCPIP0::10.1.1.2::gpib0,17::INSTR
```

Se o endereço GPIB do instrumento não for `17`, troque o número no último comando. Na interface, esses endereços aparecem como sugestões e também podem ser digitados manualmente no campo de equipamento.

No momento, `10.1.1.2` é o IP padrão sugerido pela aplicação para a conexão Ethernet. O campo de equipamento é editável, então outro endereço VISA pode ser digitado manualmente quando necessário. Uma melhoria planejada é adicionar um campo dedicado para informar apenas o IP e gerar automaticamente os endereços TCPIP correspondentes.

### Auditoria rápida

Depois de alterações no código, rode:

```bash
python -m py_compile script.py interface.py scripts/smoke_test.py scripts/visa_diagnostic.py
python scripts/smoke_test.py
```

O smoke test abre a interface em modo offscreen, verifica espaçamentos básicos, aciona `File > Import Data`, importa `samples/sample1.txt`, valida `pyvisa-sim` e executa uma aquisição simulada com instrumento falso.

### Uso Básico

1. Abra a aplicação com `python script.py`.
2. Detecte os instrumentos VISA disponíveis.
3. Selecione e conecte o analisador 4294A.
4. Execute a calibração **open** e **short** ou pule a calibração quando apropriado para teste.
5. Configure a amostra, faixa de frequência, número de pontos e parâmetros de aquisição.
6. Execute a análise.
7. Visualize os gráficos e salve os dados medidos.

### Formato dos Dados

Os arquivos exportados/importados armazenam colunas numéricas de frequência, impedância, fase e grandezas derivadas. Os arquivos `samples/sample*.txt` podem ser usados para validar a importação e os gráficos sem conexão com o equipamento.

### Observações Técnicas

- O código usa `matplotlib` com backend `Qt5Agg`.
- O arquivo `interface.py` veio de uma geração PyQt4 e contém shims de compatibilidade PyQt5. Alterações visuais devem ser feitas em `InterfaceImpedSpec.ui` e regeneradas/portadas para PyQt5.
- `script.py` aplica ajustes visuais após `setupUi()` para ampliar a coluna de parâmetros, encurtar rótulos longos, aumentar o tamanho mínimo da janela e separar os grupos das três abas.
- O comando de regeneração é:

```bash
pyuic5 InterfaceImpedSpec.ui -o interface.py
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

- PyQt5 graphical interface.
- Runtime layout adjustments to prevent clipped labels, squeezed fields, and overlapping groups in PyQt5/Windows environments.
- Results table with expanded viewing area, alternating rows, compact headers, and proportional columns.
- Plots with adjusted margins to keep axis labels visible.
- `Log`/`Linear` sweep controls aligned consistently across the three tabs.
- `Log`/`Linear` sweep controls shifted to the right and aligned below the numeric value column.
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
| `interface.py` | Python UI originally generated from the `.ui` file and adapted for PyQt5 |
| `InterfaceImpedSpec.ui` | Qt layout editable in Qt Designer |
| `requirements.txt` | Python dependencies installable with `pip` |
| `run_windows.bat` | Virtual environment setup, dependency installation and Windows launcher |
| `run_linux_mac.sh` | Virtual environment setup, dependency installation and Linux/macOS launcher |
| `samples/sample1.txt` | Sample file for import |
| `samples/sample2.txt` | Sample file for import |
| `samples/sample3.txt` | Sample file for import |
| `LICENSE` | GPL-3.0 license |

### Dependencies

This project has been modernized to run with Python 3/PyQt5:

```text
numpy
matplotlib
pyvisa
pyvisa-sim
PyQt5
```

The 4294A drivers must also be installed and correctly recognized by the operating system.

#### VISA Driver

`pyvisa` is only the Python library used by the application. To connect to a physical instrument, the computer also needs a system VISA backend/driver, such as **NI-VISA** or **Keysight IO Libraries Suite**.

That driver lets the operating system detect and expose GPIB, USB, or LAN instruments to the application. It cannot be installed through `requirements.txt` because it is not a regular Python package; it must be installed with the vendor installer.

`pyvisa-sim` is only for tests without real hardware. In that simulated mode, you do not need NI-VISA or Keysight IO Libraries, but there is also no communication with the physical 4294A.

Practical recommendation:

- If you are using a Keysight/Agilent interface or adapter, install the latest **Keysight IO Libraries Suite** version compatible with your Windows version.
- If you are using a National Instruments interface or adapter, install the latest **NI-VISA** version compatible with your Windows version.
- Avoid installing two VISA backends at the same time unless needed. If that is unavoidable, confirm in the vendor utility which backend is active for GPIB/USB/LAN.

### Installation

In Python 3 environments:

```bash
pip install -r requirements.txt
```

On Fedora, install the system Qt/VISA packages required by your environment:

```bash
sudo dnf install python3-qt5
```

The 4294A VISA drivers are still required for real hardware connections.

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

### Quick Audit

After code changes, run:

```bash
python -m py_compile script.py interface.py scripts/smoke_test.py
python scripts/smoke_test.py
```

The smoke test opens the interface in offscreen mode, checks basic spacing, triggers `File > Import Data`, imports `samples/sample1.txt`, validates `pyvisa-sim`, and runs a simulated acquisition with a fake instrument.

### Basic Use

1. Start the application with `python script.py`.
2. Detect available VISA instruments.
3. Select and connect the 4294A analyzer.
4. Run **open** and **short** calibration, or skip calibration when appropriate for testing.
5. Configure sample data, frequency range, point count and acquisition parameters.
6. Run the analysis.
7. Inspect plots and save measured data.

### Data Format

Exported/imported files store numeric columns for frequency, impedance, phase and derived quantities. The `samples/sample*.txt` files can be used to validate import and plotting without connecting the instrument.

### Technical Notes

- The code uses `matplotlib` with the `Qt5Agg` backend.
- `interface.py` came from a PyQt4 generation and includes PyQt5 compatibility shims. Visual changes should be made in `InterfaceImpedSpec.ui` and regenerated/ported to PyQt5.
- `script.py` applies visual adjustments after `setupUi()` to widen the parameter column, shorten long labels, increase the minimum window size, and separate groups across the three tabs.
- Regeneration command:

```bash
pyuic5 InterfaceImpedSpec.ui -o interface.py
```

- Publications using results obtained with this software should cite the software and the related ImpedSpec papers.
- Check VISA driver compatibility before connecting the instrument on a new computer.

### License

Distributed under the **GNU General Public License v3.0 or later**. See [`LICENSE`](./LICENSE).
