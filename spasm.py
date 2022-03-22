#!/usr/bin/env python3

'''
'SPASM' -- Smittytone's Primary 6809 ASeMmbler

Version:
    1.3.0

Copyright:
    2021, Tony Smith (@smittytone)

License:
    MIT (terms attached to this repo)
'''

##########################################################################
# Program library imports                                                #
##########################################################################

import os
import sys
import json
from constants import *
from classes import *


##########################################################################
# Functions                                                              #
##########################################################################

'''
    Assemble a single '.asm' file using a two-pass process to identify
    labels and pseudo-ops, etc.

    Args:
        file_path (str): The path to a .asm file.
'''
def assemble_file(file_path):
    # Initialize the storage arrays
    app_state.labels = []
    app_state.code = []
    lines = []
    # Check that the passed file is available to process
    if not os.path.exists(file_path):
        print("[ERROR] File " + file_path + " does not exist, skipping")
        return

    with open(file_path, "r") as file: lines = list(file)
    show_verbose("Processing file: " + os.path.abspath(file_path))

    # FROM 1.2.0: Create an initial code chunk and add it to the array
    chunk = {}
    chunk["address"] = app_state.start_address
    chunk["code"] = bytearray()
    app_state.code.append(chunk)

    for asm_pass in range(1, 3):
        # Start a pass
        app_state.pass_count = asm_pass
        show_verbose("Assembly pass #" + str(asm_pass))

        # Set the current code chunk - we will load further chunks, if any,
        # as ORG directives are encountered in the code
        app_state.chunk = app_state.code[0]
        app_state.prog_count = app_state.chunk["address"]

        # Parse the lines one at a time
        for i in range(0, len(lines)):
            current_line = lines[i]

            # Parse the current line
            if parse_line(current_line, i) is False:
                # Error in processing: print post
                print("Processing error in line " + str(i + 1) + " -- halting assembly")
                print(">>> " + current_line)
                return

    # Post-assembly, dump the machine code, provided there was no error
    if app_state.verbose is True:
        print("\nMachine Code Dump")
        print("----------------------------------------")
        for chunk in app_state.code:
            code_bytes = chunk["code"]
            line_address = chunk["address"]
            # Add the initial address
            for i in range(0, len(code_bytes), 8):
                display_str = "0x{0:04X}".format(line_address) + "  "
                for j in range(0, 8):
                    if i + j < len(code_bytes):
                        # Add the bytes, one at a time, separated by whitespace
                        display_str += "  {0:02X}".format(code_bytes[i + j])
                        line_address += 1
                print(display_str)
            # Spacer between chunks
            print(" ")

    # Write out the machine code file
    if app_state.out_file is not None:
        if app_state.out_file == "*":
            app_state.out_file, _ = os.path.splitext(file_path)
            app_state.out_file += ".rom"
        write_file(app_state.out_file)

    # Temp section for testing
    items = 0
    display_str = ""
    for chunk in app_state.code:
        code_bytes = chunk["code"]
        line_address = chunk["address"]
        # Add the initial address
        for i in range(0, len(code_bytes), 8):
            for j in range(0, 8):
                if i + j < len(code_bytes):
                    display_str += "0x{0:02X},".format(code_bytes[i + j])
                    items += 1
        print(items, display_str)


'''
Process a single line of assembly, on a per-pass basis.

Each line is segmented by space characters, and we remove extra spaces from all
line parts other than comments. You cannot have a space set using the Ascii indicator, '

Args:
    line        (list): A line of program as a raw string.
    line_number (int):  The current line (starts at 0).

Returns:
    bool: False if an error occurred, or True.
'''
def parse_line(line, line_number):
    # Split the line at the line terminator to remove the carriage return
    line = line.splitlines()[0]

    # Check for comment lines
    line, comment = find_comments(line, ";", " ")
    line, comment = find_comments(line, "*", comment)
    comment_start = 1 if comment != " " else -1

    # FROM 1.2.0: Check for quoted strings (only double-quotes for now)
    quote = ""
    quote_start = line.find('"')
    if quote_start != -1:
        line_parts = line.split('"', 1)
        quote = line_parts[len(line_parts) - 1]
        line = line_parts[0]
        line_parts = quote.split('"', 1)
        quote = '"' + line_parts[0] + '"'

    # Segment the remaining line by spaces
    line_parts = line.split(" ")

    # Remove empty entries (ie. instances of multiple spaces)
    j = 0
    while True:
        if j == len(line_parts): break
        if not line_parts[j]:
            line_parts.pop(j)
        else:
            j += 1

    # Add back the quote, if any
    if quote: line_parts.append(quote)

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
        if comment_start != -1 and app_state.pass_count == 2:
            # We have a comment, so just dump it out on pass 2
            line_data.comment_start = comment_start
            write_code([comment, " ", " ", " "], line_data)
            # And return to go and process the next line
            return True
        line_parts = [" ", " "]

    # Process the line's components
    # Check for an initial label
    label = line_parts[0]
    #if label[0] == "@":
    if label != " " and check_reserved(label):
        # Found a label - store it if we need to
        got_label = index_of_label(label)
        if got_label != -1:
            # The label has already been seen during assembly
            label = app_state.labels[got_label]
            if app_state.pass_count == 1:
                if label["addr"] != "!!!!":
                    error_message(2, line_number) # Duplicate label
                    return False
                # Set the label address
                label["addr"] = app_state.prog_count
                # Output the label valuation
                show_verbose("Label " + label["name"] + " set to 0x" +
                             to_hex(app_state.prog_count, 4) + " (line " + str(line_number + 1) + ")")
        else:
            # Record the newly found label
            app_state.labels.append({"name": label, "addr": app_state.prog_count})
            if app_state.pass_count == 1:
                show_verbose("Label " + label + " found and set to 0x" + to_hex(app_state.prog_count, 4) +
                             " (line " + str(line_number + 1) + ")")
    else:
        # Not a label, so insert a blank - ie. ensure the op will be in lineParts[1]
        line_parts.insert(0, " ")

    # If there is no third field, add an empty one
    if len(line_parts) == 2: line_parts.append(" ")

    # Put the comment string, if there is one, into the comment field, lineParts[3]
    line_parts.append(comment if comment else " ")

    # Check the opcode
    if line_parts[1] != " ":
        result = decode_op(line_parts[1], line_data)
        if result is False: return False

    # Calculate the operand
    result = decode_opnd(line_parts[2], line_data)
    if result == "ERROR": return False

    # Handle a pseudo-op if we have one, or write out the code
    if line_data.pseudo_op_type > 0:
        result = process_pseudo_op(line_parts, line_data)
    else:
        result = write_code(line_parts, line_data)

    return result


