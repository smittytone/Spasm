#!/usr/bin/env python3

"""
'SPASM' -- Smittytone's Primary 6809 ASeMmbler

Version:
    1.0.0

Copyright:
    2019, Tony Smith (@smittytone)

License:
    MIT (terms attached to this repo)
"""

##########################################################################
# Program library imports                                                #
##########################################################################

import os
import sys
import json

##########################################################################
# Application-specific constants                                         #
##########################################################################

SPACES = "                                                         "
NOUGHTS = "000000000000000000000000000000000000"
ERRORS = {"0": "No error",
          "1": "Bad mnemonic/opcode",
          "2": "Duplicate label",
          "3": "Undefined label",
          "4": "Bad branch op",
          "5": "Bad operand",
          "6": "Decode error",
          "7": "Bad TFR/EXG operand",
          "8": "Bad PUL/PSH operand",
          "9": "Bad address"}
ADDR_MODE_NONE              = 0 # pylint: disable=C0326;
ADDR_MODE_IMMEDIATE         = 1 # pylint: disable=C0326;
ADDR_MODE_DIRECT            = 2 # pylint: disable=C0326;
ADDR_MODE_INDEXED           = 3 # pylint: disable=C0326;
ADDR_MODE_EXTENDED          = 4 # pylint: disable=C0326;
ADDR_MODE_INHERENT          = 5 # pylint: disable=C0326;
ADDR_MODE_IMMEDIATE_SPECIAL = 11 # pylint: disable=C0326;
BRANCH_MODE_SHORT           = 1 # pylint: disable=C0326;
BRANCH_MODE_LONG            = 2 # pylint: disable=C0326;

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

##########################################################################
# Application globals                                                    #
##########################################################################

verbose = True
start_address = 0x0000
prog_count = 0
pass_count = 0
show_upper = 0
labels = None
code = None
out_file = None

##########################################################################
# Application-specific classes                                           #
##########################################################################

class LineData:
    '''
    A simple class to hold the temporary decode data for a line of
    6809 assembly code.
    '''
    indirect_flag = False
    index_addressing_flag = False
    index_address = -1
    line_number = 0
    comment_tab = 0
    op_type = 0
    branch_op_type = 0
    pseudo_op_type = 0
    pseudo_op_value = ""
    op = []
    opnd = -1

    def __init__(self):
        self.op = []


##########################################################################
# Functions                                                              #
##########################################################################

def assemble_file(file_path):
    '''
    Assemble a single '.asm' file using a two-pass process to identify
    labels and pseudo-ops, etc.

    Args:
        file_path (str): The path to a .asm file.
    '''

    global pass_count, prog_count, code, labels

    # Clear the storage arrays
    lines = []
    labels = []
    code = bytearray()

    # Check that the passed file is available to process
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            lines = list(file)
    else:
        show_verbose("[ERROR] File " + file_path + " does not exist, skipping")
        return

    if verbose is True:
        print("****** PROCESSING FILE  ******")
        print(file_path)

    # Do the assembly in two passes
    break_flag = False
    for asm_pass in range(1, 3):
        # Start a pass
        prog_count = start_address
        pass_count = asm_pass
        show_verbose("****** ASSEMBLY PASS #" + str(asm_pass) + " ******")
        i = 0
        for line in lines:
            # Parse the lines one at a time
            result = parse_line(line, i)
            if result is False:
                # Error in processing: print post
                print("Processing error in line " + str(i + 1) + " -- halting assembly")
                print(">>> " + line)
                break_flag = True
                # Break out of the line-by-line loop
                break
            i += 1
        if break_flag is True:
            # Break out of the pass-by-pass loop
            break

    # Post-assembly, dump the machine code, provided there was no error
    if verbose is True and break_flag is False:
        print(" ")
        print("Machine code dump")
        prog_count = start_address
        for i in range(0, len(code), 8):
            # Add the initial address
            display_str = "0x{0:04X}".format(prog_count) + "  "

            for j in range(0, 8):
                if i + j < len(code):
                    # Add the bytes, one at a time, separated by whitespace
                    display_str += "  {0:02X}".format(code[i + j])
                    prog_count += 1
            print(display_str)

    # Write out the machine code file
    if out_file is not None and break_flag is False:
        if out_file == "*":
            o_file, _ = os.path.splitext(file_path)
            write_file(o_file + ".6089")
        else:
            write_file(out_file)


def parse_line(line, line_number):
    '''
    Process a single line of assembly, on a per-pass basis.

    Each line is segmented by space characters, and we remove extra spaces from
    all line parts other than comments.
    KNOWN ISSUE: You cannot therefore have a space set using the Ascii indicator, '
    TODO: Some way of handling string constants

    Args:
        line        (list): A line of program as a raw string.
        line_number (int):  The current line (starts at 0).

    Returns:
        bool: False if an error occurred, or True.
    '''

    # Split the line at the line terminator to remove the carriage return
    line_parts = line.splitlines()
    line = line_parts[0]

    # Check for comment lines
    comment = ""
    comment_tab = line.find(";")
    if comment_tab != -1:
        # Found a comment line so re-position it
        line_parts = line.split(";", 1)
        comment = ";" + line_parts[len(line_parts) - 1]
        line = line_parts[0]

    # Segment the line by spaces
    line_parts = line.split(" ")

    # Remove empty entries (ie. instances of multiple spaces)
    j = 0
    while True:
        if j == len(line_parts): break
        if not line_parts[j]:
            line_parts.pop(j)
        else:
            j += 1

    # At this point, typical line might be:
    #   lineParts[0] = "@start_address"
    #   lineParts[1] = "EQU"
    #   lineParts[2] = "$FFFF"
    #   lineParts[3] = ";This is a comment"
    # Empty lines will be present in the list as empty strings

    # Begin line decoding: create a line data object
    line_data = LineData()
    line_data.line_number = line_number

    if not line_parts:
        # This is a comment-only line, or empty line,
        # so assemble a basic empty list
        if comment_tab != -1 and pass_count == 2:
            # We have a comment, so just dump it out on pass 2
            line_data.comment_tab = comment_tab
            write_code([comment, " ", " ", " "], line_data)
            # And return to go and process the next line
            return True
        line_parts = [" ", " "]

    # Process the line's components
    # Check for an initial label
    label = line_parts[0]
    if label[0] == "@":
        # Found a label - store it if we need to
        got_label = index_of_label(label)
        if got_label != -1:
            # The label has already been seen during assembly
            label = labels[got_label]
            if pass_count == 1:
                if label["addr"] != "UNDEF":

                    error_message(2, line_number) # Duplicate label
                    return False
                # Set the label address
                label["addr"] = prog_count
                # Output the label valuation
                show_verbose("Label " + label["name"] + " set to 0x" + "{0:04X}".format(prog_count) + " (line " + str(line_number + 1) + ")")
        else:
            # Record the newly found label
            labels.append({"name": label, "addr": prog_count})
            if verbose is True and pass_count == 1: print("Label " + label + " found on line " + str(line_number + 1))
    else:
        # Not a label, so insert a blank - ie. ensure the op will be in lineParts[1]
        line_parts.insert(0, " ")

    # If there is no third field, add an empty one
    if len(line_parts) == 2: line_parts.append(" ")

    # Put the comment string, if there is one, into the comment field, lineParts[3]
    # Otherwise drop in an empty field
    line_parts.append(comment if comment else " ")

    # Check the opcode
    if line_parts[1] != " ":
        result = decode_op(line_parts[1], line_data)
        if result is False: return False

    # TODO What if there's no op, or are we dealing with dangling lines?

    # Calculate the operand
    result = decode_opnd(line_parts[2], line_data)
    if result is False: return False

    # Handle a a pseudo-op (assembler directive) if we have one
    if line_data.pseudo_op_type > 0:
        # We have a pseudo-op
        result = process_pseudo_op(line_parts, line_data)
    else:
        # We have a regular op
        result = write_code(line_parts, line_data)

    return result


