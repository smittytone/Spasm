#!/usr/bin/env python3

##########################################################################
#                                                                        #
# 'SPASM' -- Smittytone's Primary 6809 ASeMmbler -- 1.0.0                #
# Copyright 2019, Tony Smith (@smittytone)                               #
# License: MIT (terms attached to this repo)                             #
#                                                                        #
##########################################################################


##########################################################################
# Program library imports                                                #
##########################################################################

import os
import sys
import json

##########################################################################
# Application-specific constants                                         #
##########################################################################

SPACES  = "                                                         "
NOUGHTS = "000000000000000000000000000000000000"
ERRORS  = { "0": "No error",
            "1": "Bad mnemonic/opcode",
            "2": "Duplicate label",
            "3": "Undefined label",
            "4": "Bad branch op",
            "5": "Bad operand",
            "6": "Decode error",
            "7": "Bad TFR/EXG operand",
            "8": "Bad PUL/PSH operand",
            "9": "Bad address" }
ADDR_MODE_NONE              = 0
ADDR_MODE_IMMEDIATE         = 1
ADDR_MODE_DIRECT            = 2
ADDR_MODE_INDEXED           = 3
ADDR_MODE_EXTENDED          = 4
ADDR_MODE_INHERENT          = 5
ADDR_MODE_IMMEDIATE_SPECIAL = 11
BRANCH_MODE_SHORT           = 1
BRANCH_MODE_LONG            = 2

##########################################################################
# The main 6809 instruction set in the form: mnemonic plus               #
# addressing-specific byte vales, where -1 equals 'not supported'.       #
# The addressing sequence is:                                            #
# immediate, direct, indexed, extended, inherent                         #
##########################################################################

ISA = [
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
]

##########################################################################
# The 6809 branch instruction set in the form: mnemonic plus             #
# addressing-specific byte vales. The addressing sequence is:            #
# short, long                                                            #
##########################################################################

BSA = [
    "BRA", 0x20, 0x16,
    "BHI", 0x22, 0x1022,
    "BLS", 0x23, 0x1023,
    "BHS", 0x24, 0x1024,
    "BCC", 0x24, 0x1024,
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
]

##########################################################################
# Application globals                                                    #
##########################################################################

verbose = True
startAddress = 0x0000
progCount = 0
passCount = 0
showupper = 0
labels = []
code = []
lines = []
outFile = None

##########################################################################
# Application-specific classes                                           #
##########################################################################

class DecodeData:
    '''
    A simple class to hold the temporary data for a line of
    6809 assembly code
    '''
    indirectFlag = False
    indexAddressingFlag = False
    indexedAddress = -1
    opType = 0
    branchOpType = 0
    pseudoOpType = 0
    lineNumber = 0
    commentTab = 0
    op = []
    opndValue = -1


##########################################################################
# Functions                                                              #
##########################################################################

def processFile(path):
    '''
    Assemble a single '.asm' file using a two-pass process to identify
    labels and pseudo-ops, etc.
    '''
    global startAddress
    global passCount
    global progCount
    global verbose
    global code
    global labels
    global lines

    if verbose is True:
        print("****** PROCESSING FILE  ******")
        print(path)

    # Clear the storage arrays
    lines = []
    labels = []
    code = []

    # Check that the passed file is available to process
    if os.path.exists(path):
        with open(path, "r") as file:
            lines = list(file)
    else:
        if verbose is True:
            print("File " + path + " does not exist, skipping")
        return

    # Do the assembly in two passes
    breakFlag = False
    for p in range(1, 3):
        # Start a pass
        progCount = startAddress
        passCount = p
        if verbose is True:
            print("****** ASSEMBLY PASS #" + str(p) + " ******")
        for i in range (0, len(lines)):
            # Parse the lines one at a time
            result = parseLine(lines[i], i)
            if result is False:
                # Error in processing
                print("Processing error in line " + str(i + 1) + " - halting assembly")
                breakFlag = True
                # Break out of the line-by-line loop
                break
        if breakFlag is True:
            # Break out of the pass-by-pass loop
            break

    # Post-assembly, dump the machine code, provided there was no error
    if verbose is True and breakFlag is False:
        print(" ")
        print("Machine code dump")
        progCount = startAddress
        for i in range(0, len(code), 8):
            # Add the initial address
            displayString = "0x{0:04X}".format(progCount) + "  "

            for j in range(0, 8):
                if i + j < len(code):
                    # Add the bytes, one at a time, separated by whitespace
                    displayString = displayString + "  {0:02X}".format(code[i + j])
                    progCount = progCount + 1
            print(displayString)

    # Write out the machine code file
    if outFile is not None and breakFlag is False:
        writeFile(path)