def find_comments(line, comment_symbol, comment):
    l = line.find(comment_symbol)
    if l != -1:
        # Found a comment line so re-position it
        comment = comment_symbol + line[l + 1:]
        line = line[:l]
    return (line, comment)


'''
Check that a possible label is not a reserved word.

Args:
    laber (str): The possible label.

Returns:
    True if the label is not a reserved word, or False.
'''
def check_reserved(label):
    label = label.upper()
    if label in POPS:
        return False
    if label in ISA:
        return False
    if label in BSA:
        return False
    if label[0] == "L":
        if label[1:] in BSA:
            return False
    return True

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
def decode_op(an_op, line):

    # Make mnemonic upper case
    an_op = an_op.upper()

    # Check for pseudo-ops
    if an_op in POPS:
        line.oper = [an_op]
        line.pseudo_op_type = POPS.index(an_op) + 1
        return True

    # Check for regular instructions
    if an_op in ISA:
        op_index = ISA.index(an_op)
        for i in range(op_index, op_index + 6): line.oper.append(ISA[i])
        return True

    # Check for branch instructions
    if an_op[0] == "L":
        # Handle long branch instructions
        line.branch_op_type = BRANCH_MODE_LONG
        an_op = an_op[1:]
    else:
        line.branch_op_type = BRANCH_MODE_SHORT

    if an_op in BSA:
        op_index = BSA.index(an_op)
        for i in range(op_index, op_index + 3): line.oper.append(BSA[i])
        return True

    # No instruction found: that's a Bad Op error
    error_message(1, line.line_number)
    return False


'''
This function decodes the operand.

Args:
    an_opnd (str): The extracted operand.
    line  (LineData): An object representing the decoded line.

Returns
    int: the operand value, or "ERROR" if the operand value could not be determined
'''
def decode_opnd(an_opnd, line):
    opnd_str = ""
    op_name = ""
    opnd_value = 0
    line.op_type = ADDR_MODE_NONE
    err = "ERROR"

    if len(line.oper) > 1: op_name = line.oper[0]
    if op_name in ("EXG", "TFR"):
        # Register swap operation to calculate the special operand value
        # by looking at the named registers separated by a comma
        opnd_parts = an_opnd.split(',')
        if len(opnd_parts) != 2 or opnd_parts[0] == opnd_parts[1]:
            error_message(7, line.line_number) # Bad operand
            return err

        source = get_reg_value(opnd_parts[0])
        if not source:
            error_message(7, line.line_number) # Bad operand
            return err

        dest = get_reg_value(opnd_parts[1])
        if not dest:
            error_message(7, line.line_number) # Bad operand
            return err

        # Check that a and b's bit lengths match: can't copy a 16-bit into an 8-bit
        source_size = int(source, 16)
        dest_size = int(dest, 16)
        if (source_size > 5 and dest_size < 8) or (source_size < 8 and dest_size > 5):
            error_message(7, line.line_number) # Bad operand
            return err
        opnd_str = "0x" + source + dest
        line.op_type = ADDR_MODE_IMMEDIATE_SPECIAL
    elif op_name[0:3] in ("PUL", "PSH"):
        # Push or pull operation to calculate the special operand value
        # by looking at all the named registers
        post_byte = 0
        if not an_opnd:
            error_message(8, line.line_number) # Bad operand
            return err
        opnd_parts = an_opnd.split(',')
        if len(opnd_parts) == 1:
            # A single register
            if an_opnd == op_name[3]:
                # Can't PUL or PSH a register to itself, eg. PULU U doesn't make sense
                error_message(8, line.line_number) # Bad operand
                return err
            post_byte = get_pull_reg_value(an_opnd)
            if post_byte == -1:
                error_message(8, line.line_number) # Bad operand
                return err
        else:
            for part in opnd_parts:
                reg_val = get_pull_reg_value(part)
                if reg_val == -1:
                    error_message(8, line.line_number) # Bad operand
                    return err
                post_byte |= reg_val
        opnd_str = str(post_byte)
        line.op_type = ADDR_MODE_IMMEDIATE_SPECIAL
    else:
        # Calculate the operand for all other instructions
        if an_opnd == " ": an_opnd = ""
        if an_opnd:
            quote_start = False
            # Operand string is not empty (it could be, eg. SWI) so process it char by char
            for op_char in an_opnd:
                if op_char == "<":
                    # Direct addressing
                    line.op_type = ADDR_MODE_DIRECT
                    line.expects_8b_opnd = True
                    opnd_str = ""
                elif op_char == "#":
                    # Immediate addressing
                    line.op_type = ADDR_MODE_IMMEDIATE
                    reg = line.oper[0]
                    if reg[-1:] in ("A", "B") or reg[-2:] == "CC": line.expects_8b_opnd = True
                    opnd_str = ""
                else:
                    # Convert value internally as hex
                    if op_char == "$": op_char = "0x"
                    # Operand could use indexed addressing or be a FCB/FDB value list
                    if op_char in (",", "["):
                        if line.pseudo_op_type == 0:
                            # It's an indexed addressing operand, so decode it
                            opnd_str = decode_indexed(an_opnd, line)
                            if opnd_str == "":
                                error_message(5, line.line_number) # Bad operand
                                return err
                            break

                    # FROM 1.2.0: Handle quotes
                    if op_char == '"' and quote_start is False: quote_start = True
                    # Remove un-quoted spaces and re-assemble string
                    if op_char not in (' ', '"'): opnd_str += op_char
                    if op_char == " " and quote_start is True: opnd_str += op_char

    #if opnd_str and opnd_str[0] == "@":
    if opnd_str and opnd_str[0].isalpha():
        # Operand is a label
        label_index = index_of_label(opnd_str)
        if label_index == -1:
            # Label has not been seen yet
            if app_state.pass_count == 2:
                # Any new label seen on pass 2 indicates an error
                error_message(3, line.line_number) # No label defined
                return err

            # Make a new label
            app_state.labels.append({"name": opnd_str, "addr": "!!!!"})
            show_verbose("Label " + opnd_str + " found (line " + str(line.line_number + 1) + ")")
            opnd_str = "!!!!"
        else:
            label = app_state.labels[label_index]
            opnd_value = label["addr"]
            opnd_str = str(opnd_value)

    if not opnd_str:
        # No operand found, so this must be an Inherent Addressing op
        line.op_type = ADDR_MODE_INHERENT
    else:
        if line.pseudo_op_type in (3, 4):
            # FCB/FDB - check for value lists
            opnd_parts = opnd_str.split(",")
            if len(opnd_parts) > 1:
                # We have a list of values. Convert them to hex bytes for internal processing
                byte_string = ""
                byte_count = 2 if line.pseudo_op_type == 3 else 4
                for part in opnd_parts: byte_string += to_hex(get_int_value(part), byte_count)
                # Preserve the byte string for later then bail
                line.pseudo_op_value = byte_string
                opnd_value = 0
            else:
                # Not a list, so just get the value of the operand
                opnd_value = get_int_value(opnd_str)
        elif line.pseudo_op_type == 8:
            # FCC - get a string
            line.pseudo_op_value = opnd_str
            opnd_value = 0
        elif line.is_indirect is False:
            # Get the value for any operand
            size = 16
            if line.expects_8b_opnd is True and line.op_type == ADDR_MODE_IMMEDIATE: size = 8
            opnd_value = get_int_value(opnd_str, size)

        if line.branch_op_type > 0:
            # Process a branch value
            if app_state.pass_count == 1:
                # Don't calculate the branch offset on the first pass
                opnd_value = 0
            else:
                if line.branch_op_type == BRANCH_MODE_SHORT:
                    offset = 2 # PC + 1 byte of op + 1 byte of delta
                    line.index_address = opnd_value - (app_state.prog_count + 2)
                    if line.index_address < -128 or line.index_address > 127:
                        error_message(4, line.line_number) # Bad branch type: out of range offset
                        return err
                else:
                    offset = 3 # PC + 1 byte of op + 2 bytes of delta
                    line.index_address = opnd_value - (app_state.prog_count + offset)

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

    # ADDED 1.2.0: Check that ops expecting an 8-bit operand get one
    if line.expects_8b_opnd is True and line.op_type in (ADDR_MODE_IMMEDIATE, ADDR_MODE_DIRECT):
        # We do expect an 8-bit operand
        if opnd_value < -128 or opnd_value > 255:
            # But the value is out of range, so report an error
            error_message(10, line.line_number) # Bad branch type: out of range operand
            return err
    line.opnd = opnd_value
    return opnd_value