def decode_op(an_op, line):
    '''
    Check that the specified op from the listing is a valid mnemonic.

    Args:
        an_op (str):      The extracted mnemonic.
        line  (LineData): An object representing the decoded line.

    Returns:
        list: Contains 1 item (pseudo op), 2 items (branch op) or 6 items (op).
              Each list contains the op name then integers for the opcode's machine
              code values for each available addressing mode (or -1 for an unknown op)
    '''

    # Make mnemonic upper case
    an_op = an_op.upper()

    # Check for pseudo-ops
    pseudo_ops = ("EQU", "RMB", "FCB", "FDB", "END", "ORG", "SETDP")
    if an_op in pseudo_ops:
        line.op = [an_op]
        line.pseudo_op_type = pseudo_ops.index(an_op) + 1
        return True

    # Check for regular instructions
    if an_op in ISA:
        index = ISA.index(an_op)
        for i in range(index, index + 6):
            line.op.append(ISA[i])
        return True

    # Check for branch instructions
    if an_op[0] == "L":
        # Handle long branch instructions
        line.branch_op_type = BRANCH_MODE_LONG
        an_op = an_op[1:]
    else:
        line.branch_op_type = BRANCH_MODE_SHORT

    if an_op in BSA:
        index = BSA.index(an_op)
        for i in range(index, index + 3):
            line.op.append(BSA[i])
        return True

    # No instruction found: that's a Bad Op error
    error_message(1, line.line_number)
    return False


def decode_opnd(an_opnd, line):
    '''
    This function decodes the operand.

    Args:
        an_opnd (str): The extracted operand.
        line  (LineData): An object representing the decoded line.

    Returns
        int: the operand value, or -1 if the operand value could not be determined
    '''
    global prog_count

    opnd_str = ""
    opnd_value = 0
    op_name = ""
    line.op_type = ADDR_MODE_NONE

    if len(line.op) > 1: op_name = line.op[0]

    if op_name in ("EXG", "TFR"):
        # Register swap operation to calculate the special operand value
        # by looking at the named registers separated by a comma
        parts = an_opnd.split(',')
        if len(parts) != 2 or parts[0] == parts[1]:
            error_message(7, line.line_number) # Bad operand
            return -1

        source = get_reg_value(parts[0])
        if not source:
            error_message(7, line.line_number) # Bad operand
            return -1

        dest = get_reg_value(parts[1])
        if not dest:
            error_message(7, line.line_number) # Bad operand
            return -1

        # Check that a and b's bit lengths match: can't copy a 16-bit into an 8-bit
        source_size = int(source, 16)
        dest_size = int(dest, 16)
        if (source_size > 5 and dest_size < 8) or (source_size < 8 and dest_size > 5):
            error_message(7, line.line_number) # Bad operand
            return -1
        opnd_str = "0x" + source + dest
        line.op_type = ADDR_MODE_IMMEDIATE_SPECIAL
    elif op_name[0:3] in ("PUL", "PSH"):
        # Push or pull operation to calculate the special operand value
        # by looking at all the named registers
        post_byte = 0
        if not an_opnd:
            error_message(8, line.line_number) # Bad operand
            return -1
        parts = an_opnd.split(',')
        if len(parts) == 1:
            # A single register
            if an_opnd == op_name[3]:
                # Can't PUL or PSH a register to itself, eg. PULU U doesn't make sense
                error_message(8, line.line_number) # Bad operand
                return -1
            post_byte = get_pull_reg_value(an_opnd)
            if post_byte == -1:
                error_message(8, line.line_number) # Bad operand
                return -1
        else:
            for part in parts:
                reg_val = get_pull_reg_value(part)
                if reg_val == -1:
                    error_message(8, line.line_number) # Bad operand
                    return -1
                post_byte += reg_val
        opnd_str = str(post_byte)
        line.op_type = ADDR_MODE_IMMEDIATE_SPECIAL
    else:
        # Calculate the operand for all other instructions
        if an_opnd == " ": an_opnd = ""
        if an_opnd:
            # Operand string is not empty (it could be, eg. SWI) so process it char by char
            for op_char in an_opnd:
                if op_char == ">":
                    # Direct addressing
                    line.op_type = ADDR_MODE_DIRECT
                    opnd_str = ""
                elif op_char == "#":
                    # Immediate addressing
                    line.op_type = ADDR_MODE_IMMEDIATE
                    opnd_str = ""
                else:
                    # Convert value internally as hex
                    if op_char == "$": op_char = "0x"

                    # Operand could use indexed addressing or be a FCB/FDB value list
                    if op_char == ",":
                        if line.pseudo_op_type == 0:
                            # It's an indexed addressing operand, so decode it
                            opnd_str = decode_indexed(an_opnd, line)
                            if opnd_str == "":
                                error_message(8, line.line_number) # Bad operand
                                return -1
                            break
                    # Remove spaces and re-assemble string
                    if op_char != " ": opnd_str += op_char

    if opnd_str and opnd_str[0] == "@":
        # Operand is a label
        index = index_of_label(opnd_str)
        if index == -1:
            # Label has not been seen yet
            if pass_count == 2:
                # Any new label seen on pass 2 indicates an error
                error_message(3, line.line_number) # No label defined
                return -1

            # Make a new label
            labels.append({"name": opnd_str, "addr": "UNDEF"})
            show_verbose("Label " + opnd_str + " found on line " + str(line.line_number + 1))
            opnd_str = "UNDEF"
        else:
            label = labels[index]
            opnd_value = label["addr"]
            opnd_str = str(opnd_value)

    if not opnd_str:
        # No operand found, so this must be an Inherent Addressing op
        line.op_type = ADDR_MODE_INHERENT
    else:
        if line.pseudo_op_type in (3, 4):
            # FCB/FDB - check for value lists
            parts = opnd_str.split(",")
            if len(parts) > 1:
                # We have a list of values. Convert them to hex bytes for internal processing
                byte_string = ""
                format_str = "{0:02X}" if line.pseudo_op_type == 3 else "{0:04X}"
                for part in parts:
                    byte_string += format_str.format(get_int_value(part))
                # Preserve the byte string for later then bail
                line.pseudo_op_value = byte_string
                opnd_value = 0
            else:
                # Not a list, so just get the value of the operand
                opnd_value = get_int_value(opnd_str)
        elif line.indirect_flag is False:
            # Get the value for any operand other than indexed
            opnd_value = get_int_value(opnd_str)

        if line.branch_op_type > 0:
            # Process a branch value
            if pass_count == 1:
                # Don't calculate the branch offset on the first pass
                opnd_value = 0
            else:
                if line.branch_op_type == BRANCH_MODE_SHORT:
                    offset = 2 # PC + 1 byte of op + 1 byte of delta
                    line.index_address = opnd_value - (prog_count + 2)
                    if line.index_address < -128 or line.index_address > 127:
                        error_message(4, line.line_number) # Bad branch type: out of range offset
                        return -1
                else:
                    offset = 3 # PC + 1 byte of op + 2 bytes of delta
                    line.index_address = opnd_value - (prog_count + offset)

                if line.index_address >= 0:
                    opnd_value = line.index_address
                elif line.branch_op_type == BRANCH_MODE_LONG:
                    # Only retain the lowest 16 bits
                    opnd_value = (65536 + line.index_address) & 0xFFFF
                else:
                    # Only retain the lowest 8 bits
                    opnd_value = (256 + line.index_address) & 0xFF
        elif line.op_type == ADDR_MODE_NONE:
            # Set Extended addressing
            line.op_type = ADDR_MODE_EXTENDED

    line.opnd = opnd_value
    return opnd_value