def parseLine(line, lineNumber):
    '''
    Process a single line of assembly, on a per-pass basis.
    Each line is segmented by space characters, and we remove extra spaces from
    all line parts other than comments.
    KNOWN ISSUE: You cannot therefore have a space set using the Ascii indicator, '
    TODO: Some way of handling string constants
    '''
    global labels

    # Split the line at the line terminator
    lineParts = line.splitlines()
    line = lineParts[0]
    
    # Check for comment lines
    comment = ""
    commentTab = line.find(";")
    if commentTab != -1:
        # Found a comment line so re-position it
        lineParts = line.split(";", 1)
        comment = ";" + lineParts[len(lineParts) - 1]
        line = lineParts[0]

    # Segment line by spaces
    lineParts = line.split(' ')

    # Remove empty entries (ie. instances of multiple spaces)
    j = 0
    while True:
        if j == len(lineParts):
            break
        if len(lineParts[j]) == 0:
            lineParts.pop(j)
        else:
            j = j + 1

    # At this point, typical line might be:
    #   lineParts[0] = "@startAddress"
    #   lineParts[1] = "EQU"
    #   lineParts[2] = "$FFFF"
    #   lineParts[3] = ";This is a comment"

    # Begin line decoding
    lineData = DecodeData()
    lineData.lineNumber = lineNumber

    if len(lineParts) == 0:
        # This is a comment-only line, or empty line,
        # so assemble a basic empty list
        if commentTab != -1 and passCount == 2:
            # We have a comment, so just dump it out on pass 2
            lineData.commentTab = commentTab
            writeCode([comment, " ", " ", " "], [], 0, lineData)
            # And return to go and process the next line
            return True
        else:
            lineParts = [" ", " "]

    # Process the line's components
    # Check for an initial label
    label = lineParts[0]
    if label[0] == "@":
        # Found a label - store it if we need to
        a = haveGotLabel(lineParts[0])
        if a != -1:
            # The label has already been seen during assembly
            label = labels[a]
            if passCount == 1:
                if label["addr"] != "UNDEF":
                    errorMessage(2, lineNumber) # Duplicate label
                    return False
                # Set the label address
                label["addr"] = progCount
                # Output the label valuation
                if verbose is True:
                    print("Label " + label["name"] + " set to 0x" + "{0:04X}".format(progCount) + " (line " + str(lineNumber) + ")")
        else:
            # Record the newly found label
            newLabel = { "name": label, "addr": progCount }
            labels.append(newLabel)
            if verbose is True and passCount == 1:
                print("Label " + lineParts[0] + " found on line " + str(lineNumber + 1))
    else:
        # Not a label, so insert a blank - ie. ensure the op will be in lineParts[1]
        lineParts.insert(0, " ")

    # If there is no third field, add an empty one
    if len(lineParts) == 2:
        lineParts.append(" ")

    # Put the comment string, if there is one, into the comment field, lineParts[3]
    # Otherwise drop in an empty field
    if len(comment) > 0:
        lineParts.append(comment)
    else:
        lineParts.append(" ")

    # Check the opcode
    op = []
    if lineParts[1] != " ":
        op = decodeOp(lineParts[1], lineData)
        # NOTE 'op' will contain all the op's possible codes
        if len(op) == 0:
            return False
        lineData.op = op

    # TODO What if there's no op, or are we dealing with dangling lines?

    # Calculate the operand
    opnd = decodeOpnd(lineParts[2], lineData)
    if opnd == -1:
        return False
    
    # Handle a a pseudo-op (assembler directive) if we have one
    result = True
    if lineData.pseudoOpType > 0:
        # We have a pseudo-op
        result = processPseudoOp(lineParts, opnd, lineParts[0], lineData)
    else:
        # We have a regular op
        result = writeCode(lineParts, op, opnd, lineData)
    if result is False:
        errorMessage(6, lineNumber) # Bad decode
        return False
    return result


def decodeOp(op, data):
    '''
    Check that the specified op from the listing is a valid mnemonic.
    Returns a list containing 1 item (pseudo op), 2 items (branch op) or 6 items (op)
    Each list contains the op name then integers for the opcode's
    machine code values for each available addressing mode (or -1 for an unknown op)
    '''

    # Make mnemonic upper case
    op = op.upper()

    # Check for pseudo-ops
    if op == "EQU":
        data.pseudoOpType = 1
        return ["EQU"]
    if op == "RMB":
        data.pseudoOpType = 2
        return ["RMB"]
    if op == "FCB":
        data.pseudoOpType = 3
        return ["FCB"]
    if op == "FDB":
        data.pseudoOpType = 4
        return ["FDB"]
    if op == "END":
        data.pseudoOpType = 5
        return ["END"]
    if op == "ORG":
        # Not yet implemented
        data.pseudoOpType = 6
        return ["ORG"]
    if op == "SETDP":
        # Not yet implemented
        data.pseudoOpType = 7
        return ["SETDP"]

    # Check for regular instructions
    for i in range(0, len(ISA), 6):
        if ISA[i] == op:
            # Return the instruction data
            return [ISA[i], ISA[i + 1], ISA[i + 2], ISA[i + 3], ISA[i + 4], ISA[i + 5]]

    # Check for branch instructions
    if op[0] == "L":
        # Handle long branch instructions
        data.branchOpType = BRANCH_MODE_LONG
        op = op[-3]
    else:
        data.branchOpType = BRANCH_MODE_SHORT

    for i in range (0, len(BSA), 3):
        if BSA[i] == op:
            # Return the branch code data
            return [BSA[i], BSA[i + 1], BSA[i + 2], -1, -1, -1]

    # No instruction found: that's an error - this will be picked up in parseLine()
    errorMessage(1, data.lineNumber) # Bad op
    return []