'''
Process assembler pseudo-ops, ie. directives with specific assembler-level functionality.

Args:
    line_parts (list):       The program components of the current line (see 'parse_line()').
    line       (DecodeData): The decoded line data.

Returns:
    bool: False if an error occurred, or True.
'''
def process_pseudo_op(line_parts, line):
    result = False
    opnd_value = line.opnd
    label_name = line_parts[0]
    if label_name == " ": label_name = ""
    label_idx = index_of_label(label_name)

    if line.pseudo_op_type == 1:
        # EQU: assign the operand value to the label declared immediately
        # before the EQU op. MUST have a label
        if label_idx == -1: return False
        if app_state.pass_count == 1:
            label = app_state.labels[label_idx]
            label["addr"] = opnd_value
            show_verbose("Label " + label_name + " set to 0x" +
                         to_hex(opnd_value) + " (line " + str(line.line_number + 1) + ")")
        result = write_code(line_parts, line)

    if line.pseudo_op_type in (2, 9):
        # RMB: Reserve the next 'opnd_value' bytes and set the label to the current
        # value of the programme counter
        # ZMB: Same as RMB, but zero the bytes
        if label_idx != -1:
            label = app_state.labels[label_idx]
            label["addr"] = app_state.prog_count
        if app_state.pass_count == 1:
            show_verbose(str(opnd_value) + " bytes reserved at address 0x" +
                         to_hex(app_state.prog_count, 4) + " (line " + str(line.line_number + 1) + ")")
        if line.pseudo_op_type == 9:
            for i in range(app_state.prog_count, app_state.prog_count + opnd_value):
                poke(i, 0x00)
        result = write_code(line_parts, line)
        app_state.prog_count += opnd_value

    if line.pseudo_op_type == 3:
        # FCB: Pokes 'opnd_value' (1 byte) or 'pseudo_op_value' (x bytes) at the
        # current byte. Sets a label, if present, to the address of the first byte
        if label_idx != -1:
            label = app_state.labels[label_idx]
            label["addr"] = app_state.prog_count
        if line.pseudo_op_value:
            # Multiple bytes to poke in, in the form of a hex string
            count = 0
            for i in range(0, len(line.pseudo_op_value), 2):
                byte = line.pseudo_op_value[i:i+2]
                if i == 0:
                    line.opnd = int(byte, 16)
                    # Write out the sequence's first byte value
                    result = write_code(line_parts, line)
                elif app_state.pass_count == 2:
                    # Write out the sequence's subsequent bytes
                    print("          0x" + to_hex(app_state.prog_count, 4) + "    " + byte)
                poke(app_state.prog_count, int(byte, 16))
                app_state.prog_count += 1
                count += 1
            if app_state.pass_count == 1:
                show_verbose(str(count) + " bytes written at 0x" +
                             to_hex(app_state.prog_count - count, 4) +
                             " (line " + str(line.line_number + 1) + ")")
        else:
            # Just a single byte to drop in
            opnd_value = opnd_value & 0xFF
            poke(app_state.prog_count, opnd_value)
            if app_state.pass_count == 1:
                show_verbose("The byte at 0x" + to_hex(app_state.prog_count, 4) + " set to 0x" +
                             to_hex(opnd_value) + " (line " + str(line.line_number + 1) + ")")
            result = write_code(line_parts, line)
            app_state.prog_count += 1

    if line.pseudo_op_type == 4:
        # FDB: Pokes the MSB of 'opnd_value' into the current byte and the LSB into
        # the next byte. Sets the label to the address of the first byte.
        if label_idx != -1:
            label = app_state.labels[label_idx]
            label["addr"] = app_state.prog_count
        if line.pseudo_op_value:
            # Multiple bytes to poke in, in the form of a hex string
            byte_count = 0
            for i in range(0, len(line.pseudo_op_value), 4):
                byte = line.pseudo_op_value[i:i+4]
                byte_count = i
                if i == 0:
                    line.opnd = int(byte, 16)
                    result = write_code(line_parts, line)
                elif app_state.pass_count == 2:
                    print("          0x" + to_hex(app_state.prog_count, 4) + "    " + byte)
                poke(app_state.prog_count, (int(byte, 16) >> 8) & 0xFF)
                poke(app_state.prog_count + 1, int(byte, 16) & 0xFF)
                app_state.prog_count += 2
            if app_state.pass_count == 1:
                show_verbose(str(byte_count) + " bytes written at 0x" + to_hex(app_state.prog_count - byte_count, 4) +
                             " (line " + str(line.line_number + 1) + ")")
        else:
            # Just a single 16-bit value to drop in
            opnd_value = opnd_value & 0xFFFF
            if app_state.pass_count == 1:
                show_verbose("The two bytes at 0x" + to_hex(app_state.prog_count, 4) + " set to 0x" +
                             to_hex(opnd_value, 4) + " (line " + str(line.line_number + 1) + ")")
            result = write_code(line_parts, line)
            poke(app_state.prog_count, (opnd_value >> 8) & 0xFF)
            poke(app_state.prog_count + 1, opnd_value & 0xFF)
            app_state.prog_count += 2

    if line.pseudo_op_type == 5:
        # END: The end of the program. This is optional, and currently does nothing
        result = write_code(line_parts, line)

    if line.pseudo_op_type == 6:
        # ORG: set or reset the origin
        if app_state.pass_count == 1:
            show_verbose("Origin set to 0x" + to_hex(opnd_value, 4) + " (line " + str(line.line_number + 1) + ")")
            if app_state.prog_count != app_state.chunk["address"]:
                new_chunk = {}
                new_chunk["code"] = bytearray()
                new_chunk["address"] = 0xFFFF
                app_state.code.append(new_chunk)
            app_state.chunk["address"] = opnd_value
        app_state.chunk = chunk_from_address(opnd_value)
        app_state.prog_count = opnd_value
        result = write_code(line_parts, line)
        if label_name:
            label = app_state.labels[label_idx]
            label["addr"] = opnd_value
            if app_state.pass_count == 1:
                show_verbose("Label " + label["name"] + " set to 0x" +
                             to_hex(opnd_value, 4) + " (line " + str(line.line_number + 1) + ")")

    # TODO
    # Add SETDP

    if line.pseudo_op_type == 8:
        # FCC: Pokes in a string
        result = write_code(line_parts, line)
        for i in range(0, len(line.pseudo_op_value)):
            byte = line.pseudo_op_value[i:i+1]
            poke(app_state.prog_count, ord(byte))
            app_state.prog_count += 1

    return result


