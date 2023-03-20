''' 
This script configures PRACH allocations according to 38.211 Table 6.3.3.2-2/3.
'''
import pyvisa
from argparse import ArgumentParser
from tables import data_table_6_3_3_2_2, data_table_6_3_3_2_3


def configure_prach_index(smx, table, index, type):
    selected_prach_index_configuration = table[index]
    if len(selected_prach_index_configuration[0]) > 1:
        if type in selected_prach_index_configuration[0]:
            selected_prach_index_configuration[0] = [type]

    prach_format = selected_prach_index_configuration[0][0]
    required_rf_frames = selected_prach_index_configuration[1]
    prach_rf_within_frames = selected_prach_index_configuration[2]
    prach_subframes = [prach_rf_within_frames*10 + subframe for subframe in selected_prach_index_configuration[3]]
    starting_symbol_within_subframe = selected_prach_index_configuration[4]
    number_of_prach_slots = selected_prach_index_configuration[5] if selected_prach_index_configuration[5] != '-' else 1
    number_of_prach_repetitions = selected_prach_index_configuration[6] if selected_prach_index_configuration[6] != '-' else 1
    prach_duration = selected_prach_index_configuration[7] if selected_prach_index_configuration[7] != 0 else 1

    smx.write(f":SOURce1:BB:NR5G:OUTPut:SEQLen {required_rf_frames}")

    for subframe in prach_subframes:
        smx.write(f":SOURce1:BB:NR5G:SCHed:CELL0:SUBF{subframe}:USER0:BWPart0:NALLoc {number_of_prach_slots*number_of_prach_repetitions}")
        for slot in range(0, number_of_prach_slots):
            for repetition in range(0, number_of_prach_repetitions):
                smx.write(f":SOURce1:BB:NR5G:SCHed:CELL0:SUBF{subframe}:USER0:BWPart0:ALLoc{slot*number_of_prach_repetitions + repetition}:CONTent PRAC")
                smx.write(f":SOURce1:BB:NR5G:SCHed:CELL0:SUBF{subframe}:USER0:BWPart0:ALLoc{slot*number_of_prach_repetitions + repetition}:REPetitions OFF")
                if prach_format == '3':
                    smx.write(f":SOURce1:BB:NR5G:SCHed:CELL0:SUBF{subframe}:USER0:BWPart0:ALLoc{slot*number_of_prach_repetitions + repetition}:PRACh:SCSPacing N5")
                if prach_format in ['0', '1', '2']:
                    smx.write(f":SOURce1:BB:NR5G:SCHed:CELL0:SUBF{subframe}:USER0:BWPart0:ALLoc{slot*number_of_prach_repetitions + repetition}:PRACh:SCSPacing N1_25")
                smx.write(f":SOURce1:BB:NR5G:SCHed:CELL0:SUBF{subframe}:USER0:BWPart0:ALLoc{slot*number_of_prach_repetitions + repetition}:PRACh:FORMat F{prach_format}")
                smx.write(f":SOURce1:BB:NR5G:SCHed:CELL0:SUBF{subframe}:USER0:BWPart0:ALLoc{slot*number_of_prach_repetitions + repetition}:SLOT {slot}")
                smx.write(f":SOURce1:BB:NR5G:SCHed:CELL0:SUBF{subframe}:USER0:BWPart0:ALLoc{slot*number_of_prach_repetitions + repetition}:SYMoffset {starting_symbol_within_subframe + repetition*prach_duration}")


def main():
    parser = ArgumentParser()
    parser.add_argument('resource_name', help='Visa instrument address e.g. >TCPIP::192.186.1.14::hislip0::instr<')
    parser.add_argument('-i', '--prach_configuration_index', help='Prach configuration to be configured', type=int)
    parser.add_argument('-t', '--prach_table', help='Select PRACH table. 2 => 6.3.3.2-2, 2 => 6.3.3.2-3', default=2, type=int, choices=[2, 3])
    parser.add_argument('-f', '--preamble_format', help='Select preamble format. Only used, if not given by table.', default=None, choices=['A1', 'B1', 'A2', 'B2', 'A3', 'B3'])
    args = parser.parse_args()

    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(args.resource_name)
    inst.timeout = 1000
    inst.write(":SOURce1:BB:NR5G:LINK UP")
    inst.write(":SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:NALLoc 0")

    if (args.prach_table == 2):
        configure_prach_index(inst, data_table_6_3_3_2_2, args.prach_configuration_index, args.preamble_format)
    else:
        configure_prach_index(inst, data_table_6_3_3_2_3, args.prach_configuration_index, args.preamble_format)

if __name__ == "__main__":
    main()