def decodeOpnd(opnd, data):
    '''
    This function decodes the operand string 'opnd' to an integer, using
    the opcode data supplied as 'op'.
    It returns -1 if the operand value could not be determined
    '''
    global progCount

    opndString = ""
    opndValue = 0
    op = data.op
    opName = ""
    data.opType = ADDR_MODE_NONE

    if len(op) > 1:
        opName = op[0]
    if opName == "EXG" or opName == "TFR":
        # Register swap operation to calculate the special operand value
        # by looking at the named registers separated by a comma
        parts = opnd.split(',')
        if len(parts) != 2 or parts[0] == parts[1]:
            errorMessage(7, data.lineNumber) # Bad operand
            return -1
        a = regValue(parts[0])
        if a == "":
            errorMessage(7, data.lineNumber) # Bad operand
            return -1
        b = regValue(parts[1])
        if b == "":
            errorMessage(7, data.lineNumber) # Bad operand
            return -1
        # Check that a and b's bit lengths match: can't copy a 16-bit into an 8-bit
        ia = int(a, 16)
        ib = int(b, 16)
        if (ia > 5 and ib < 8) or (ia < 8 and ib > 5):
            errorMessage(7, data.lineNumber) # Bad operand
            return -1
        opndString = "0x" + a + b
        # Set Immediate Addressing Special
        data.opType = ADDR_MODE_IMMEDIATE_SPECIAL
    elif opName[0:3] == "PUL" or opName[0:3] == "PSH":
        # Push or pull operation to calculate the special operand value
        # by looking at all the named registers
        a = 0
        if len(opnd) == 0:
            errorMessage(8, data.lineNumber) # Bad operand
            return -1
        parts = opnd.split(',')
        if len(parts) == 1:
            # A single register
            if opnd == opName[3]:
                # Can't PUL or PSH a register to itself, eg. PULU U doesn't make sense
                errorMessage(8, data.lineNumber) # Bad operand
                return -1
            a = pullRegValue(opnd)
            if a == -1:
                errorMessage(8, data.lineNumber) # Bad operand
                return -1
        else:
            for i in range(0, len(parts)):
                b = pullRegValue(parts[i])
                if b == -1:
                    errorMessage(8, data.lineNumber) # Bad operand
                    return -1
                a = a + b
        opndString = str(a)
        # Set Immediate Addressing Special
        data.opType = ADDR_MODE_IMMEDIATE_SPECIAL
    else:
        # Calculate the operand for all other instructions
        data.indirectFlag = False
        if opnd == " ":
            opnd = ""
        if len(opnd) > 0:
            # Operand string is not empty (it could be, eg. SWI) so process it char by char
            for i in range(0, len(opnd)):
                l = opnd[i]
                if l == ">":
                    # Direct addressing
                    data.opType = ADDR_MODE_DIRECT
                    opndString = ""
                elif l == "#":
                    # Immediate addressing
                    data.opType = ADDR_MODE_IMMEDIATE
                    opndString = ""
                else:
                    if l == "$":
                        # Convert value internally as hex
                        l = "0x"
                    if l == ",":
                        # Indexed addressing
                        opndString = decodeIndexed(opnd, data)
                        if opndString == "":
                            errorMessage(8, data.lineNumber) # Bad operand
                            return -1
                        break
                    if l != " ":
                        opndString = opndString + l

    if len(opndString) > 0 and opndString[0] == "(":
        # Extended indirect addressing
        data.opType = ADDR_MODE_INDEXED
        opndString = opndString[1:-1]
        opndValue = 0x9F
        data.indexAddress = getValue(opndString)
        data.indexAddressingFlag = True
        data.indirectFlag = True

    if len(opndString) > 0 and opndString[0] == "@":
        f = haveGotLabel(opndString)
        if f == -1:
            # Label not seen yet
            if passCount == 2:
                errorMessage(3, data.lineNumber) # No label defined
                return
            newLabel = { "name": opndString, "addr": "UNDEF" }
            labels.append(newLabel)
            if verbose is True and passCount == 1:
                print("Label " + opndString + " found on line " + str(data.lineNumber + 1))
            opndString = "UNDEF"
        else:
            label = labels[f]
            opndString = str(label["addr"])

    '''
    # DEBUG
    if passCount == 1:
        print("OP: " + opName)
        print("OPND: " + opndString)
    '''

    if opndString == "":
        # Set Inherent addressing
        data.opType = ADDR_MODE_INHERENT
    else:
        if data.indirectFlag is False:
            opndValue = getValue(opndString)
        if data.branchOpType > 0:
            # Process a branch value
            if passCount == 1:
                opndValue = 0
            else:
                #print("Branch opnd: " + str(opndValue) + " op: " + opName)
                #print("progCount :" + str(progCount))
                if data.branchOpType == BRANCH_MODE_SHORT:
                    offset = 2 # PC + 1 byte of op + 1 byte of delta
                    data.indexAddress = opndValue - (progCount + 2) 
                    if data.indexAddress < -128 or data.indexAddress > 127:
                        errorMessage(4, lineNumber) # Bad branch
                        return -1
                else:
                    offset = 3 # PC + 1 byte of op + 2 bytes of delta
                    data.indexAddress = opndValue - (progCount + offset)
                
                if data.indexAddress >= 0:
                    opndValue = data.indexAddress
                elif data.branchOpType == BRANCH_MODE_LONG:
                    # Only retain the lowest 16 bits
                    opndValue = (65536 + data.indexAddress) & 0xFFFF
                else:
                    # Only retain the lowest 8 bits
                    opndValue = (256 + data.indexAddress) & 0xFF
        elif data.opType == 0:
            # Set Extended addressing
            data.opType = ADDR_MODE_EXTENDED
    return opndValue