'''
Get a specific chunk from its address.

Args:
    an_address (int): The chunk address.

Returns:
    Chunk: The required chunk.
'''
def chunk_from_address(address):
    for chunk in app_state.code:
        if chunk["address"] == address: return chunk
    print("ERROR -- mis-addressed chunk")
    sys.exit(1)


'''
Decode the indexed addressing operand.

Args:
    opnd (str):        The extracted operand.
    line (DecodeData): The decoded line data.

Returns:
    str: The operand value as a string, or an empty string if there was an error.
'''
def decode_indexed(opnd, line):
    line.op_type = ADDR_MODE_INDEXED
    opnd_value = 0
    reg = 0
    byte_value = ADDRESSING_NONE
    is_extended = False
    index_parts = opnd.split(',')

    # Decode the left side of the operand
    left = index_parts[0]
    if left:
        if left[0] == "[":
            # Addressing mode is Indirect Indexed, eg. LDA (5,PC)
            line.is_indirect = True
            is_extended = True
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
            is_negative = False
            if left[0] == "-":
                left = left[1:]
                is_negative = True
            if left[0] == "$": left = "0x" + left[1:]
            if is_negative:
                left = "-" + left
            if left[0].isalpha(): #== "@":
                label_index = index_of_label(left)
                if label_index == -1:
                    if app_state.pass_count == 2:
                        error_message(3, line.line_number) # No label defined
                        return ""
                    app_state.labels.append({"name": left, "addr": "!!!!"})
                    if app_state.pass_count == 1: show_verbose("Label " + left + " found on line " + str(line.line_number + 1))
                    # Set byte value to 129 to make sure we allow a 16-bit max. space
                    byte_value = 129
                else:
                    label = app_state.labels[label_index]
                    byte_value = label["addr"]
            else:
                byte_value = get_int_value(left)
                if (byte_value < -32768 or byte_value > 32767):
                    return ""
            if byte_value > 127 or byte_value < -128:
                # 16-bit
                opnd_value += 0x89
                byte_value = get_int_value(left, 16, True)
            elif line.is_indirect is True or byte_value > 15 or byte_value < -16:
                # 8-bit
                opnd_value += 0x88
                byte_value = get_int_value(left, 8, True)
            elif byte_value == 0:
                # Trap a zero offset call
                opnd_value += + 0x84
                byte_value = ADDRESSING_NONE
            else:
                # 5 bit offset so retain only bits 0-5
                opnd_value = byte_value & 0x1F
                byte_value = ADDRESSING_NONE
    else:
        # Nothing left of the comma
        opnd_value = 0x84

    if is_extended is False:
        # Decode the right side of the operand
        right = index_parts[1].lstrip()
        # Remove right hand bracket (indirect) if present
        if right[-1] == "]": right = right[:-1]
        # Operand is of the 'n,PCR' type - just set bit 2
        if right[:2].upper() == "PC": opnd_value += 4
        if right[-1:] == "+":
            if right[-2:] == "++": # ',R++'
                opnd_value = 0x91 if line.is_indirect else 0x81
            else:
                # ',R+' is not allowed with indirection
                if line.is_indirect is True: return ""
                opnd_value = 0x80
            # Set the analysed string to the register
            right = right[0]
            # Ignore any prefix value
            byte_value = ADDRESSING_NONE
        if right[0] == "-":
            if right[1] == "-": # ',--R'
                opnd_value = 0x93 if line.is_indirect else 0x83
            else:
                # ',-R' is not allowed with indirection
                if line.is_indirect is True: return ""
                opnd_value = 0x82
            # Set the analysed string to the register
            right = right[-1]
            # Ignore any prefix value
            byte_value = ADDRESSING_NONE
        # Add in the register value (assume X, which equals 0 in the register coding)
        if right.upper() == "Y": reg = 0x20
        if right.upper() == "U": reg = 0x40
        if right.upper() == "S": reg = 0x60

    # Store the index data for later
    line.index_address = byte_value
    line.is_indexed = True
    line.is_indirect = False

    # Return the operand value as a string
    opnd_value += reg
    return str(opnd_value)


'''
Return the machine code for the specific register as used in TFR and EXG ops.

Args:
    reg (str): The register name.

Returns:
    str: Single-character hex string
'''
def get_reg_value(reg):
    reg = reg.upper()
    regs = ("D", "X", "Y", "U", "S", "PC", "A", "B", "CC", "DP")
    values = ("0", "1", "2", "3", "4", "5", "8", "9", "A", "B")
    if reg in regs: return values[regs.index(reg)]
    return ""


'''
Return the value for the specific register as used in PUL and PSH ops.

Args:
    reg (str): The register name.

Returns:
    int: The register value.
'''
def get_pull_reg_value(reg):
    reg = reg.upper()
    regs = ("CC", "A", "B", "D", "DP", "X", "Y", "S", "U", "PC")
    values = (1, 2, 4, 6, 8, 16, 32, 64, 64, 128)
    if reg in regs: return values[regs.index(reg)]
    return -1