def process_pseudo_op(line_parts, line):
    '''
    Process assembler pseudo-ops, ie. directives with specific assembler-level functionality.

    Args:
        line_parts (list):       The program components of the current line (see 'parse_line()').
        line       (DecodeData): The decoded line data.

    Returns:
        bool: False if an error occurred, or True.
    '''

    global prog_count, start_address

    result = False
    label_name = line_parts[0]
    if label_name == " ": label_name = ""
    opnd_value = line.opnd

    if line.pseudo_op_type == 1:
        # EQU: assign the operand value to the label declared immediately
        # before the EQU op
        if pass_count == 1:
            idx = index_of_label(label_name)
            label = labels[idx]
            label["addr"] = opnd_value
            show_verbose("Label " + label_name + " set to 0x" + "{0:04X}".format(opnd_value) + " (line " + str(line.line_number + 1) + ")")
        result = write_code(line_parts, line)

    if line.pseudo_op_type == 2:
        # RMB: Reserve the next 'opnd_value' bytes and set the label to the current
        # value of the programme counter
        idx = index_of_label(label_name)
        if idx != -1:
            label = labels[idx]
            label["addr"] = prog_count

        if verbose is True and pass_count == 1:
            print(str(opnd_value) + " bytes reserved at address 0x" + "{0:04X}".format(prog_count) + " (line " + str(line.line_number + 1) + ")")

        for i in range(prog_count, prog_count + opnd_value): poke(i, 0x12)
        result = write_code(line_parts, line)
        prog_count += opnd_value

    if line.pseudo_op_type == 3:
        # FCB: Pokes 'opnd_value' into the current byte and sets the label to the
        # address of that byte. 'opnd_value' must be an 8-bit value
        idx = index_of_label(label_name)
        if idx != -1:
            label = labels[idx]
            label["addr"] = prog_count

        if line.pseudo_op_value:
            # Multiple bytes to poke in, in the form of a hex string
            # This is set in 'decode_opnd'
            count = 0

            for i in range(0, len(line.pseudo_op_value), 2):
                byte = line.pseudo_op_value[i:i+2]
                if i == 0:
                    line.opnd = int(byte)
                    result = write_code(line_parts, line)
                elif pass_count == 2: print("0x{0:04X}".format(prog_count) + "    " + byte)
                poke(prog_count, int(byte, 16))
                prog_count += 1
                count += 1

            if verbose is True and pass_count == 1:
                print(str(count) + " bytes written at 0x" + "{0:04X}".format(prog_count - count) + " (line " + str(line.line_number + 1) + ")")
        else:
            # Only a single byte to drop in
            # This is set in 'decode_opnd'
            opnd_value = opnd_value & 0xFF
            poke(prog_count, opnd_value)

            if verbose is True and pass_count == 1:
                print("The byte at 0x" + "{0:04X}".format(prog_count) + " set to 0x" + "{0:02X}".format(opnd_value) + " (line " + str(line.line_number + 1) + ")")

            result = write_code(line_parts, line)
            prog_count += 1

    if line.pseudo_op_type == 4:
        # FDB: Pokes the MSB of 'opnd_value' into the current byte and the LSB into
        # the next byte and sets the label to the address of the first byte.
        idx = index_of_label(label_name)
        if idx != -1:
            label = labels[idx]
            label["addr"] = prog_count

        if line.pseudo_op_value:
            # Multiple bytes to poke in, in the form of a hex string
            # This is set in 'decode_opnd'
            count = 0
            initial = 0
            byte_str = ""

            for i in range(0, len(line.pseudo_op_value), 2):
                byte = line.pseudo_op_value[i:i+2]
                byte_str += byte
                count += 1
                if i == 0:
                    initial = int(byte, 16) << 8
                elif i == 2:
                    initial += int(byte, 16)
                    line.opnd = initial
                    result = write_code(line_parts, line)
                    byte_str = ""
                elif pass_count == 2 and count % 2 == 0:
                    print("0x{0:04X}".format(prog_count - 2) + "    " + byte_str)
                    byte_str = ""

                poke(prog_count, int(byte, 16))
                prog_count += 1

            if verbose is True and pass_count == 1:
                print(str(count) + " bytes written at 0x" + "{0:04X}".format(prog_count - count) + " (line " + str(line.line_number + 1) + ")")
        else:
            # Only a single 16-bit value to drop in
            # This is set in 'decode_opnd'
            opnd_value = opnd_value & 0xFFFF
            lsb = opnd_value & 0xFF
            msb = (opnd_value & 0xFF00) >> 8
            if verbose is True and pass_count == 1:
                print("The two bytes at 0x" + "{0:04X}".format(prog_count) + " set to 0x" + "{0:04X}".format(opnd_value) + " (line " + str(line.line_number + 1) + ")")
            result = write_code(line_parts, line)
            poke(prog_count, msb)
            poke(prog_count + 1, lsb)
            prog_count += 2

    if line.pseudo_op_type == 5:
        # END: The end of the program. This is optional, and currently does nothing
        result = write_code(line_parts, line)

    if line.pseudo_op_type == 6:
        # ORG: set or reset the origin
        if pass_count == 1 and verbose is True:
            print("Origin set to " + "0x{0:04X}".format(opnd_value) + " (line " + str(line.line_number + 1) + ")")
        if prog_count == start_address: start_address = opnd_value
        prog_count = opnd_value
        result = write_code(line_parts, line)
        if label_name:
            idx = index_of_label(label_name)
            label = labels[idx]
            label["addr"] = opnd_value
            if pass_count == 1 and verbose is True:
                print("Label " + label["name"] + " set to 0x" + "{0:04X}".format(opnd_value) + " (line " + str(line.line_number + 1) + ")")

    return result