def writeCode(lineParts, op, opnd, data):
    '''
    Write out the machine code and, on the second pass, print out the listing
    Returns false in the instance of an error
    '''
    global progCount

    # Set up a place to store the line's machine code output
    byteString = ""

    if len(op) > 1:
        if data.branchOpType > 0:
            data.opType = data.branchOpType

        # Get the machine code for the op
        if data.opType > 10:
            opValue = op[data.opType - 10]
        else:
            opValue = op[data.opType]
        
        if opValue == -1:
            errorMessage(6, data.lineNumber) # Bad opcode
            return False

        # Poke in the opcode
        if opValue < 256:
            poke(progCount, opValue)
            progCount = progCount + 1
            if passCount == 2:
                byteString = byteString + "{0:02X}".format(opValue)
        if opValue > 255:
            lsb = opValue & 0xFF
            msb = (opValue & 0xFF00) >> 8
            poke(progCount, msb)
            progCount = progCount + 1
            poke(progCount, lsb)
            progCount = progCount + 1
            if passCount == 2:
                byteString = byteString + "{0:02X}".format(msb) + "{0:02X}".format(lsb)
        
        if data.branchOpType == BRANCH_MODE_LONG:
            data.opType = ADDR_MODE_EXTENDED
        elif data.branchOpType == BRANCH_MODE_SHORT:
            data.opType = ADDR_MODE_DIRECT
        
        if data.opType == ADDR_MODE_IMMEDIATE:
            # Immediate addressing
            # Get last character of opcode
            anOp = op[0]
            anOp = anOp[-1]
            if anOp == "D" or anOp == "X" or anOp == "Y" or anOp == "S" or anOp == "U":
                data.opType = ADDR_MODE_EXTENDED
        if data.opType == ADDR_MODE_IMMEDIATE_SPECIAL:
            # Immediate addressing: TFR/EXG OR PUL/PSH
            poke(progCount, int(opnd))
            progCount = progCount + 1
            if passCount == 2:
                byteString = byteString + "{0:02X}".format(opnd)
        if data.opType == ADDR_MODE_INHERENT:
            # Inherent addressing
            data.opType = ADDR_MODE_NONE
        if data.indexAddressingFlag is True:
            poke(progCount, opnd)
            if passCount == 2:
                byteString = byteString + "{0:02X}".format(opnd)
            progCount = progCount + 1
            if data.indexAddress != -1:
                opnd = data.indexAddress
                if opnd > 127 or opnd < -128:
                    # Do 16-bit address
                    data.opType = ADDR_MODE_EXTENDED
                elif opnd > 127 or opnd < -128:
                    # Do 16-bit address
                    data.opType = ADDR_MODE_INDEXED
            else:
                data.opType = ADDR_MODE_NONE
        if data.opType > ADDR_MODE_NONE and data.opType < ADDR_MODE_EXTENDED:
            # Immediate, direct and indexed addressing
            poke(progCount, opnd)
            progCount = progCount + 1
            if passCount == 2:
                byteString = byteString + "{0:02X}".format(opnd)
        if data.opType == ADDR_MODE_EXTENDED:
            # Extended addressing
            lsb = opnd & 0xFF
            msb = (opnd & 0xFF00) >> 8
            poke(progCount, msb)
            progCount = progCount + 1
            poke(progCount, lsb)
            progCount = progCount + 1
            if passCount == 2:
                byteString = byteString + "{0:02X}".format(msb) + "{0:02X}".format(lsb)

    if passCount == 2:
        # Display the line on pass 2
        # Determine the length of the longest label
        t = 6
        if len(labels) > 0:
            for i in range(0, len(labels)):
                label = labels[i]
                if t < len(label["name"]):
                    t = len(label["name"])

        if data.lineNumber == 0:
            # Print the header on the first line
            print("Address   Bytes       Label" + SPACES[:(t - 5)] + "   Op.      Data")
            print("-----------------------------------------------")

        # Handle comment-only lines
        if data.commentTab > 0:
            print(SPACES[:55] + lineParts[0])
            return True

        # First, add the 16-bit address
        if len(byteString) > 0:
            # Display the address at the start of the op's first byte
            displayString = "0x{0:04X}".format(progCount - int(len(byteString) / 2)) + "    "
        elif data.pseudoOpType > 0:
            # Display the address at the start of the pseudoop's first byte
            # NOTE pseudo ops have no byteString, hence this separate entry
            displayString = "0x{0:04X}".format(progCount) + "    "
        else:
            # Display no address for any other line, eg. comment-only lines
            displayString = "          "

        # Add the lines assembled machine code
        displayString = displayString + byteString + SPACES[:(10 - len(byteString))] + "  "

        # Add the label name - or spaces in its place
        displayString = displayString + lineParts[0] + SPACES[:(t - len(lineParts[0]))] + "   "

        # Add the op
        ops = lineParts[1]
        if showupper == 1:
            ops = ops.upper()
        elif showupper == 2:
            ops = ops.lower()
        displayString = displayString + ops + SPACES[:(5 - len(lineParts[1]))] + "    "

        # Add the operand
        if len(lineParts) > 2:
            displayString = displayString + lineParts[2]

        # Add the comment, if there is one
        if len(lineParts) > 3:
            displayString = displayString + SPACES[:(55 - len(displayString))] + lineParts[3]

        # And output the line
        print(displayString)
    return True


def regValue(reg):
    '''
    Return the machine code for the specific register as used in TFR and EXG ops
    '''
    regs = ["D", "X", "Y", "U", "S", "PC", "A", "B", "CC", "DP"]
    vals = ["0", "1", "2", "3", "4", "5", "8", "9", "A", "B"]

    if reg.upper() in regs:
        return vals[regs.index(reg.upper())]
    return ""


