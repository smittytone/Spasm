#!/usr/bin/env python3

##########################################################################
# Application-specific classes                                           #
##########################################################################

'''
A very simple class to hold the temporary decode data for a line of
6809 assembly code.
'''
class LineData:
    def __init__(self):
        self.oper = []               # The line elements
        self.opnd = -1
        self.op_type = 0
        self.branch_op_type = 0
        self.pseudo_op_type = 0
        self.pseudo_op_value = ""
        self.index_address = -1
        self.line_number = 0
        self.comment_start = -1
        self.is_indirect = False
        self.is_indexed = False
        self.expects_8b_opnd = False # ADDED 1.2.0


'''
A very simple class to hold the application's state and preference data.
'''
class AppState:
    def __init__(self):
        self.verbose = True
        self.start_address = 0x0000
        self.base_address = 0x0000
        self.prog_count = 0
        self.pass_count = 0
        self.show_upper = 0
        self.num_bytes = 256
        self.labels = None
        self.code = None
        self.out_file = None
        self.chunk = None
