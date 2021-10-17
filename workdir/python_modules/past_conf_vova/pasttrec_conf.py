import os
import db
import tdc_daq
from time import sleep
import copy

from trbnet import TrbNet

import sys  
sys.path.insert(0, '../')
import pasttrec_ctrl as pt

lib = '/trbnettools/trbnetd/libtrbnet.so'
host = os.getenv("DAQOPSERVER")

def getConnectedMDCtree():
    t = TrbNet(libtrbnet=lib, daqopserver=host)
    boards = t.trb_read_uid(0xffff)
    hardware = t.trb_register_read( 0xffff, 0x42 )
    # print("Boards: {}, Hardwares: {}".format(len(boards), len(hardware)))
    tree = {}

    def addToTree(element, indexes, array):
        if len(indexes) == 0:
            if element not in array:
                array[element] = {}
        else:
            if indexes[0] not in array:
                array[indexes[0]] = {}
            addToTree(element, indexes[1:], array[indexes[0]])

    for board in boards:
        path = [hex(el) for el in t.trb_nettrace(board,16) ]
        path = [el for i, el in enumerate(path) if i % 2 == 0]
        if len(path) > 0:
            addToTree(hex(board), path, tree)
        else:
            tree[hex(board)] = {} 
    even = [el for i,el in enumerate(hardware) if i % 2 == 0]
    odd = [((el >> 24) & 0xFF) for i,el in enumerate(hardware) if i % 2 == 1]

    hubs = {}
    def addToHubs(elements):
        for el in elements:
            if int(el,16) not in even: 
                addToHubs(elements[el])
                continue
            ind = even.index(int(el,16))
            value = odd[ind]
            if value == 0xa6:
                hubs[el] = elements[el]
            else:
                addToHubs(elements[el])
    addToHubs(tree)
    return hubs

class MDCTDC_PT: 
    def __init__(self, gain=4,pt=10,thr=0x08,baselines=[0x0f,0x0f,0x0f,0x0f,0x0f,0x0f,0x0f,0x0f]):
        self.gain = gain
        self.pt = pt
        self.thr = thr
        self.baselines = baselines
        
