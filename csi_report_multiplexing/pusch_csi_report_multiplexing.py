''' 
This script multiplexes CSI part 1 reports into a UCI bit sequence according to 6.3.2.1.2-6 and sends it to a SMX.
'''
import pyvisa
from argparse import ArgumentParser

def setup_uci_transmission(inst):
    inst.write(":SOURce1:BB:NR5G:LINK UP")
    inst.write(":SOURce1:BB:NR5G:SIMPle 1")
    inst.write(":SOURce1:BB:NR5G:UBWP:USER0:USCH:CCODing:STATe 1")

def concatenate_csi_reports(reports):
    return "".join(reversed(reports))

def send_csi_reports(inst, uci):
    smx_encoded_value = f'#H{int(uci, 2):X},{len(uci)}'
    inst.write(f":SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:PUSCh:UCI:CSI1:BITS {len(uci)}")
    inst.write(f":SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:PUSCh:UCI:CSI1:PATTern {smx_encoded_value}")

def main():
    parser = ArgumentParser()
    parser.add_argument('resource_name', help='Visa instrument address e.g. >TCPIP::192.186.1.14::hislip0::instr<')
    args = parser.parse_args()

    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(args.resource_name)
    setup_uci_transmission(inst)

    # CSI reports #1, #2, #3, ...
    reports = ['1010101110100', '1010101110101', '1010101110111']
    send_csi_reports(inst, concatenate_csi_reports(reports))

if __name__ == "__main__":
    main()