def decode_indexed(opnd, line):
    '''
    Decode the indexed addressing operand.

    Args:
        opnd (str):        The extracted operand.
        line (DecodeData): The decoded line data.

    Returns:
        str: The operand value as a string, or an empty string if there was an error.
    '''

    line.op_type = ADDR_MODE_INDEXED
    opnd_value = 0
    byte_value = -1
    parts = opnd.split(',')

    # Decode the left side of the operand
    left = parts[0]
    if left:
        if left[0] == "(":
            # Addressing mode is Indirect Indexed, eg. LDA (5,PC)
            line.indirect_flag = True
            opnd_value = 0x10
            # Remove front bracket
            left = left[1:]

        # Decode left of comma: check for specific registers first
        # as these are fixed values in the ISA
        if left == "":
            opnd_value += 0x84
        elif left.upper() == "A":
            opnd_value += 0x86
        elif left.upper() == "B":
            opnd_value += 0x85
        elif left.upper() == "D":
            opnd_value += 0x8B
        else:
            # The string should be a number
            if left[0] == "$":
                # Convert $ to 0x internally
                left = "0x" + left[1:]
            if left[0] == "@":
                index = index_of_label(left)
                if index == -1:
                    if pass_count == 2:
                        error_message(3, line.line_number) # No label defined
                        return ""
                    labels.append({"name": left, "addr": "UNDEF"})
                    if verbose is True and pass_count == 1: print("Label " + left + " found on line " + str(line.line_number + 1))
                    byte_value = 129
                else:
                    label = labels[index]
                    byte_value = label["addr"]
            else:
                byte_value = get_int_value(left)
            if byte_value > 127 or byte_value < -128:
                # 16-bit
                opnd_value += 0x89
            elif line.indirect_flag is True or (byte_value > 15 or byte_value < -16):
                # 8-bit
                opnd_value += 0x88
            elif byte_value == 0:
                # Trap a zero offset call
                opnd_value += + 0x84
                byte_value = -1
            else:
                # 5 bit offset so retain only bits 0-5
                opnd_value = byte_value & 0x1F
                byte_value = -1
    else:
        # Nothing left of the comma
        opnd_value = 0x84

    # Decode the right side of the operand
    right = parts[1]
    if right[-1] == ")":
        # Remove bracket (indirect)
        right = right[:-1]
    if right[:2].upper() == "PC":
        # Operand is of the 'n,PCR' type - just set bit 2
        opnd_value += 4
    if right[-1:] == "+":
        if right[-2:] == "++":
            # ',R++'
            opnd_value = 0x91 if line.indirect_flag else 0x81
        else:
            # ',R+' is not allowed with indirection
            if line.indirect_flag is True: return ""
            opnd_value = 0x90 if line.indirect_flag else 0x80 # NOTE Makes no sense with above call CHECK
        # Set the analysed string to the register
        right = right[0]
        # Ignore any prefix value
        byte_value = -1
    if right[0] == "-":
        if right[1] == "-":
            opnd_value = 0x93 if line.indirect_flag else 0x83
        else:
            # ',-R' is not allowed with indirection
            if line.indirect_flag is True: return ""
            opnd_value = 0x92 if line.indirect_flag else 0x82 # NOTE Makes no sense with above call CHECK
        # Set the analysed string to the register
        right = right[-1]
        # Ignore any prefix value
        byte_value = -1

    # Add in the register value (assume X, which equals 0 in the register coding)
    reg = 0
    if right.upper() == "Y": reg = 0x20
    if right.upper() == "U": reg = 0x40
    if right.upper() == "S": reg = 0x60

    # Store the index data for later
    line.index_address = byte_value
    line.index_addressing_flag = True
    line.indirect_flag = False

    # Return the operand value as a string
    opnd_value += reg
    return str(opnd_value)


