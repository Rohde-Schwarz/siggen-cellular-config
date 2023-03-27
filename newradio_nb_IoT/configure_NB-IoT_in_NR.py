''' 38.141-1 4.9.3 - NB-IoT in 5G This script sets up a NR-FR1-TM1_1__FDD_10MHz_15kHz testmodel, applies puncturing and adds a NB-IoT carrier '''
import pyvisa
import math
from argparse import ArgumentParser

def configure_nr_n_tm(inst, nb_iot_re, iot_boost):
    # setup NR-FR1-TM1_1__FDD_10MHz_15kHz + Puncturing
    inst.query(':SOURce1:BB:NR5G:SETTing:TMODel:DL "NR-FR1-TM1_1__FDD_10MHz_15kHz";*OPC?')
    inst.query(':SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:NALLoc 1;*OPC?')
    inst.query(':SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:ALLoc0:SCSPacing SCS15;*OPC?')
    inst.query(':SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:ALLoc0:SYMNumber 14;*OPC?')
    inst.query(f':SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:ALLoc0:RBOFfset {nb_iot_re};*OPC?')
    inst.query(':SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:ALLoc0:RBNumber 1;*OPC?')
    inst.query(':SOURce1:BB:NR5G:STATe 1;*OPC?')

    # setup NB-iot
    inst.query(':SOURce2:BB:EUTRa:SETTing:TMOD:DL "N-TM_Standalone";*OPC?')
    inst.query(':SOURce2:BB:EUTRa:STATe 1;*OPC?')

    # add NB-iot and NR signal
    inst.query(':SCONfiguration:OUTPut:MAPPing:RF1:MODE Add;*OPC?')
    inst.query(':SCONfiguration:OUTPut:MAPPing:RF1:STReam2:STATe 1;*OPC?')

    # frequency shift nb-iot
    half_rb = 6 * 15e3
    target_lower_end = float(inst.query(':SOURce1:BB:NR5G:NODE:CELL0:TXBW:POINta?')) + nb_iot_re * 12 * 15e3
    nb_freq_shift = target_lower_end + half_rb
    inst.query(f':SOURce2:BB:FOFFset {nb_freq_shift};*OPC?')

    # power leveling
    total_rbs = float(inst.query(':SOURce1:BB:NR5G:NODE:CELL0:TXBW:S15K:NRB?'))
    power_nr = 10 * math.log10(1 - (10**(iot_boost / 10))/total_rbs)
    inst.query(f':SOURce1:BB:PGAin {power_nr:.6f};*OPC?')

    power_iot = 10 * math.log10(1/total_rbs) + iot_boost
    inst.query(f':SOURce2:BB:PGAin {power_iot:.6f};*OPC?')
    inst.query(':OUTPut1:STATe 1;*OPC?')


def main():
    parser = ArgumentParser()
    parser.add_argument('resource_name', help='Visa instrument address e.g. >TCPIP::192.186.1.14::hislip0::instr<')
    parser.add_argument('-r', '--nb_iot_re', help='Number of NB-IoT resource blocks.', default=4, type=int)
    parser.add_argument('-b', '--iot_boost', help='NB-IoT boost', default=6, type=int)
    args = parser.parse_args()

    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(args.resource_name)
    inst.timeout = 20000
    configure_nr_n_tm(inst, nb_iot_re=args.nb_iot_re, iot_boost=args.iot_boost)

if __name__ == "__main__":
    main()