def pullRegValue(reg):
    '''
    Return the value for the specific register as used in PUL and PSH ops
    '''
    regs = ["X", "Y", "U", "S", "PC", "A", "B", "CC", "DP", "D"]
    vals = [16, 32, 64, 64, 128, 2, 4, 1, 8, 6]

    if reg.upper() in regs:
        return vals[regs.index(reg.upper())]
    return -1


def getValue(numstring):
    '''
    Convert a string value to an integer value
    '''
    value = 0
    if numstring == "UNDEF":
        value = 0
    elif numstring[:2] == "0x":
        # Hex value
        value = int(numstring, 16)
    elif numstring[0] == "@":
        # A label value
        label = labels[haveGotLabel(numstring)]
        value = label["addr"]
    elif numstring[0] == "%":
        # Binary data
        value = decodeBinary(numstring[1:])
    elif numstring[0] == "'":
        # Ascii data
        value = ord(numstring[1])
    else:
        value = int(numstring)
    return value


def decodeBinary(value):
    '''
    Decode the supplied binary value (a string), eg. '0010010' to an integer
    '''
    a = 0
    for i in range(0, len(value)):
        b = len(value) - i - 1
        if value[b] == "1":
            a = a + (2 ** i)
    return a


def decodeIndexed(opnd, data):
    '''
    Decode the indexed addressing operand.
    Returns the operand value as a string (for the convenience of the calling function, decodeOpnd()
    Retruns and empty string if there was an error of some kind
    '''
    data.opType = ADDR_MODE_INDEXED
    opndValue = 0
    a = -1
    parts = opnd.split(',')

    # Decode the left side of the operand
    l = parts[0]
    if len(l) > 0:
        if l[0] == "(":
            # Operand is Indirect, eg. LDA (5,PC)
            data.indirectFlag = True
            opndValue = 0x10
            # Remove front bracket
            l = l[1:]
        # Decode left of comma: check for specific registers first
        # as these are fixed values in the ISA
        if l == "":
            opndValue = opndValue + 0x84
        elif l.upper() == "A":
            opndValue = opndValue + 0x86
        elif l.upper() == "B":
            opndValue = opndValue + 0x85
        elif l.upper() == "D":
            opndValue = opndValue + 0x8B
        else:
            # The string should be a number
            if l[0] == "$":
                # Convert $ to 0x internally
                l = "0x" + l[1:]
            if l[0] == "@":
                f = haveGotLabel(l)
                if f == -1:
                    if passCount == 2:
                        errorMessage(3, data.lineNumber) # No label defined
                        return ""
                    newLabel = { "name": l, "addr": "UNDEF" }
                    labels.append(newLabel)
                    if verbose is True and passCount == 1:
                        print("Label " + l + " found on line " + str(data.lineNumber + 1))
                    a = 129
                else:
                    label = labels[f]
                    a = label["addr"]
            else:
                a = getValue(l)
            if a > 127 or a < -128:
                # 16-bit
                opndValue = opndValue + 0x89
            elif data.indirectFlag is True or (a > 15 or a < -16):
                # 8-bit
                opndValue = opndValue + 0x88
            elif a == 0:
                # Trap a zero offset call
                opndValue = opndValue + 0x84
                a = -1
            else:
                # 5 bit offset so retain only bits 0-5
                opndValue = a & 0x1F
                a = -1
    
    # Decode the right side of the operand
    if len(parts[0]) == 0:
        # Nothing left of the comma
        opndValue = 0x84
    l = parts[1]
    if l[-1] == ")":
        # Remove bracket (indirect)
        l = l[:-1]
    if l[:2].upper() == "PC":
        # Operand is of the 'n,PCR' type - just set bit 2
        opndValue = opndValue + 4
    if l[-1:] == "+":
        if l[-2:] == "++":
            # ',R++'
            opndValue = 0x91 if data.indirectFlag else 0x81
        else:
            # ',R+' is not allowed with indirection
            if data.indirectFlag is True:
                return ""
            opndValue = 0x90 if data.indirectFlag else 0x80
        # Set the analysed string to the register
        l = l[0]
        # Ignore any prefix value
        a = -1
    if l[0] == "-":
        if l[1] == "-":
            opndValue = 0x93 if data.indirectFlag else 0x83
        else:
            # ',-R' is not allowed with indirection
            if data.indirectFlag is True:
                return ""
            opndValue = 0x92 if data.indirectFlag else 0x82
        # Set the analysed string to the register
        l = l[-1]
        # Ignore any prefix value
        a = -1

    # Add in the register value (assume X, which equals 0 in the register coding)
    rf = 0
    if l.upper() == "Y":
        rf = 0x20
    if l.upper() == "U":
        rf = 0x40
    if l.upper() == "S":
        rf = 0x60

    # Store the index data for later
    data.indexAddress = a
    data.indexAddressingFlag = True
    data.indirectFlag = False

    # Return the operand value as a string
    opndValue = opndValue + rf
    return str(opndValue)