def get_reg_value(reg):
    '''
    Return the machine code for the specific register as used in TFR and EXG ops.

    Args:
        reg (str): The register name.

    Returns:
        str: Single-character hex string
    '''

    reg = reg.upper()
    regs = ("D", "X", "Y", "U", "S", "PC", "A", "B", "CC", "DP")
    vals = ("0", "1", "2", "3", "4", "5", "8", "9", "A", "B")
    if reg in regs: return vals[regs.index(reg)]
    return ""


def get_pull_reg_value(reg):
    '''
    Return the value for the specific register as used in PUL and PSH ops.

    Args:
        reg (str): The register name.

    Returns:
        int: The register value.
    '''

    reg = reg.upper()
    regs = ("X", "Y", "U", "S", "PC", "A", "B", "CC", "DP", "D")
    vals = (16, 32, 64, 64, 128, 2, 4, 1, 8, 6)
    if reg in regs: return vals[regs.index(reg)]
    return -1


def get_int_value(num_str):
    '''
    Convert a prefixed string value to an integer.

    Args:
        num_str (str): The known numeric string.

    Returns:
        int: A positive integer value.
    '''

    value = 0
    if num_str == "UNDEF":
        value = 0
    elif num_str[:2] == "0x":
        # Hex value
        value = int(num_str, 16)
    elif num_str[0] == "@":
        # A label value
        label = labels[index_of_label(num_str)]
        value = label["addr"]
    elif num_str[0] == "%":
        # Binary data
        value = decode_binary(num_str[1:])
    elif num_str[0] == "'":
        # Ascii data in the next character
        value = ord(num_str[1])
    else:
        value = int(num_str)
    return value


def decode_binary(bin_str):
    '''
    Decode the supplied binary value (as a string, eg. '0010010') to an integer.

    Args:
        bin_str (str): A string binary representation.

    Returns:
        int: The intger value.
    '''

    value = 0
    for i in range(0, len(bin_str)):
        bit = len(bin_str) - i - 1
        if bin_str[bit] == "1": value += (2 ** i)
    return value


def index_of_label(label_name):
    '''
    See if we have already encountered 'label_name' in the listing.

    Args:
        label_name (str): The name of the found label.

    Returns:
        int: The index of the label in the list, or -1 if it isn't yet recorded.
    '''

    if labels:
        for label in labels:
            if label["name"] == label_name:
                # Got a match so return the label's index in the list
                return labels.index(label)
    # Return -1 to indicate 'label_name' is not in the list
    return -1


def write_code(line_parts, line):
    '''
    Write out the machine code and, on the second pass, print out the listing.

    Args:
        line_parts (list):       The program components of the current line (see 'parse_line()').
        line       (DecodeData): The decoded line data.

    Returns:
        bool: False in the instance of an error, otherwise True.
    '''
    global prog_count

    # Set up a place to store the line's machine code output
    byte_str = ""

    if len(line.op) > 1:
        if line.branch_op_type > 0: line.op_type = line.branch_op_type

        # Get the machine code for the op
        op_value = line.op[line.op_type - 10 if line.op_type > 10 else line.op_type]

        if op_value == -1:
            error_message(6, line.line_number) # Bad opcode
            return False

        # Poke in the opcode
        if op_value < 256:
            poke(prog_count, op_value)
            prog_count += 1
            if pass_count == 2: byte_str += "{0:02X}".format(op_value)
        if op_value > 255:
            lsb = op_value & 0xFF
            msb = (op_value & 0xFF00) >> 8
            poke(prog_count, msb)
            prog_count += 1
            poke(prog_count, lsb)
            prog_count += 1
            if pass_count == 2: byte_str += ("{0:02X}".format(msb) + "{0:02X}".format(lsb))

        if line.branch_op_type == BRANCH_MODE_LONG: line.op_type = ADDR_MODE_EXTENDED
        if line.branch_op_type == BRANCH_MODE_SHORT: line.op_type = ADDR_MODE_DIRECT

        if line.op_type == ADDR_MODE_IMMEDIATE:
            # Immediate addressing
            # Get last character of opcode
            an_op = line.op[0]
            an_op = an_op[-1]
            if an_op in ("D", "X", "Y", "S", "U"): line.op_type = ADDR_MODE_EXTENDED
        if line.op_type == ADDR_MODE_IMMEDIATE_SPECIAL:
            # Immediate addressing: TFR/EXG OR PUL/PSH
            poke(prog_count, int(line.opnd))
            prog_count += 1
            if pass_count == 2: byte_str += "{0:02X}".format(line.opnd)
        if line.op_type == ADDR_MODE_INHERENT:
            # Inherent addressing
            line.op_type = ADDR_MODE_NONE
        if line.index_addressing_flag is True:
            poke(prog_count, line.opnd)
            if pass_count == 2: byte_str += "{0:02X}".format(line.opnd)
            prog_count += 1
            if line.index_address != -1:
                line.opnd = line.index_address
                if line.opnd > 127 or line.opnd < -128:
                    # Do 16-bit address
                    line.op_type = ADDR_MODE_EXTENDED
                elif line.opnd > 127 or line.opnd < -128:
                    # Do 16-bit address
                    line.op_type = ADDR_MODE_INDEXED
            else:
                line.op_type = ADDR_MODE_NONE
        if line.op_type > ADDR_MODE_NONE and line.op_type < ADDR_MODE_EXTENDED:
            # Immediate, direct and indexed addressing
            poke(prog_count, line.opnd)
            prog_count += 1
            if pass_count == 2: byte_str += "{0:02X}".format(line.opnd)
        if line.op_type == ADDR_MODE_EXTENDED:
            # Extended addressing
            lsb = line.opnd & 0xFF
            msb = (line.opnd & 0xFF00) >> 8
            poke(prog_count, msb)
            poke(prog_count + 1, lsb)
            prog_count += 2
            if pass_count == 2: byte_str += ("{0:02X}".format(msb) + "{0:02X}".format(lsb))

    if pass_count == 2:
        # Display the line on pass 2
        # Determine the length of the longest label
        label_len = 6
        if labels:
            for label in labels:
                if label_len < len(label["name"]): label_len = len(label["name"])

        if line.line_number == 0:
            # Print the header on the first line
            print("Address   Bytes       Label" + SPACES[:(label_len - 5)] + "   Op.      Data")
            print("-----------------------------------------------")

        # Handle comment-only lines
        if line.comment_tab > 0:
            print(SPACES[:55] + line_parts[0])
            return True

        # First, add the 16-bit address
        if byte_str:
            # Display the address at the start of the op's first byte
            display_str = "0x{0:04X}".format(prog_count - int(len(byte_str) / 2)) + "    "
        elif line.pseudo_op_type > 0:
            # Display the address at the start of the pseudoop's first byte
            # NOTE most pseudo ops have no byteString, hence this separate entry
            display_str = "0x{0:04X}".format(prog_count) + "    "
            if line.pseudo_op_type == 3: byte_str = "{0:02X}".format(line.opnd)
            if line.pseudo_op_type == 4: byte_str = "{0:04X}".format(line.opnd)
            if line.pseudo_op_type == 6: display_str = "          "
        else:
            # Display no address for any other line, eg. comment-only lines
            display_str = "          "

        # Add the lines assembled machine code
        display_str += (byte_str + SPACES[:(10 - len(byte_str))] + "  ")

        # Add the label name - or spaces in its place
        display_str += (line_parts[0] + SPACES[:(label_len - len(line_parts[0]))] + "   ")

        # Add the op
        op_str = line_parts[1]
        if show_upper == 1:
            op_str = op_str.upper()
        elif show_upper == 2:
            op_str = op_str.lower()
        display_str += (op_str + SPACES[:(5 - len(line_parts[1]))] + "    ")

        # Add the operand
        if len(line_parts) > 2: display_str += line_parts[2]

        # Add the comment, if there is one
        if len(line_parts) > 3: display_str += (SPACES[:(55 - len(display_str))] + line_parts[3])

        # And output the line
        print(display_str)
    return True


