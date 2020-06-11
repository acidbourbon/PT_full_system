#!/usr/bin/env python3

import db
import pasttrec_ctrl as ptc


################################################################
##     define sequence of boards to activate in scan          ##
################################################################


def generate_neighbouring_FPC_board_list(name):
    ## define sequence of boards to activate in scan.
    # switch on first boards at niegbouring wires, then boards far away from board under investigation, same layer, then next layer
    next_fpc_difference = []
    ## generate alternating  +,- list of numbers 
    for i in range(0,40):
        next_fpc_difference += [ i ]
        next_fpc_difference += [ -1*i ]

    fpca = db.get_fpca_of_board(name)
    fpcd = db.get_fpcd_of_board(name)
    boards_scan_list = []
    boards_scan_list += [ name ]
    for chamber in range(0,6):
      nextchamber = db.get_chamber_of_board(name)+next_fpc_difference[chamber]
      for layer in range(0,6):
        nextlayer = db.get_layer_of_board(name)+next_fpc_difference[layer]
        for nplus in next_fpc_difference:
            nextfpca = fpca+nplus
            next_board = db.find_board_by_fpc(nextfpca,nextlayer,nextchamber)
            if next_board != 0 and next_board not in boards_scan_list:
                boards_scan_list += [ next_board ]

    print( str(len(boards_scan_list)) + " boards to activate, sequence of activation, boards list: ")
    print(boards_scan_list)
    return boards_scan_list

def generate_neighbouring_w_board_list(name):
    ## define sequence of boards to activate in scan.
    # switch on first boards at niegbouring wires in all layers, then boards far away from board under investigation, 
    next_fpc_difference = []
    ## generate alternating  +,- list of numbers 
    for i in range(0,40):
        next_fpc_difference += [ i ]
        next_fpc_difference += [ -1*i ]
    fpca = db.get_fpca_of_board(name)
    fpcd = db.get_fpcd_of_board(name)
    boards_scan_list = []
    boards_scan_list += [ name ]
    for chamber in range(0,6):
        nextchamber = db.get_chamber_of_board(name)+next_fpc_difference[chamber]
        for nplus in next_fpc_difference:
            nextfpca = fpca+nplus
            for layer in range(0,6):
                nextlayer = db.get_layer_of_board(name)+next_fpc_difference[layer]
                next_board = db.find_board_by_fpc(nextfpca,nextlayer,nextchamber)
                if next_board != 0 and next_board not in boards_scan_list:
                    boards_scan_list += [ next_board ]

    print( str(len(boards_scan_list)) + " boards to activate, sequence of activation, boards list: ")
    print(boards_scan_list)
   
    return boards_scan_list