'''
Convert a prefixed string value to an integer.

Args:
    constant_string (str): The known numeric string.
    size            (int): The number of bits in the value

Returns:
    int: A positive integer value.
'''
def get_int_value(constant_string, size=8, do_twos=False):
    value = 0
    is_negative = False
    if constant_string[0] == "-":
        constant_string = constant_string[1:]
        is_negative = True
    if constant_string == "!!!!":
        value = 0
    elif constant_string[:2] == "0x":
        # Hex value
        value = int(constant_string, 16)
    elif constant_string[0].isalpha():
        # A label value
        label = app_state.labels[index_of_label(constant_string)]
        value = label["addr"]
    elif constant_string[0] == "%":
        # Binary data
        value = decode_binary(constant_string[1:])
    elif constant_string[0] == "'":
        # Ascii data in the next character
        value = ord(constant_string[1])
    else:
        value = int(constant_string)

    if is_negative: value *= -1

    # FROM 1.2.0: Check for negative values - cast to 2's comp
    if value < 0 and do_twos is True:
        if value < -128 or size == 16:
            value += 32768
        else:
            value += 256
    return value


'''
Encode an integer to a 'str_len' length hex string.

Args:
    value   (int): The integer.
    length  (str): A string binary representation. Default: 2

Returns:
    str: The hex representation
'''
def to_hex(value, length=2):
    format_string = "{0:0" + str(length) + "X}"
    return format_string.format(value)


'''
Decode the supplied binary value (as a string, eg. '0010010') to an integer.

Args:
    binary_string (str): A string binary representation.

Returns:
    int: The integer value.
'''
def decode_binary(binary_string):
    value = 0
    for i in range(0, len(binary_string)):
        bit = len(binary_string) - i - 1
        if binary_string[bit] == "1": value += (2 ** i)
    return value


'''
See if we have already encountered 'label_name' in the listing.

Args:
    label_name (str): The name of the found label.

Returns:
    int: The index of the label in the list, or -1 if it isn't yet recorded.
'''
def index_of_label(label_name):
    if app_state.labels:
        for label in app_state.labels:
            if label["name"] == label_name:
                # Got a match so return the label's index in the list
                return app_state.labels.index(label)
    # Return -1 to indicate 'label_name' is not in the list
    return -1


'''
Write out the machine code and, on the second pass, print out the listing.

Args:
    line_parts (list):       The program components of the current line (see 'parse_line()').
    line       (DecodeData): The decoded line data.

Returns:
    bool: False in the instance of an error, otherwise True.
'''
def write_code(line_parts, line):
    byte_str = ""

    if len(line.oper) > 1:
        if line.branch_op_type > 0: line.op_type = line.branch_op_type

        # Get the machine code for the op
        op_value = line.oper[line.op_type - 10 if line.op_type > 10 else line.op_type]

        if op_value == -1:
            error_message(6, line.line_number) # Bad opcode
            return False

        # Poke in the opcode
        if op_value < 256:
            poke(app_state.prog_count, op_value)
            app_state.prog_count += 1
            if app_state.pass_count == 2: byte_str += to_hex(op_value)
        if op_value > 255:
            lsb = op_value & 0xFF
            msb = (op_value >> 8) & 0xFF
            poke(app_state.prog_count, msb)
            poke(app_state.prog_count + 1, lsb)
            app_state.prog_count += 2
            if app_state.pass_count == 2: byte_str += (to_hex(msb) + to_hex(lsb))

        # Set 'op-type' for output
        if line.branch_op_type == BRANCH_MODE_LONG: line.op_type = ADDR_MODE_EXTENDED
        if line.branch_op_type == BRANCH_MODE_SHORT: line.op_type = ADDR_MODE_DIRECT

        if line.op_type == ADDR_MODE_IMMEDIATE:
            # Immediate addressing - get last character of opcode
            an_op = line.oper[0]
            an_op = an_op[-1]
            if an_op in ("D", "X", "Y", "S", "U"): line.op_type = ADDR_MODE_EXTENDED
        if line.op_type == ADDR_MODE_IMMEDIATE_SPECIAL:
            # Immediate addressing: TFR/EXG OR PUL/PSH
            poke(app_state.prog_count, int(line.opnd))
            app_state.prog_count += 1
            if app_state.pass_count == 2: byte_str += to_hex(line.opnd)
        if line.op_type == ADDR_MODE_INHERENT:
            # Inherent addressing
            line.op_type = ADDR_MODE_NONE
        if line.is_indexed is True:
            poke(app_state.prog_count, line.opnd)
            if app_state.pass_count == 2: byte_str += to_hex(line.opnd)
            app_state.prog_count += 1
            if line.index_address != ADDRESSING_NONE:
                line.opnd = line.index_address
                # By this point, all values should be unsigned
                if line.opnd > 255:
                    # Do 16-bit address
                    line.op_type = ADDR_MODE_EXTENDED
                else:
                    # Do 8-bit address
                    line.op_type = ADDR_MODE_INDEXED
            else:
                line.op_type = ADDR_MODE_NONE
        if line.op_type > ADDR_MODE_NONE and line.op_type < ADDR_MODE_EXTENDED:
            # Immediate, direct and indexed addressing
            poke(app_state.prog_count, line.opnd)
            app_state.prog_count += 1
            if app_state.pass_count == 2: byte_str += to_hex(line.opnd)
        if line.op_type == ADDR_MODE_EXTENDED:
            # Extended addressing
            lsb = line.opnd & 0xFF
            msb = (line.opnd >> 8) & 0xFF
            poke(app_state.prog_count, msb)
            poke(app_state.prog_count + 1, lsb)
            app_state.prog_count += 2
            if app_state.pass_count == 2: byte_str += (to_hex(msb) + to_hex(lsb))

    if app_state.pass_count == 2 and app_state.verbose is True:
        # Display the line on pass 2
        # Determine the length of the longest label
        label_len = 5
        if app_state.labels:
            for label in app_state.labels:
                if label_len < len(label["name"]): label_len = len(label["name"])
        label_len = 9 - label_len if label_len < 5 else label_len + 4

        if line.line_number == 0:
            # Print the header on the first line
            display_str = "Line      Address   Bytes       Label" + set_spacer(label_len - 5) + "Op.      Data"
            print(display_str)
            print("-" * len(display_str))

        # Set the line number
        display_str = str(line.line_number + 1)
        display_str = "0" * (6 - len(display_str)) + display_str + "    "

        # Handle comment-only lines
        if line.comment_start != -1:
            print(display_str + set_spacer(10) + line_parts[0])
            return True

        # Add the 16-bit address
        if byte_str:
            # Display the address at the start of the op's first byte
            display_str += ("0x" + to_hex(app_state.prog_count - int(len(byte_str) / 2), 4) + "    ")
        elif line.pseudo_op_type > 0:
            # Display the address at the start of the pseudoop's first byte
            # NOTE most pseudo ops have no byteString, hence this separate entry
            display_str += ("0x" + to_hex(app_state.prog_count, 4) + "    ")
            if line.pseudo_op_type == 3: byte_str = to_hex(line.opnd)
            if line.pseudo_op_type == 4: byte_str = to_hex(line.opnd, 4)

        # Add the lines assembled machine code
        display_str += (byte_str + set_spacer(12, len(byte_str)))

        # Add the label name - or spaces in its place
        display_str += (line_parts[0] + set_spacer(label_len - len(line_parts[0])))

        # Add the op
        op_str = line_parts[1]
        if app_state.show_upper == 1:
            op_str = op_str.upper()
        elif app_state.show_upper == 2:
            op_str = op_str.lower()
        display_str += (op_str + set_spacer(9, len(op_str)))

        # Add the operand
        if len(line_parts) > 2: display_str += line_parts[2]

        # Add the comment, if there is one
        extra_str = ""
        if len(line_parts) > 3 and len(line_parts[3]) > 1:
            if len(display_str) > 64:
                extra_str = display_str[65:]
                display_str = display_str[:65]
            display_str += (set_spacer(68, len(display_str)) + line_parts[3])

        # And output the line
        print(display_str)

        # Output any sub-lines, if any, caused by 'comment squeeze'
        if extra_str:
            while extra_str:
                print(set_spacer(41) + extra_str[:12])
                extra_str = extra_str[12:]
    return True