def poke(address, value):
    '''
    Add new byte values to the machine code storage.

    Args:
        address (int): A 16-bit address in the store.
        value   (int): An 8-bit value to add to the store.
    '''
    if address - start_address > len(code) - 1:
        end_address = address - start_address - len(code)
        if end_address > 1:
            # 'address' is well beyond the end of the list, so insert
            # padding values in the form of a 6809 NOP opcode
            for _ in range(0, end_address - 1): code.append(0x12)
        # Poke the provided value after the padding
        code.append(value)
    elif not code:
        # Poke in the first item
        code.append(value)
    else:
        # Replace an existing item
        code[address - start_address] = value


def error_message(err_code, err_line):
    '''
    Display an error message.

    Args:
        err_code (int): The error type.
        err_line (int): The program on which the error occurred.
    '''

    if 0 < err_code < len(ERRORS):
        # Show standard message
        print("Error on line " + str(err_line + 1) + ": " + ERRORS[str(err_code)])
    else:
        # Show non-standard error code
        print("Error on line " + str(err_line + 1) + ": " + str(err_code))


def show_verbose(message):
    '''
    Display a message if verbose mode is enabled.

    Args:
        messsage (str): The text to print.
    '''

    if verbose is True: print(message)


def disassemble_file(file_path):
    '''
    Disassemble the specified .6809 file.

    Args:
        file_path (str): The path to the .6809 file.
    '''

    file_data = None
    if os.path.exists(file_path) is True:
        with open(file_path, "r") as file: file_data = file.read()
    else:
        print("[ERROR] File " + file_path + " does not exist, skipping")

    if file_data is not None:
        # Prep the disassembly
        data = json.loads(file_data)
        code = data["code"]
        address = data["address"]
        post_op_bytes = 0
        opnd = 0
        special_opnd = 0
        pre_op_byte = 0
        index_code = 0
        address_mode = ADDR_MODE_NONE
        line_str = ""
        byte_str = ""
        index_str = ""
        got_op = False

        print("Address   Operation       Bytes")
        print("-------------------------------")
        # Run through the machine code byte by byte
        for unit in code:
            # Get the current byte
            next_byte = ord(unit)
            byte_str += "{0:02X}".format(next_byte)

            # Combine the current byte with the previous one, if that
            # was 0x10 or 0x11 (ie. extended ISA)
            if pre_op_byte != 0:
                next_byte = (pre_op_byte << 8) + next_byte
                pre_op_byte = 0

            found = False
            the_op = ""

            if got_op is False:
                # Look for an op first
                if next_byte in (0x10, 0x11):
                    # Extended ISA indicator found, so hold for combination
                    # with the next loaded byte of code
                    pre_op_byte = next_byte
                    continue

                # Run through the main ISA to find the op
                for i in range(0, len(ISA), 6):
                    # Run through each op's possible op codes to find a match
                    for j in range(i + 1, i + 6):
                        if ISA[j] == next_byte:
                            # Got it
                            the_op = ISA[i]
                            # Value of 'k' indicates which addressing mode we have
                            address_mode = j - i
                            found = True
                            break
                    if found is True:
                        break

                if found is False:
                    # Didn't match the byte in the main ISA, so check for a branch op
                    for i in range(0, len(BSA), 3):
                        # Run through each op's possible op codes to find a match
                        for j in range(i + 1, i + 3):
                            if BSA[j] == next_byte:
                                # Got it
                                the_op = BSA[i]
                                # Correct the name of an extended branch op
                                # Add 10 to 'address_mode' to indicate branching
                                if j - i == 2: the_op = "L" + the_op
                                address_mode = j - i + 10
                                found = True
                                break
                        if found is True:
                            break

                # If we still haven't matched the op, print a warning and bail
                if found is False:
                    print("Bad Op: " + "{0:02X}".format(next_byte))
                    return

                # Set the initial part of the output line
                line_str = "0x{0:04X}".format(address) + "    " + the_op + "   "

                # Add a space for three-character opcodes
                if len(the_op) == 3: line_str += " "

                # Gather the operand bytes (if any) according to addressing mode
                if address_mode == ADDR_MODE_INHERENT:
                    # There's no operand with inherent addressing, so just dump the line
                    print(line_str + set_spacer(line_str) + byte_str)
                    address += 1
                    byte_str = ""
                elif address_mode == ADDR_MODE_IMMEDIATE:
                    # Immediate addressing
                    got_op = True
                    post_op_bytes = 1
                    address += 1

                    # Does the immediate postbyte have a special value?
                    # It will for PSH/PUL and TFR/EXG ops
                    if the_op[:1] == "P":
                        special_opnd = 1 if the_op[-1:] == "S" else 2
                    elif the_op in ("TFR", "EXG"):
                        special_opnd = 3
                    else:
                        # Set the number of operand bytes to gather to the byte-size of the
                        # named register (eg. two bytes for 16-bit registers
                        if the_op[-1:] in ("X", "Y", "D", "S", "U", "C"): post_op_bytes = 2

                        # Add the # symbol it indicate addressing type
                        line_str += "#"
                elif address_mode in (ADDR_MODE_DIRECT, ADDR_MODE_INDEXED, ADDR_MODE_EXTENDED):
                    # Indexed, Direct and Extended addressing
                    got_op = True
                    post_op_bytes = 1
                    address += 1
                    if address_mode == ADDR_MODE_EXTENDED: post_op_bytes += 1
                    if address_mode == ADDR_MODE_DIRECT: line_str += ">"
                elif address_mode > 10:
                    # Handle branch operation offset bytes
                    got_op = True
                    post_op_bytes = 2 if address_mode - 10 == BRANCH_MODE_LONG else 1
                    address += 1
            else:
                # We are handling the operand bytes having found the op
                # Check for the branching operations (short then long) first
                if address_mode - 10 == BRANCH_MODE_SHORT:
                    # 'next_byte' is an 8-bit branch offset
                    target = 0
                    if next_byte & 0x80 == 0x80:
                        # Sign bit set
                        target = address + 1 - (255 - next_byte)
                    else:
                        target = address + 1 + next_byte
                    line_str += "${0:04X}".format(target)
                elif address_mode - 10 == BRANCH_MODE_LONG:
                    # 'next_byte' is part of a 16-bit branch offset
                    if post_op_bytes > 0: opnd += (next_byte << (8 * (post_op_bytes - 1)))
                    if post_op_bytes == 1:
                        target = 0
                        if opnd & 0x8000 == 0x8000:
                            # Sign bit set
                            target = address + 1 - (65535 - opnd)
                        else:
                            target = address + 1 + opnd
                        line_str += "${0:04X}".format(target)
                elif address_mode == ADDR_MODE_IMMEDIATE and special_opnd > 0:
                    # See above for the meanings of 'special_opnd'
                    if special_opnd == 1:
                        line_str += get_puls_pshs_regs(next_byte)
                    elif special_opnd == 2:
                        line_str += get_pulu_pshu_regs(next_byte)
                    else:
                        line_str += get_tfr_exg_regs(next_byte)
                    special_opnd = 0
                elif address_mode == ADDR_MODE_INDEXED:
                    # 'index_code' is set according to the first post-op byte
                    if index_code == 0:
                        # Check for Indirect Indexed addressing
                        is_indirect = False
                        if next_byte & 0x10 == 0x10 and next_byte > 0x80: is_indirect = True

                        # Get the named register from the first post-op byte (bits 5 & 6)
                        reg = get_indexed_reg(next_byte)

                        # Get the operation code from the first post-op byte (bits 0-4)
                        code = next_byte & 0x0F
                        if next_byte < 0x80:
                            # Pull the 5-bit offset out of the post-op byte (bits 0-4)
                            index_str = "${0:02X}".format(code) + "," + reg
                        elif next_byte == 0x9F:
                            # Extended indirect
                            post_op_bytes = 2
                            index_code = 3
                        else:
                            if code == 0x04: index_str = "," + reg
                            if code in (0x08, 0x09):
                                # 8-, 16-bit offset from reg
                                index_str = "," + reg
                                post_op_bytes += (code - 0x07)
                                index_code = code - 0x07
                            if code == 0x06: index_str = "A," + reg
                            if code == 0x05: index_str = "B," + reg
                            if code == 0x0B: index_str = "D," + reg
                            if code == 0x00: index_str = "," + reg + "+"
                            if code == 0x01: index_str = "," + reg + "++"
                            if code == 0x02: index_str = ",-" + reg
                            if code == 0x03: index_str = ",--" + reg
                            if code in (0x0C, 0x0D):
                                # Constant offset From PC
                                index_str = ",PC"
                                post_op_bytes += (code - 0x0B)
                                index_code = code - 0x0B
                        # Wrap the operand string in brackets to indicate indirection
                        if is_indirect is True: index_str = "(" + index_str + ")"
                    else:
                        # Collect the extra byte(s) when 'index_code' is 1 or 2
                        if post_op_bytes > 0: opnd += (next_byte << (8 * (post_op_bytes - 1)))
                        if post_op_bytes == 1:
                            if index_code < 3:
                                format_str = "${0:0" + str(index_code * 2) + "X}"
                                index_str = format_str.format(opnd) + index_str
                            else:
                                index_str = "${0:04X}".format(opnd)
                            if is_indirect is True: index_str = "(" + index_str + ")"
                else:
                    # Pick up any other mode (including plain immediate addressing) and output a value
                    if post_op_bytes > 0: opnd += (next_byte << (8 * (post_op_bytes - 1)))
                    line_str += "{0:02X}".format(next_byte)

                # Decrement the operand bytes counter,
                # and increase the current memory address
                post_op_bytes -= 1
                address += 1

                if post_op_bytes == 0:
                    # We've got all the operand bytes we need, so output the line
                    # and zero key variables
                    line_str += index_str
                    space_str = set_spacer(line_str)
                    print(line_str + space_str + byte_str)
                    got_op = False
                    index_code = 0
                    opnd = 0
                    byte_str = ""
                    index_str = ""