def processPseudoOp(lineParts, opndValue, labelName, data):
    '''
    Process assembler pseudo-ops, ie. directives with specific assembler-level functionality
    '''
    global progCount

    result = False

    if data.pseudoOpType == 1:
        # EQU: assign the operand value to the label declared immediately
        # before the EQU op
        if passCount == 1:
            i = haveGotLabel(labelName)
            label = labels[i]
            label["addr"] = opndValue
            if verbose is True:
                print("Label " + labelName + " set to 0x" + "{0:04X}".format(opndValue) + " (line " + str(data.lineNumber) + ")")
        result = writeCode(lineParts, [], 0, data)

    if data.pseudoOpType == 2:
        # RMB: Reserve the next 'opndValue' bytes and set the label to the current
        # value of the programme counter
        i = haveGotLabel(labelName)
        label = labels[i]
        label["addr"] = progCount
        if verbose is True and passCount == 1:
            print(str(opndValue) + " bytes reserved at address 0x" + "{0:04X}".format(progCount) + " (line " + str(data.lineNumber) + ")")
        for i in range(progCount, progCount + opndValue):
            poke(i, 0x12)
        result = writeCode(lineParts, [], 0, data)
        progCount = progCount + opndValue

    if data.pseudoOpType == 3:
        # FCB: Pokes 'opndValue' into the current byte and sets the label to the
        # address of that byte. NOTE 'opndValue' must be an 8-bit value
        i = haveGotLabel(labelName)
        label = labels[i]
        label["addr"] = progCount
        opndValue = opndValue & 0xFF
        poke(progCount, opndValue)
        if verbose is True and passCount == 1:
            print("The byte at 0x" + "{0:04X}".format(progCount) + " set to 0x" + "{0:02X}".format(opndValue) + " (line " + str(data.lineNumber) + ")")
        result = writeCode(lineParts, [], 0, data)
        progCount = progCount + 1

    if data.pseudoOpType == 4:
        # FDB: Pokes the MSB of 'opndValue' into the current byte and the LSB into
        # the next byte and sets the label to the address of the first byte.
        i = haveGotLabel(labelName)
        label = labels[i]
        label["addr"] = progCount
        opndValue = opndValue & 0xFFFF
        lsb = opndValue & 0xFF
        msb = (opndValue & 0xFF00) >> 8
        if verbose is True and passCount == 1:
            print("The two bytes at 0x" + "{0:04X}".format(progCount) + " set to 0x" + "{0:04X}".format(opndValue) + " (line " + str(data.lineNumber) + ")")
        result = writeCode(lineParts, [], 0, data)
        poke(progCount, msb)
        progCount = progCount + 1
        poke(progCount, lsb)
        progCount = progCount + 1
    
    if data.pseudoOpType == 5:
        # END: The end of the program. This is optional, and does nothing
        result = writeCode(lineParts, [], 0, data)

    if data.pseudoOpType == 6:
        # ORG: set or reset the origin, ie. the value of 'startAddress'
        if passCount == 1 and verbose is True:
            print("Origin set to " + "0x{0:04X}".format(opndValue) + " (line " + str(data.lineNumber) + ")")
        progCount = opndValue
        result = writeCode(lineParts, [], 0, data)
    
    return result

    
def haveGotLabel(labelName):
    '''
    See if we have already encountered 'labelName' in the listing.
    Return -1 if we have not, or the index of the label in the list
    '''

    if len(labels) > 0:
        for i in range(0, len(labels)):
            label = labels[i]
            if label["name"] == labelName:
                # Got a match so return the label's index in the list
                return i

    # Return -1 to indicate 'labelName' is not in the list
    return -1


def poke(address, value):
    '''
    Build up the machine code storage as we poke in new byte values
    '''
    global startAddress
    global code

    if address - startAddress > len(code) - 1:
        a = address - startAddress - len(code)
        if a > 1:
            # 'address' is well beyond the end of the list, so insert
            # padding values in the form of a 6809 NOP opcode
            for i in range(0, a - 1):
                code.append(0x12)
        # Poke the provided value after the padding
        code.append(value)
    elif len(code) == 0:
        # Poke in the first item
        code.append(value)
    else:
        # Replace an existing item
        code[address - startAddress] = value


def errorMessage(errCode, errLine):
    '''
    Display an error message
    '''

    if errCode > 0 and errCode < len(ERRORS):
        print("Error on line " + str(errLine + 1) + ": " + ERRORS[str(errCode)])
    else:
        print("Error on line " + str(errLine + 1) + ": " + str(errCode))
    print("    " + lines[errLine])


