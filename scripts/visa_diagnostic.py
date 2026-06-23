import argparse
import traceback

import pyvisa

DEFAULT_PORTS = [5025, 5024, 10001, 10000]


def build_resource_manager(simulation, py_backend):
    if simulation:
        return pyvisa.ResourceManager("@sim")
    if py_backend:
        return pyvisa.ResourceManager("@py")
    return pyvisa.ResourceManager()


def tcpip_addresses(ip_address, gpib_address):
    return [
        f"TCPIP0::{ip_address}::inst0::INSTR",
        *[
            f"TCPIP0::{ip_address}::{port}::SOCKET"
            for port in DEFAULT_PORTS
        ],
        f"TCPIP0::{ip_address}::gpib0,{gpib_address}::INSTR",
    ]


def query_address(rm, address, timeout):
    print(f"Opening: {address}")
    instrument = rm.open_resource(address)
    instrument.timeout = timeout
    if address.upper().endswith("::SOCKET"):
        instrument.write_termination = "\n"
        instrument.read_termination = "\n"
    print("Sending: *IDN?")
    print(f"Response: {instrument.query('*IDN?').strip()}")
    instrument.close()


def main():
    parser = argparse.ArgumentParser(
        description="List VISA resources and optionally query one instrument."
    )
    parser.add_argument(
        "address",
        nargs="?",
        help="VISA address to test, for example GPIB0::17::INSTR",
    )
    parser.add_argument(
        "--sim",
        action="store_true",
        help="Use pyvisa-sim instead of a real VISA backend.",
    )
    parser.add_argument(
        "--py",
        action="store_true",
        help="Use pyvisa-py instead of the system VISA backend.",
    )
    parser.add_argument(
        "--ip",
        default=None,
        help="Try common TCPIP VISA addresses for this IP address.",
    )
    parser.add_argument(
        "--gpib",
        default="17",
        help="GPIB address used when building a LAN/GPIB gateway address.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5000,
        help="Instrument timeout in milliseconds.",
    )
    args = parser.parse_args()

    print(f"PyVISA: {pyvisa.__version__}")
    if args.sim:
        backend_name = "pyvisa-sim"
    elif args.py:
        backend_name = "pyvisa-py"
    else:
        backend_name = "system VISA"
    print(f"Backend: {backend_name}")

    try:
        rm = build_resource_manager(args.sim, args.py)
        print(f"Resource manager: {rm}")
        resources = () if (args.address or args.ip) else rm.list_resources()
    except Exception:
        print("Could not open the VISA resource manager.")
        print(traceback.format_exc())
        print(
            "For real hardware, install a system VISA backend such as "
            "Keysight IO Libraries Suite or NI-VISA."
        )
        return 1

    if resources:
        print("Detected resources:")
        for resource in resources:
            print(f"  {resource}")
    else:
        print("No VISA resources detected.")

    if not args.address:
        if args.ip:
            failed = False
            for address in tcpip_addresses(args.ip, args.gpib):
                try:
                    query_address(rm, address, args.timeout)
                    return 0
                except Exception:
                    failed = True
                    print("Failed.")
                    print(traceback.format_exc())
            return 2 if failed else 0
        return 0

    try:
        query_address(rm, args.address, args.timeout)
    except Exception:
        print("Could not query the selected instrument.")
        print(traceback.format_exc())
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
