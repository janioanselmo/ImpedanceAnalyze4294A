# Instalação offline

Use esta pasta para levar o software para a máquina conectada ao equipamento.

## Conteúdo

- `wheels/`: pacotes Python baixados previamente para instalação sem internet.
- `../install_offline_windows.bat`: cria o ambiente virtual, instala os pacotes locais e abre o programa.
- `../scripts/visa_diagnostic.py`: testa a conexão TCPIP/VISA antes de usar a interface.

## Passos na máquina do equipamento

1. Extraia o pacote offline em uma pasta local.
2. Confirme que o Python instalado é 64-bit e compatível com as wheels.
3. Configure a placa de rede conectada ao equipamento:

```text
IP:      10.1.1.1
Máscara: 255.255.255.0
Gateway: vazio
DNS:     vazio
```

4. Execute, na raiz do projeto:

```bat
install_offline_windows.bat
```

5. Teste a conexão com um destes endereços:

```bat
.\.venv\Scripts\python.exe scripts\visa_diagnostic.py --py TCPIP0::10.1.1.2::inst0::INSTR
.\.venv\Scripts\python.exe scripts\visa_diagnostic.py --py TCPIP0::10.1.1.2::5025::SOCKET
.\.venv\Scripts\python.exe scripts\visa_diagnostic.py --py TCPIP0::10.1.1.2::gpib0,17::INSTR
```

Se o endereço GPIB do equipamento não for `17`, substitua esse número.