def set_spacer(spaces):
    '''
    Determing the number of spaces to pad a printed line.

    Args:
        spaces (int): The length of the unpadded line.

    Returns:
        str: A string of spaces to pad the line.
    '''

    num = 26 - len(spaces)
    # If the line is too long, just return a couple of spaces
    if num < 1: return "  "
    return SPACES[:num]


def get_indexed_reg(byte_value):
    '''
    Convert a post-op byte value into a register name.

    Args:
        byte_value (int): The post-op byte value.

    Returns:
        str: The indicated register.
    '''

    byte_value = (byte_value & 0x60) >> 5
    regs = ("X", "Y", "U", "S")
    if byte_value < 4: return regs[byte_value]
    return "N/A"


def get_tfr_exg_regs(byte_value):
    '''
    Generic TFR/EXG operand string generator, converting a post-op byte value
    into disassembled output, eg. "A,B".

    Args:
        byte_value (int): The post-op byte value.

    Returns:
        str: The register string.
    '''

    reg_list = ("D", "X", "Y", "U", "S", "PC", "A", "B", "CC", "DP")
    from_nibble = (byte_value & 0xF0) >> 4
    to_nibble = byte_value & 0x0F
    from_str = reg_list[from_nibble - 2] if from_nibble > 5 else reg_list[from_nibble]
    to_str = reg_list[to_nibble - 2] if to_nibble > 5 else reg_list[to_nibble]
    return from_str + "," + to_str


