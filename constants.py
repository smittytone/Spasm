#!/usr/bin/env python3

##########################################################################
# Application-specific constants                                         #
##########################################################################

VERSION = "1.3.0"

ERRORS = {"0": "No error",
          "1": "Bad mnemonic/opcode",
          "2": "Duplicate label",
          "3": "Undefined label",
          "4": "Bad branch op",
          "5": "Bad operand",
          "6": "Decode error",
          "7": "Bad TFR/EXG operand",
          "8": "Bad PUL/PSH operand",
          "9": "Bad address",
          "10": "8-bit operand expected"} # ADDED 1.2.0

ADDR_MODE_NONE              = 0 # pylint: disable=C0326;
ADDR_MODE_IMMEDIATE         = 1 # pylint: disable=C0326;
ADDR_MODE_DIRECT            = 2 # pylint: disable=C0326;
ADDR_MODE_INDEXED           = 3 # pylint: disable=C0326;
ADDR_MODE_EXTENDED          = 4 # pylint: disable=C0326;
ADDR_MODE_INHERENT          = 5 # pylint: disable=C0326;
ADDR_MODE_IMMEDIATE_SPECIAL = 11 # pylint: disable=C0326;
BRANCH_MODE_SHORT           = 1 # pylint: disable=C0326;
BRANCH_MODE_LONG            = 2 # pylint: disable=C0326;
ADDRESSING_NONE             = 999999

PSEUDO_OP_EQU               = 0 # pylint: disable=C0326;
PSEUDO_OP_RMB               = 1 # pylint: disable=C0326;
PSEUDO_OP_FCB               = 2 # pylint: disable=C0326;
PSEUDO_OP_FDB               = 3 # pylint: disable=C0326;
PSEUDO_OP_END               = 4 # pylint: disable=C0326;
PSEUDO_OP_ORG               = 5 # pylint: disable=C0326;
PSEUDO_OP_SETDP             = 6 # pylint: disable=C0326;
PSEUDO_OP_FCC               = 7 # pylint: disable=C0326;
PSEUDO_OP_ZMB               = 8 # pylint: disable=C0326;

##########################################################################
# The main 6809 instruction set in the form: mnemonic plus               #
# addressing-specific byte vales, where -1 equals 'not supported'.       #
# The addressing sequence is:                                            #
# immediate, direct, indexed, extended, inherent                         #
##########################################################################