class MDCTDC_FPGA: 
    def __init__(self, addr, pasttrec):
        self.addr = "0x{:04X}".format(int(addr,16))
        self.pasttrec = pasttrec
    def found_baseline(self):
        baselines = pt.found_baselines_for_board(self.addr)
        for ch in baselines:
            if "err" in baselines[ch]: 
                print("Error: noize {} for FPGA {} ch {}".format(baselines[ch]["err"],self.addr, ch))
                continue
            if baselines[ch]["sigma"] > 5: 
                print("Error: noize stdev is greater than 5 for FPGA {} ch {}".format(self.addr, ch))
                return 
            if baselines[ch]["sigma"] > 1: print("Warning: noize stdev is greater than 1 for FPGA {} ch {}".format(self.addr, ch))
            base = round(baselines[ch]["mean"])
            self.pasttrec[ch // 8].baselines[ch % 8] = base + 15
        
class MDCTDC_OEP: 
    def __contains__(self, item):
        return item in [fpga.addr for fpga in self.fpga]
    def __init__(self, addr, fpga):
        self.addr = "0x{:04X}".format(int(addr,16))
        self.fpga = fpga
    def __str__(self):
        st = "OEP \t |    |\t        FPGA1       |\t        FPGA2       |\t        FPGA3       \n"
        st += "{}\t | -- ".format(self.addr)
        for fpga in self.fpga:
            st += "|\t\t\t{}\t\t".format(fpga.addr)
        st += "|\n"
        st += "\t\t | CH |\tPT1  PT2  PT3  PT4  |\tPT1  PT2  PT3  PT4  |\tPT1  PT2  PT3  PT4  \n"
        st += "\t\t | GA "
        for fpga in self.fpga:
            st += "|\t0x{:02X} 0x{:02X} 0x{:02X} 0x{:02X}\t".format((fpga.pasttrec[0].gain),(fpga.pasttrec[1].gain),(fpga.pasttrec[2].gain),(fpga.pasttrec[3].gain))
        st += "|\n"
        st += "\t\t | TH "    
        for fpga in self.fpga:
            st += "|\t0x{:02X} 0x{:02X} 0x{:02X} 0x{:02X}\t".format((fpga.pasttrec[0].thr),(fpga.pasttrec[1].thr),(fpga.pasttrec[2].thr),(fpga.pasttrec[3].thr))
        st += "|\n"
        st += "\t\t | PT "    
        for fpga in self.fpga:
            st += "|\t0x{:02X} 0x{:02X} 0x{:02X} 0x{:02X}\t".format((fpga.pasttrec[0].pt),(fpga.pasttrec[1].pt),(fpga.pasttrec[2].pt),(fpga.pasttrec[3].pt))
        for ch in range(8):
            st += "|\n"
            st += "\t\t | B{} ".format(ch)    
            for fpga in self.fpga:
                st += "|\t0x{:02X} 0x{:02X} 0x{:02X} 0x{:02X}\t".format((fpga.pasttrec[0].baselines[ch]),(fpga.pasttrec[1].baselines[ch]),(fpga.pasttrec[2].baselines[ch]),(fpga.pasttrec[3].baselines[ch]))
        st +="|"
        return st


def generateDefaultConfiguration(mdctree):
    OEPs = []
    for oep in mdctree:
        fpga_l = []
        for fpga in mdctree[oep]:
            fpga_l.append(MDCTDC_FPGA(fpga, [MDCTDC_PT(), MDCTDC_PT(), MDCTDC_PT(), MDCTDC_PT()]))
        OEPs.append(MDCTDC_OEP(oep, fpga_l))
    return OEPs

def readConfigurationFromFile(file):
    OEPs = []
    with open(file,"r") as f:
        content = f.read().split("OEP 	 |    |	        FPGA1       |	        FPGA2       |	        FPGA3       ")
        for oep in content:
            if not oep: continue
    #         print("OEP: ", oep)
            lines = oep.split("\n")
            fpga_addr = []
            gain_arr = []
            thr_arr = []
            pt_arr = []
            ch_arr = [[], [], [], [], [], [], [], []]
            state = 0
            setno = 0
            for i,line in enumerate(lines):
                if not line: continue
    #             print("line {}: ".format(i), line)
                tokens = line.split("|")
                if state == 0:
                    if "0x" not in tokens[0]: continue
                    oepaddr = tokens[0]
                    for token in tokens[2:]:
                        if not token: continue
                        fpga_addr.append(token.strip())
                    print("Found fpgas: ", fpga_addr)
                    state = 1
                elif state == 1:
                    if "PT1  PT2  PT3  PT4" in line:
                        state = 3
                elif state == 3:
                    for nt, token in enumerate(tokens[2:]):
                        if not token: continue
                        values = [el.strip() for el in token.split(" ")]
                        if setno == 0:
                            gain_arr.append([int(el,16) for el in values])
                        elif setno == 1:
                            thr_arr.append([int(el,16) for el in values])
                        elif setno == 2:
                            pt_arr.append([int(el,16) for el in values])
                        else:
                            ch_arr[setno-3].append([int(el,16) for el in values])
                    setno += 1
            fpgas = []
            for i,fpga in enumerate(fpga_addr):
                thrs = thr_arr[i]
                pts = pt_arr[i]
                gas = gain_arr[i]
                chs = [ch_arr[ch][i] for ch in range(8)]
                pasttrecs = []
                for j in range(4):
                    pasttrecs.append(MDCTDC_PT(gas[j], pts[j], thrs[j], [el[j] for el in chs]))
                fpgas.append(MDCTDC_FPGA(fpga_addr[i], pasttrecs))
            OEPs.append(MDCTDC_OEP(oepaddr.strip(), fpgas))
    return OEPs

def overwrite(base, changes):
    newOep = copy.deepCopy(base)
    for oep in changes:
        if oep in newOep:
            newOep[oep] = changes[oep]
    return copy.deepCopy(newOep)        
    

# OEPs = generateDefaultConfiguration(getConnectedMDCtree())

# with open(os.open('test.txt', os.O_CREAT | os.O_WRONLY, 0o777),"w") as f:
#     for oep in OEPs:
#         print(oep.thr_str(), file=f)
    
# os.chmod("test.txt", 0o777)