'''
Add new byte values to the machine code storage.

Args:
    address (int):  A 16-bit address in the store.
    value   (int):  An 8-bit value to add to the store.
'''
def poke(address, value):
    chunk = app_state.chunk
    if address - chunk["address"] > len(chunk["code"]) - 1:
        end_address = address - chunk["address"] - len(chunk["code"])
        if end_address > 1:
            # 'address' is well beyond the end of the list, so insert
            # padding values in the form of a 6809 NOP opcode
            for _ in range(0, end_address - 1): chunk["code"].append(0x12)
        # Poke the provided value after the padding
        chunk["code"].append(value)
    elif not chunk["code"]:
        # Poke in the first item
        chunk["code"].append(value)
    else:
        # Replace an existing item
        chunk["code"][address - chunk["address"]] = value


'''
Display an error message.

Args:
    err_code (int): The error type.
    err_line (int): The program on which the error occurred.
'''
def error_message(err_code, err_line):
    if 0 < err_code < len(ERRORS):
        # Show standard message
        print("Error on line " + str(err_line + 1) + ": " + ERRORS[str(err_code)])
    else:
        # Show non-standard error code
        print("Error on line " + str(err_line + 1) + ": " + str(err_code))


'''
Display a message if verbose mode is enabled.

Args:
    messsage (str): The text to print.
'''
def show_verbose(message):
    if app_state.verbose is True: print(message)


'''
Disassemble the specified .6809 or .rom file.

Args:
    file_spec (str, bool): The path and the type of the file (True = .6809, False = .rom).
'''
def disassemble_file(file_spec):
    code_data = None
    file_data = None
    file_path = file_spec[0]
    file_type = file_spec[1]

    if not os.path.exists(file_path):
        print("[ERROR] File " + file_path + " does not exist, skipping")
        return

    if file_type is True:
        # This is a .6809 file, ie. a text representation of JSON, with
        # the code set to key 'code' and the start address set to key
        # 'address'

        # FROM 1.2.0
        # The 'code' field is a string of two-character hex values,
        # which we now decode to a bytearray (as per a .rom read)
        # And we need to deal with chunks in .6809 files
        with open(file_path, "r") as file: file_data = file.read()
        code_data = json.loads(file_data)
    else:
        # This is a .rom file, ie. just a binary data dump, so open it and
        # convert to a bytearray
        file = open(file_path, "rb")
        file_data = bytearray(file.read())
        file.close()

        # FROM 1.2.0: Put the data into chunk for processing
        code_data = []
        code_chunk = {}
        code_chunk["code"] = file_data
        code_chunk["address"] = app_state.start_address
        code_data.append(code_chunk)

    if code_data is not None:
        # Disassemble the supplied set of chunks
        print("Address       Operation              Bytes          Ascii")
        print("---------------------------------------------------------")

        for chunk in code_data:
            loaded_code = chunk["code"]
            code = bytearray()
            for i in range(0, len(loaded_code), 2):
                a_char = loaded_code[i:i+2]
                a_int = int(a_char, 16)
                code.extend(a_int.to_bytes(1, byteorder='big', signed=False))

            address = chunk["address"]
            if app_state.base_address == 0: app_state.base_address = address
            if app_state.num_bytes == 0: app_state.num_bytes = len(code)

            post_op_bytes = 0
            pre_op_byte = 0
            opnd = 0
            special_opnd = 0
            index_code = 0
            address_mode = ADDR_MODE_NONE
            line_str = ""
            byte_str = ""
            str_str = ""
            index_str = ""
            got_op = False

            # Run through the machine code byte by byte
            for next_byte in code:
                # Only proceed if we're in the required address range
                if address < app_state.base_address or address > app_state.base_address + app_state.num_bytes:
                    address += 1
                    continue

                # Assemble the byte string
                byte_str += "{0:02X}".format(next_byte)
                str_str += (chr(next_byte) if 31 < next_byte < 128 else "_")

                # Combine the current byte with the previous one, if that
                # was 0x10 or 0x11 (ie. extended ISA)
                if pre_op_byte != 0:
                    next_byte = (pre_op_byte << 8) + next_byte
                    pre_op_byte = 0

                found = False
                the_op = ""
                if got_op is False:
                    # Look for an op
                    if next_byte in (0x10, 0x11):
                        # Extended ISA indicator found, so hold for combination
                        # with the next loaded byte of code
                        pre_op_byte = next_byte
                        address += 1
                        continue

                    # Run through the main ISA to find the op
                    for i in range(0, len(ISA), 6):
                        # Run through each op's possible op codes to find a match
                        for j in range(i + 1, i + 6):
                            if ISA[j] == next_byte:
                                found = True
                                the_op = ISA[i]
                                address_mode = j - i
                                break
                        if found is True: break

                    if found is False:
                        # Didn't match the byte in the main ISA, so check for a branch op
                        for i in range(0, len(BSA), 3):
                            # Run through each op's possible op codes to find a match
                            for j in range(i + 1, i + 3):
                                if BSA[j] == next_byte:
                                    found = True
                                    the_op = BSA[i]
                                    # Correct the name of an extended branch op
                                    # Add 10 to 'address_mode' to indicate branching
                                    if j - i == 2: the_op = "L" + the_op
                                    address_mode = j - i + 10
                                    break
                            if found is True: break

                    # If we still haven't matched the op, print a warning and bail
                    if found is False: print("Bad Op: " + "${0:02X}".format(next_byte))

                    # Set the initial part of the output line
                    line_str = "${0:04X}".format(address) + "         " + the_op
                    line_str += set_spacer(8, len(the_op))

                    # Gather the operand bytes (if any) according to addressing mode
                    if address_mode == ADDR_MODE_INHERENT:
                        # There's no operand with inherent addressing, so just dump the line
                        print(line_str + set_spacer(37, len(line_str)) + byte_str)
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
                            if the_op[-1:] in ("X", "Y", "D", "S", "U"): post_op_bytes = 2
                            if the_op[-2:] == "PC": post_op_bytes = 2

                            # Add the # symbol it indicate addressing type
                            line_str += "#$"
                    elif address_mode in (ADDR_MODE_DIRECT, ADDR_MODE_INDEXED, ADDR_MODE_EXTENDED):
                        # Indexed, Direct and Extended addressing
                        got_op = True
                        post_op_bytes = 1
                        address += 1
                        if address_mode == ADDR_MODE_EXTENDED: post_op_bytes += 1
                        if address_mode == ADDR_MODE_DIRECT: line_str += "<"
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
                            target = address + 1 - (256 - next_byte)
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
                                if code in (0x08, 0x09): # 8-, 16-bit offset from reg
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
                                if code in (0x0C, 0x0D): # Constant offset From PC
                                    index_str = ",PC"
                                    post_op_bytes += (code - 0x0B)
                                    index_code = code - 0x0B
                            # Wrap the operand string in brackets to indicate indirection
                            if is_indirect is True: index_str = "[" + index_str + "]"
                        else:
                            # Collect the extra byte(s) when 'index_code' is 1 or 2
                            if post_op_bytes > 0: opnd += (next_byte << (8 * (post_op_bytes - 1)))
                            if post_op_bytes == 1:
                                if index_code < 3:
                                    format_str = "${0:0" + str(index_code * 2) + "X}"
                                    index_str = format_str.format(opnd) + index_str
                                else:
                                    index_str = "${0:04X}".format(opnd)
                                if is_indirect is True: index_str = "[" + index_str + "]"
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
                        space_str = set_spacer(37, len(line_str))
                        print_str = line_str + space_str + byte_str
                        print(print_str + set_spacer(52, len(print_str)) + str_str)
                        got_op = False
                        index_code = 0
                        opnd = 0
                        byte_str = ""
                        str_str = ""
                        index_str = ""