ISA = (
    "ABX", -1, -1, -1, -1, 0x3A,
    "ADCA", 0x89, 0x99, 0xA9, 0xB9, -1,
    "ADCB", 0xC9, 0xD9, 0xE9, 0xF9, -1,
    "ADDA", 0x8B, 0x9B, 0xAB, 0xBB, -1,
    "ADDB", 0xCB, 0xDB, 0xEB, 0xFB, -1,
    "ADDD", 0xC3, 0xD3, 0xE3, 0xF3, -1,
    "ANDA", 0x84, 0x94, 0xA4, 0xB4, -1,
    "ANDB", 0xC4, 0xD4, 0xE4, 0xF4, -1,
    "ANDCC", 0x1C, -1, -1, -1, -1,
    "ASL", -1, 0x08, 0x68, 0x78, -1,
    "ASLA", -1, -1, -1, -1, 0x48,
    "ASLB", -1, -1, -1, -1, 0x58,
    "ASR", -1, 0x07, 0x67, 0x77, -1,
    "ASRA", -1, -1, -1, -1, 0x47,
    "ASRB", -1, -1, -1, -1, 0x57,
    "BITA", 0x85, 0x95, 0xA5, 0xB5, -1,
    "BITB", 0xC5, 0xD5, 0xE5, 0xF5, -1,
    "CLR", -1, 0x0F, 0x6F, 0x7F, -1,
    "CLRA", -1, -1, -1, -1, 0x4F,
    "CLRB", -1, -1, -1, -1, 0x5F,
    "CMPA", 0x81, 0x91, 0xA1, 0xB1, -1,
    "CMPB", 0xC1, 0xD1, 0xE1, 0xF1, -1,
    "CMPD", 0x1083, 0x1093, 0x10A3, 0x10B3, -1,
    "CMPS", 0x118C, 0x119C, 0x11AC, 0x11BC, -1,
    "CMPU", 0x1183, 0x1193, 0x11A3, 0x11B3, -1,
    "CMPX", 0x8C, 0x9C, 0xAC, 0xBC, -1,
    "CMPY", 0x108C, 0x109C, 0x10AC, 0x10BC, -1,
    "COM", -1, 0x03, 0x63, 0x73, -1,
    "COMA", -1, -1, -1, -1, 0x43,
    "COMB", -1, -1, -1, -1, 0x53,
    "CWAIT", 0x3C, -1, -1, -1, -1,
    "DAA", -1, -1, -1, -1, 0x19,
    "DEC", -1, 0x0A, 0x6A, 0x7A, -1,
    "DECA", -1, -1, -1, -1, 0x4A,
    "DECB", -1, -1, -1, -1, 0x5A,
    "EORA", 0x88, 0x98, 0xA8, 0xB8, -1,
    "EORB", 0xC8, 0xD8, 0xE8, 0xF8, -1,
    "EXG", 0x1E, -1, -1, -1, -1,
    "INC", -1, 0x0C, 0x6C, 0x7C, -1,
    "INCA", -1, -1, -1, -1, 0x4C,
    "INCB", -1, -1, -1, -1, 0x5C,
    "JMP", -1, 0x0E, 0x6E, 0x7E, -1,
    "JSR", -1, 0x9D, 0xAD, 0xBD, -1,
    "LDA", 0x86, 0x96, 0xA6, 0xB6, -1,
    "LDB", 0xC6, 0xD6, 0xE6, 0xF6, -1,
    "LDD", 0xCC, 0xDC, 0xEC, 0xFC, -1,
    "LDS", 0x10CE, 0x10DE, 0x10EE, 0x10FE, -1,
    "LDU", 0xCE, 0xDE, 0xEE, 0xFE, -1,
    "LDX", 0x8E, 0x9E, 0xAE, 0xBE, -1,
    "LDY", 0x108E, 0x109E, 0x10AE, 0x10BE, -1,
    "LEAS", -1, -1, 0x32, -1, -1,
    "LEAU", -1, -1, 0x33, -1, -1,
    "LEAX", -1, -1, 0x30, -1, -1,
    "LEAY", -1, -1, 0x31, -1, -1,
    "LSL", -1, 0x08, 0x68, 0x78, -1,
    "LSLA", -1, -1, -1, -1, 0x48,
    "LSLB", -1, -1, -1, -1, 0x58,
    "LSR", -1, 0x04, 0x64, 0x74, -1,
    "LSRA", -1, -1, -1, -1, 0x44,
    "LSRB", -1, -1, -1, -1, 0x54,
    "MUL", -1, -1, -1, -1, 0x3D,
    "NEG", -1, 0x00, 0x60, 0x70, -1,
    "NEGA", -1, -1, -1, -1, 0x40,
    "NEGB", -1, -1, -1, -1, 0x50,
    "NOP", -1, -1, -1, -1, 0x12,
    "ORA", 0x8A, 0x9A, 0xAA, 0xBA, -1,
    "ORB", 0xCA, 0xDA, 0xEA, 0xFA, -1,
    "ORCC", 0x1A, -1, -1, -1, -1,
    "PSHS", 0x34, -1, -1, -1, -1,
    "PSHU", 0x36, -1, -1, -1, -1,
    "PULS", 0x35, -1, -1, -1, -1,
    "PULU", 0x37, -1, -1, -1, -1,
    "ROL", -1, 0x09, 0x69, 0x79, -1,
    "ROLA", -1, -1, -1, -1, 0x49,
    "ROLB", -1, -1, -1, -1, 0x59,
    "ROR", -1, 0x06, 0x66, 0x76, -1,
    "RORA", -1, -1, -1, -1, 0x46,
    "RORB", -1, -1, -1, -1, 0x56,
    "RTI", -1, -1, -1, -1, 0x3B,
    "RTS", -1, -1, -1, -1, 0x39,
    "SBCA", 0x82, 0x92, 0xA2, 0xB2, -1,
    "SBCB", 0xC2, 0xD2, 0xE2, 0xF2, -1,
    "SEX", -1, -1, -1, -1, 0x1D,
    "STA", -1, 0x97, 0xA7, 0xB7, -1,
    "STB", -1, 0xD7, 0xE7, 0xF7, -1,
    "STD", -1, 0xDD, 0xED, 0xFD, -1,
    "STS", -1, 0x10DF, 0x10EF, 0x10FF, -1,
    "STU", -1, 0xDF, 0xEF, 0xFF, -1,
    "STX", -1, 0x9F, 0xAF, 0xBF, -1,
    "STY", -1, 0x109F, 0x10AF, 0x10BF, -1,
    "SUBA", 0x80, 0x90, 0xA0, 0xB0, -1,
    "SUBB", 0xC0, 0xD0, 0xE0, 0xF0, -1,
    "SUBD", 0x83, 0x93, 0xA3, 0xB3, -1,
    "SYNC", -1, -1, -1, -1, 0x13,
    "SWI", -1, -1, -1, -1, 0x3F,
    "SWI2", -1, -1, -1, -1, 0x103F,
    "SWI3", -1, -1, -1, -1, 0x113F,
    "TFR", 0x1F, -1, -1, -1, -1,
    "TST", -1, 0x0D, 0x6D, 0x7D, -1,
    "TSTA", -1, -1, -1, -1, 0x4D,
    "TSTB", -1, -1, -1, -1, 0x5D
)

##########################################################################
# The 6809 branch instruction set in the form: mnemonic plus             #
# addressing-specific byte vales. The addressing sequence is:            #
# short, long                                                            #
##########################################################################

BSA = (
    "BRA", 0x20, 0x16,
    "BHI", 0x22, 0x1022,
    "BLS", 0x23, 0x1023,
    "BCC", 0x24, 0x1024,
    "BHS", 0x24, 0x1024,
    "BLO", 0x25, 0x1025,
    "BCS", 0x25, 0x1025,
    "BNE", 0x26, 0x1026,
    "BEQ", 0x27, 0x1027,
    "BVC", 0x28, 0x1028,
    "BVS", 0x29, 0x1029,
    "BPL", 0x2A, 0x102A,
    "BMI", 0x2B, 0x102B,
    "BGE", 0x2C, 0x102C,
    "BLT", 0x2D, 0x102D,
    "BGT", 0x2E, 0x102E,
    "BLE", 0x2F, 0x102F,
    "BSR", 0x8D, 0x17
)

POPS = ("EQU", "RMB", "FCB", "FDB", "END", "ORG", "SETDP", "FCC", "ZMB")