def get_puls_pshs_regs(byte_value):
    '''
    Pass on the correct register lists for PSHS or PULS.

    Args:
        byte_value (int): The post-op byte value.

    Returns:
        str: The list of registers referenced in the operand.
    '''

    return get_pul_psh_regs(byte_value, ("CC", "A", "B", "DP", "X", "Y", "U", "PC"))


def get_pulu_pshu_regs(byte_value):
    '''
    Pass on the correct register lists for PSHU or PULU.

    Args:
        byte_value (int): The post-op byte value..

    Returns:
        str: The list of registers referenced in the operand.
    '''

    return get_pul_psh_regs(byte_value, ("CC", "A", "B", "DP", "X", "Y", "S", "PC"))


def get_pul_psh_regs(byte_value, reg_tuple):
    '''
    Generic PUL/PSH operand string generator.

    Args:
        byte_value (int):  The post-op byte value.
        reg_list   (list): Names of possible registers.

    Returns:
        str: The list of registers referenced in the operand.
    '''

    output = ""
    for i in range(0, 8):
        if byte_value & (2 ** i) > 0:
            # Bit is set, so add the register to the output string, 'os'
            output += (reg_tuple[i] + ",")
    # Remove the final comma
    if output: output = output[0:len(output) - 1]

    # Return the output string, eg. "CC,A,X,Y,PC"
    return output


def show_help():
    '''
    Display Spasm's help information.
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


def write_file(file_path=None):
    '''
    Write the assembled bytes, if any, to a .6809 file.

    Args:
        file_path (str): The path of the output file.
    '''

    if file_path:
        # Build the dictionary and convert to JSON
        byte_str = ""
        for a_byte in code: byte_str += chr(a_byte)
        the_op = {"address": start_address, "code": byte_str}
        json_op = json.dumps(the_op, ensure_ascii=False)

        # Write out the file
        with open(file_path, "w") as file: file.write(json_op)
        print("File " + file_path + " written")


def get_files():
    '''
    Determine all the '.asm' and '.6809' files in the script's directory.
    '''

    current_dir = os.getcwd()
    files = [file for file in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, file))]

    # Count the number of .asm and .6809 files
    asm_files = []
    dis_files = []

    for file in files:
        _, file_ext = os.path.splitext(file)
        if file_ext == ".asm": asm_files.append(file)
        if file_ext == ".6809": dis_files.append(file)

    asm_count = len(asm_files)
    if asm_count == 1:
        show_verbose("Processing 1 .asm file in " + current_dir)
    elif asm_count > 1:
        show_verbose("Processing " + str(asm_count) + " .asm files in " + current_dir)
    else:
        show_verbose("No suitable .asm files found in " + current_dir)

    dis_count = len(dis_files)
    if dis_count == 1:
        show_verbose("Processing 1 .6809 file in " + current_dir)
    elif dis_count > 1:
        print("Processing " + str(dis_count) + " .6809 files in " + current_dir)
    else:
        show_verbose("No suitable .6809 files found in " + current_dir)

    handle_files(asm_files)
    handle_files(dis_files)


def handle_files(the_files=None):
    '''
    Pass on all supplied '.asm' files on for assembly, '.6809' files for disassembly.

    Args:
        the_files (list): The .asm or .6809 files.
    '''

    if the_files:
        for file in the_files:
            if file[-1:] == "m": assemble_file(file)
            if file[-1:] == "9": disassemble_file(file)


if __name__ == '__main__':

    # Do we have any arguments?
    if len(sys.argv) > 1:
        files_flag = False
        arg_flag = False
        files = []
        for index, item in enumerate(sys.argv):
            if arg_flag is True:
                arg_flag = False
            elif item in ("-v", "--verbose"):
                # Handle the -v / --verbose switch
                verbose = True
            elif item in ("-q", "--quiet"):
                # Handle the -q / --quiet switch
                verbose = False
            elif item in ("-u", "--upper"):
                # Handle the -u / --upper switch
                show_upper = 1
            elif item in ("-l", "--lower"):
                # Handle the -l / --lower switch
                show_upper = 2
            elif item in ("-s", "--startaddress"):
                # Handle the -s / --startaddress switch
                if index + 1 >= len(sys.argv):
                    print("[ERROR] -s / --startaddress must be followed by an address")
                    sys.exit(1)
                address = sys.argv[index + 1]
                base = 10
                if address[0] == "$": address = "0x" + address[1:]
                if address[:2] == "0x": base = 16
                try:
                    start_address = int(address, base)
                except ValueError:
                    print("[ERROR] -s / --start_address must be followed by a valid address")
                    sys.exit(1)
                show_verbose("Code start address set to 0x{0:04X}".format(start_address))
                arg_flag = True
            elif item in ("-h", "--help"):
                # Handle the -h / --help switch
                show_help()
                sys.exit(0)
            elif item in ("-o", "--outfile"):
                if index + 1 >= len(sys.argv) or sys.argv[index + 1][0] == "-":
                    out_file = "*"
                else:
                    out_file = sys.argv[index + 1]
                    _, file_ext = os.path.splitext(out_file)
                    if file_ext != ".6809":
                        print("[ERROR] -o / --outfile must specify a .6089 file")
                        sys.exit(1)
                # Make sure 'outfile' is a .6809 file
                parts = out_file.split(".")
                if parts == 1: out_file += ".6809"
                arg_flag = True
            else:
                if item[0] == "-":
                    print("[ERROR] unknown option: " + item)
                    sys.exit(1)
                elif index != 0 and arg_flag is False:
                    # Handle any included .asm files
                    _, file_ext = os.path.splitext(item)
                    if file_ext in (".asm", ".6809"):
                        files.append(item)
                    else:
                        print("[ERROR] File " + item + " is not a .asm or .6809 file")
        if files:
            # Process any named files
            handle_files(files)
    else:
        # By default get all the .asm files in the working directory
        get_files()

    sys.exit(0)