def disassembleFile(path):
    global code
    global startAddress

    data = None
    fileExists = os.path.exists(path)
    if fileExists is True:
        with open(path, "r") as file:
            data = file.read()
    else:
        print("No file")

    if data is not None:
        filedata = json.loads(data)
        code = filedata["code"]
        startAddress = filedata["address"]
        
        count = startAddress
        opBytes = 0
        opnd = 0
        special = 0
        preOpByte = 0
        addressMode = 0
        linestring = ""
        byteString = ""
        gotOp = False

        # Run through the machine code byte by byte
        for i in range(0, len(code)):
            # Get the current byte
            byte = ord(code[i])
            
            # Combine the current byte with the previous one, if that
            # was 0x10 or 0x11 (ie. extended ISA)
            if preOpByte != 0:
                byte = (preOpByte << 8) + byte
                preOpByte = 0

            found = False
            op = ""
            opCode = -1

            if gotOp is False:
                # Look for an op first
                if byte == 0x10 or byte == 0x11:
                    # Extended ISA indicator found, so hold for combination
                    # with the next loaded byte of code
                    preOpByte = byte
                    continue
                
                # Run through the main ISA to find the op
                for j in range(0, len(ISA), 6):
                    # Run through each op's possible op codes to find a match
                    for k in range(j + 1, j + 6):
                        if ISA[k] == byte:
                            # Got it
                            op = ISA[j]
                            addressMode = k - j
                            found = True
                            break
                    if found is True:
                        break
                
                if found is False:
                    # Didn't match the byte in the main ISA, so check for a branch op
                    for j in range(0, len(BSA), 3):
                        # Run through each op's possible op codes to find a match
                        for k in range(j + 1, j + 3):
                            if BSA[k] == byte:
                                # Got it
                                op = BSA[j]
                                # Correct the name of an extended branch op
                                if k - j == 2:
                                    op = "L" + op
                                addressMode = k - j + 10
                                found = True
                                break
                        if found is True:
                            break
                
                # If we still haven't matched the op, print a warning 
                if found is False:
                    print("Bad Op: " + "{0:02X}".format(byte))
                    count = count + 1
                    break
                
                # Add the op's value to the machine code output string
                byteString = byteString + "{0:02X}".format(byte)

            # Print or process the line
            if gotOp is False:
                # Set the initial part of the output line
                linestring = "0x{0:04X}".format(count) + "    " + op + "   "
                
                # Add a space for three-character opcodes
                if len(op) == 3:
                    linestring = linestring + " "

                # Gather the operand bytes (if any) according to addressing mode
                if addressing == ADDR_MODE_INHERENT:
                    # Inherent addressing, so no operand: just dump the line
                    print(linestring + setSpacer(linestring) + byteString)
                    count = count + 1
                    byteString = ""
                elif addressing == ADDR_MODE_IMMEDIATE:
                    # Immediate addressing
                    opBytes = 1
                    gotOp = True
                    count = count + 1

                    # Does the immediate postbyte have a special value?
                    # It will for PSH/PUL and TFR/EXG ops
                    if op[:1] == "P":
                        if op[-1:] == "S":
                            special = 1
                        else:
                            special = 2
                    elif op == "TFR" or op == "EXG":
                        special = 3
                    else: 
                        linestring = linestring + "#"
                        # Set the number of operand bytes to gather to the byte-size of the 
                        # named register (eg. two bytes for 16-bit registers
                        if op[-1:] == "X" or op[-1:] == "Y" or op[-1:] == "D" or op[-1:] == "S" or op[-1:] == "U" or op[-2:] == "PC":
                            opBytes = 2
                elif addressing == ADDR_MODE_DIRECT:
                    # Direct addressing
                    linestring = linestring + ">"
                    gotOp = True
                    opBytes = 1
                    count = count + 1
                elif addressing == ADDR_MODE_INDEXED:
                    # Indexed addressing TODO
                    gotOp = True
                    count = count + 1
                elif addressing == ADDR_MODE_EXTENDED:
                    # Extended addressing TODO
                    gotOp = True
                    count = count + 1
                elif addressing > 10:
                    # Handle ranch operation offset bytes
                    gotOp = True
                    count = count + 1
                    opBytes = 1
                    
                    # Is the branch and extended one?
                    if addressing - 10 == BRANCH_MODE_LONG:
                        opBytes = 2
            else:
                # We are handling the operand bytes having found the op
                byteString = byteString + "{0:02X}".format(byte)
                if addressing - 10 == BRANCH_MODE_SHORT:
                    # 'byte' is the 8-bit offset
                    target = 0
                    if byte & 0x80 == 0x80:
                        # Sign bit set
                        target = count + 1 - (255 - byte)
                    else:
                        target = count + 1 + byte
                    linestring = linestring + "${0:04X}".format(target)
                elif addressing == ADDR_MODE_IMMEDIATE and special > 0:
                    if special == 1:
                        # PSHS/PULS
                        linestring = linestring + disPushS(byte)
                    elif special == 2:
                        # PSHU/PULU
                        linestring = linestring + disPushU(byte)
                    else:
                        # TFR/EXG
                        linestring = linestring + disTransfer(byte)
                    special = 0
                else:
                    if opBytes > 0:
                        opnd = opnd + (byte << (8 * (opBytes - 1)))
                    linestring = linestring + "{0:02X}".format(byte)
                
                opBytes = opBytes - 1
                count = count + 1

                if opBytes == 0:
                    # We've got all the operand bytes we need, so output the line
                    sp = setSpacer(linestring)
                    print(linestring + sp + byteString)
                    gotOp = False
                    opnd = 0
                    byteString = ""


def setSpacer(l, c):
    '''
    Return an appropriate number of spaces for the output
    Parameter: 'l' is the input line
    '''
    s = 26 - len(l)
    if s < 1:
        # If the line is too long, just return a couple of spaces
        return "  "
    # Return a space string of suitable length
    return "               "[:s]


def disTransfer(b):
    '''
    Generic TFR/EXG operand string generator
    Parameter: 'b' is the byte value
    '''
    r = ["D", "X", "Y", "U", "S", "PC", "A", "B", "CC", "DP"]
    ss = ""
    ds = ""

    s = (b & 0xF0) >> 4
    d = b & 0x0F

    if s > 5:
        ss = r[s - 2]
    else:
        ss = r[s]

    if d > 5:
        ds = r[d - 2]
    else:
        ds = r[d]

    # Return the operating string, eg. "A,B"
    return ss + "," + ds


def disPushS(b):
    '''
    Pass on the correct register lists for PSHS or PULS
    Parameter: 'b' is the byte value
    '''
    return disPush(b, ["CC", "A", "B", "DP", "X", "Y", "U", "PC"])


def disPushU(b):
    '''
    Pass on the correct register lists for PSHU or PULU
    Parameter: 'b' is the byte value
    '''
    return disPush(b, ["CC", "A", "B", "DP", "X", "Y", "S", "PC"])