'''
Determing the number of spaces to pad a printed line.

Args:
    a_max (int): The length of the padded line.
    a_min (int): The length of the un-padded line.

Returns:
    str: A string of spaces to pad the line.
'''
def set_spacer(a_max, a_min=0):
    spaces = "                                                         "
    num = a_max - a_min
    # If the line is too long, just return a couple of spaces
    if num < 1: return "  "
    return spaces[:num]


'''
Convert a post-op byte value into a register name.

Args:
    post_byte_value (int): The post-op byte value.

Returns:
    str: The indicated register.
'''
def get_indexed_reg(post_byte_value):
    post_byte_value = (post_byte_value & 0x60) >> 5
    regs = ("X", "Y", "U", "S")
    if post_byte_value < 4: return regs[post_byte_value]
    return "N/A"


'''
Generic TFR/EXG operand string generator, converting a post-op byte value
into disassembled output, eg. "A,B".

Args:
    post_byte_value (int): The post-op byte value.

Returns:
    str: The register string.
'''
def get_tfr_exg_regs(post_byte_value):
    reg_list = ("D", "X", "Y", "U", "S", "PC", "A", "B", "CC", "DP")
    from_nibble = (post_byte_value & 0xF0) >> 4
    to_nibble = post_byte_value & 0x0F
    from_str = reg_list[from_nibble - 2] if from_nibble > 5 else reg_list[from_nibble]
    to_str = reg_list[to_nibble - 2] if to_nibble > 5 else reg_list[to_nibble]
    return from_str + "," + to_str


'''
Pass on the correct register lists for PSHS or PULS.

Args:
    post_byte_value (int): The post-op byte value.

Returns:
    str: The list of registers referenced in the operand.
'''
def get_puls_pshs_regs(post_byte_value):
    return get_pul_psh_regs(post_byte_value, ("CC", "A", "B", "DP", "X", "Y", "U", "PC"))


'''
Pass on the correct register lists for PSHU or PULU.

Args:
    post_byte_value (int): The post-op byte value..

Returns:
    str: The list of registers referenced in the operand.
'''
def get_pulu_pshu_regs(post_byte_value):
    return get_pul_psh_regs(post_byte_value, ("CC", "A", "B", "DP", "X", "Y", "S", "PC"))


'''
Generic PUL/PSH operand string generator.

Args:
    post_byte_value (int):  The post-op byte value.
    reg_list        (list): Names of possible registers.

Returns:
    str: The list of registers referenced in the operand.
'''
def get_pul_psh_regs(post_byte_value, reg_tuple):
    output = ""
    for i in range(0, 8):
        if post_byte_value & (2 ** i) > 0:
            # Bit is set, so add the register to the output string
            output += (reg_tuple[i] + ",")
    # Remove the final comma and return the output string, eg. "CC,A,X,Y,PC"
    if output: output = output[0:len(output) - 1]
    return output


'''
Write the assembled bytes, if any, to a .6809 file.

Args:
    file_path (str): The path of the output file.
'''
def write_file(file_path=None):
    # FROM 1.2.0: The 'code' field is a sequence of hex values
    if file_path:
        op_data = []
        _, ext = os.path.splitext(file_path)
        if ext == ".rom":
            byte_arr = bytearray()
            for chunk in app_state.code:
                for a_byte in chunk["code"]: byte_arr += (a_byte.to_bytes(length=1, byteorder='big'))
            with open(file_path, "wb") as file: file.write(byte_arr)
            print("File " + os.path.abspath(file_path) + " written")
        else:
            for chunk in app_state.code:
                # Build the output data string
                byte_str = ""
                for a_byte in chunk["code"]: byte_str += ("%02X" % a_byte)

                # Build the dictionary and add to the data array
                op_part = {"address": chunk["address"], "code": byte_str}
                op_data.append(op_part)
            json_op = json.dumps(op_data, ensure_ascii=False)

            # Write out the file
            with open(file_path, "w") as file: file.write(json_op)
            print("File " + os.path.abspath(file_path) + " written")


'''
Determine all the '.asm' and '.6809' files in the script's directory.
'''
def get_files():
    current_dir = os.getcwd()
    found_files = [found_file for found_file in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, found_file))]

    # Count the number of .asm and .6809 files
    asm_files = []
    dis_files = []
    for found_file in found_files:
        _, file_ext = os.path.splitext(found_file)
        if file_ext in (".asm", ".asm6890"): asm_files.append(found_file)
        if file_ext in (".6809", ".rom"): dis_files.append(found_file)

    # Display file type breakdown
    asm_count = len(asm_files)
    if asm_count == 1:
        show_verbose("Processing 1 .asm file in " + current_dir)
    elif asm_count > 1:
        show_verbose("Processing " + str(asm_count) + " .asm/.asm6809 files in " + current_dir)
    else:
        show_verbose("No suitable .asm/.asm6809 files found in " + current_dir)

    dis_count = len(dis_files)
    if dis_count == 1:
        show_verbose("Processing 1 .6809 file in " + current_dir)
    elif dis_count > 1:
        print("Processing " + str(dis_count) + " .6809 files in " + current_dir)
    else:
        show_verbose("No suitable .6809 files found in " + current_dir)

    # Process the files
    handle_files(asm_files)
    handle_files(dis_files)


'''
Pass on all supplied '.asm' files on for assembly, '.6809' or '.rom' files for disassembly.

Args:
    the_files (list): The .asm, .rom or .6809 files.
'''
def handle_files(the_files=None):
    if the_files:
        for one_file in the_files:
            _, file_ext = os.path.splitext(one_file)
            print(file_ext)
            if file_ext in (".asm", ".asm6809"): assemble_file(one_file)
            if file_ext in (".6809", ".rom"): disassemble_file((one_file, True))


'''
Pass on all supplied '.asm' files on for assembly, '.6809' or '.rom' files for disassembly.

Args:
    the_files (list): The .asm, .rom or .6809 files.

Returns:
    int: The numerical value
'''
def str_to_int(num_str):
    num_base = 10
    if num_str[0] == "$": num_str = "0x" + num_str[1:]
    if num_str[:2] == "0x": num_base = 16
    try:
        return int(num_str, num_base)
    except ValueError:
        return False


'''
Display Spasm's help information.
'''
def show_help():
    print(" ")
    print("SPASM is an assembler/disassembler for the 8-bit Motorola 6809 chip family.")
    print(" ")
    print("Place one or more '*.asm' or '*.asm6809' files in this directory and just call")
    print("the tool, or assemble specific files by providing them as arguments.")
    print(" ")
    print("Place one or more '*.6809' or '.rom' files in this directory and call the tool,")
    print("or disassemble specific files by providing them as arguments.")
    print(" ")
    print("Options:")
    print(" -h / --help         - Print spasm help information (this screen).")
    print(" -v / --version      - Display spasm version information.")
    print(" -q / --quiet        - Display no extra information during assembly.")
    print("                       NOTE Verbose mode is the default.")
    print(" -s / --startaddress - Set the start address of the (dis)assembled code,")
    print("                       specified as a hex or decimal value.")
    print(" -b / --baseaddress  - Set the base address of disassembled code,")
    print("                       specified as a hex or decimal value.")
    print(" -n / --numbytes     - The number of bytes to disassemble.")
    print(" -o / --output       - Save assembled code to a file. The name is optional; if no name")
    print("                       is specified, the input file name is used with a suitable extension")
    print(" -l / --lower        - Display opcodes in lowercase.")
    print(" -u / --upper        - Display opcodes in uppercase.")
    print("                       NOTE the above two switches will overwrite each other")
    print("                            if both are called: the last one wins. If neither")
    print("                            is used, the output matches the input.")
    print(" ")


'''
Display Spasm's version
'''
def show_version():
    print("SPASM " + VERSION)
    print("SPASM copyright (c) 2021 Tony Smith (@smittytone)")


if __name__ == '__main__':
    # Do we have any arguments?
    if len(sys.argv) > 1:
        app_state = AppState()
        files_flag = False
        arg_flag = False
        arg_files = []
        for index, item in enumerate(sys.argv):
            if arg_flag is True:
                arg_flag = False
            elif item in ("-v", "--version"):
                show_version()
            elif item in ("-q", "--quiet"):
                app_state.verbose = False
            elif item in ("-u", "--upper"):
                app_state.show_upper = 1
            elif item in ("-l", "--lower"):
                app_state.show_upper = 2
            elif item in ("-h", "--help"):
                show_help()
                sys.exit(0)
            elif item in ("-s", "--startaddress"):
                if index + 1 >= len(sys.argv):
                    print("[ERROR] -s / --startaddress must be followed by an address")
                    sys.exit(1)
                an_address = str_to_int(sys.argv[index + 1])
                if an_address is False:
                    print("[ERROR] -s / --startaddress must be followed by a valid address")
                    sys.exit(1)
                app_state.start_address = an_address
                show_verbose("Code start address set to 0x{0:04X}".format(an_address))
                arg_flag = True
            elif item in ("-o", "--outfile"):
                if index + 1 >= len(sys.argv) or sys.argv[index + 1][0] == "-":
                    app_state.out_file = "*"
                else:
                    app_state.out_file = sys.argv[index + 1]
                    _, out_file_ext = os.path.splitext(app_state.out_file)
                    if out_file_ext not in (".6809", ".rom"):
                        print("[ERROR] -o / --outfile must specify a .6809 or .rom file")
                        sys.exit(1)
                    # Make sure 'outfile' is a .6809 file
                    parts = app_state.out_file.split(".")
                    if parts == 1: app_state.out_file += ".6809"
                    arg_flag = True
            elif item in ("-n", "--numbytes"):
                if index + 1 >= len(sys.argv):
                    print("[ERROR] -n / --numbytes must be followed by an integer value")
                    sys.exit(1)
                number = str_to_int(sys.argv[index + 1])
                if number is False:
                    print("[ERROR] -n / --numbytes must be followed by an integer value")
                    sys.exit(1)
                app_state.num_bytes = number
                show_verbose("Number of disassembly bytes set to " + str(number))
                arg_flag = True
            elif item in ("-b", "--base"):
                if index + 1 >= len(sys.argv):
                    print("[ERROR] -b / --baseaddress must be followed by an address")
                    sys.exit(1)
                an_address = str_to_int(sys.argv[index + 1])
                base = 10
                if an_address is False:
                    print("[ERROR] -b / --baseaddress must be followed by an address")
                    sys.exit(1)
                app_state.base_address = an_address
                show_verbose("Disassembly start address set to 0x{0:04X}".format(an_address))
                arg_flag = True
            else:
                if item[0] == "-":
                    print("[ERROR] unknown option: " + item)
                    sys.exit(1)
                elif index != 0 and arg_flag is False:
                    # Handle any included .asm, .6809 or .rom files
                    _, arg_file_ext = os.path.splitext(item)
                    if arg_file_ext in (".asm", ".asm6809", ".6809", ".rom"):
                        arg_files.append(item)
                    else:
                        print("[ERROR] File " + item + " is not a .asm, .6809 or .rom file")
        # Process any named files
        if arg_files: handle_files(arg_files)
    else:
        # By default show help
        show_help()

    sys.exit(0)