def disPush(b, r):
    '''
    Generic PUL/PSH operand string generator
    Parameters: 'b' is the byte value, 'r' the array of register names
    '''
    os = ""
    for i in range (0, 8):
        if b & (2 ** i) > 0:
            # Bit is set, so add the register to the output string, 'os'
            os = os + r[i] + ","
    # Remove the final comma
    if len(os) > 0:
        os = os[0:len(os)-1]
    # Return the output string, eg. "CC,A,X,Y,PC"
    return os


def showHelp():
    '''
    Display Dasm's help information
    '''
    print(" ")
    print("DASM is an assembler/disassembler for the 8-bit Motorola 6809 chip family.")
    print("Place one or more '*.asm' files in this directory and just call the tool,")
    print("or assemble specific files by providing them as arguments.")
    print(" ")
    print("Options:")
    print(" -h / --help    - print help information")
    print(" -v / --verbose - display extra information during assembly")
    print(" -q / --quiet   - display no extra information during assembly")
    print("                  NOTE always overrides -v / -- verbose")
    print(" -s / --start   - Set the start address of the assembled code,")
    print("                  specified as a hex or decimal value")
    print(" -o / --output  - Name the output file")
    print(" -l / --lower   - Display opcodes in lowercase")
    print(" -u / --upper   - Display opcodes in uppercase")
    print("                  NOTE the above two switch will overwrite each other")
    print("                       if both are called: the last one wins. If neither")
    print("                       is used, the output matches the input")
    print(" ")


def writeFile(path):
    '''
    Write the assembled bytes, if any, to a .6809 file
    '''
    
    global code
    global startAddress
    global outFile

    # Build the dictionary
    byteString = ""
    for i in range(0, len(code)):
        byteString = byteString + chr(code[i])

    op = { "address": startAddress,
           "code": byteString }

    #print(op["address"])
    jop = json.dumps(op, ensure_ascii=False)
    #print(jop)

    pwd = os.getcwd()
    fileExists = os.path.exists(os.path.join(pwd, outFile))

    with open(outFile, "w") as file:
        file.write(jop)

    print("File " + outFile + " written")


def getFiles():
    '''
    Determine all the '.asm' files in the script's directory, and process them one by one
    '''
    pwd = os.getcwd()
    files = [file for file in os.listdir(pwd) if os.path.isfile(os.path.join(pwd, file))]

    # Count the number of .asm and .6809 files
    acount = 0
    dcount = 0
    for file in files:
        if file[-3:] == "asm":
            acount = acount + 1
        if exfile[-4:] == "6809":
            dcount = dcount + 1

    if acount == 1:
        if verbose is True:
            print("Processing 1 .asm file in " + pwd)
    elif acount > 1:
        if verbose is True:
            print("Processing " + str(acount) + " .asm files in " + pwd)
    else:
        if verbose is True:
            print("No suitable .asm files found in " + pwd)

    if dcount == 1:
        if verbose is True:
            print("Processing 1 .6809 file in " + pwd)
    elif dcount > 1:
        if verbose is True:
            print("Processing " + str(dcount) + " .6809 files in " + pwd)
    else:
        if verbose is True:
            print("No suitable .6809 files found in " + pwd)

    handleFiles(files)


def handleFiles(files):
    
    if len(files) > 0:
        for file in files:
            if file[-3:] == "asm":
                processFile(file)
            if file[-4:] == "6809":
                disassembleFile(file)


if __name__ == '__main__':
    '''
    The tool's entry point
    '''
    # Do we have any arguments?
    if len(sys.argv) > 1:
        filesFlag = False
        argFlag = False
        files = []
        for index, item in enumerate(sys.argv):
            if argFlag is True:
                argFlag = False
            elif item == "-v" or item == "--verbose":
                # Handle the -v / --verbose switch
                verbose = True
            elif item == "-q" or item == "--quiet":
                # Handle the -q / --quiet switch
                verbose = False
            elif item == "-u" or item == "--upper":
                # Handle the -u / --upper switch
                showupper = 1
            elif item == "-l" or item == "--lower":
                # Handle the -l / --lower switch
                showupper = 2
            elif item == "-s" or item == "--startaddress":
                # Handle the -s / --startaddress switch
                if index + 1 >= len(sys.argv):
                    print("Error: -s / --startaddress must be followed by an address")
                    sys.exit(0)
                address = sys.argv[index + 1]
                base = 10
                if address[:2] == "0x" or address[:1] == "$":
                    base = 16
                try:
                    startAddress = int(sys.argv[index + 1], base)
                except err:
                    print("Error: -s / --startAddress must be followed by an address")
                    sys.exit(0)
                if verbose is True:
                    print("Code start address set to 0x{0:04X}".format(startAddress))
                argFlag = True
            elif item == "-h" or item == "--help":
                # Handle the -h / --help switch
                showHelp()
                sys.exit(0)
            elif item == "-o" or item == "--outfile":
                if index + 1 >= len(sys.argv):
                    print("Error: -0 / --outfile must be followed by a file name")
                    sys.exit(0)
                outFile = sys.argv[index + 1]
                parts = outFile.split(".")
                if parts == 1:
                    outFile = outFile + ".6809"
                argFlag = True
            else:
                if index != 0 and argFlag is False:
                    # Handle any included .asm files
                    if item[-3:] == "asm" or item[-4:] == "6809":
                        files.append(item)
                    else:
                        print(item + " is not a .asm or .6809 file - ignoring")
        
        if len(files) == 0:
            # By default get all the .asm files in the working directory
            getFiles()
        else:
            # Process any named files
            handleFiles(files)
    else:
        # By default get all the .asm files in the working directory
        getFiles()

    sys.exit(0)
