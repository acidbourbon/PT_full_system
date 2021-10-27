import os
import db
import tdc_daq
from time import sleep
# import copy

from trbnet import TrbNet
from pathlib import Path

import pasttrec_ctrl as pt

lib = '/trbnettools/trbnetd/libtrbnet.so'
host = os.getenv("DAQOPSERVER")

defaultPtSettings = {
    "baseline_sel": 0b1,  
    "tc1_c": 0b011,
    "tc1_r": 0b110,
    "tc2_c": 0b101,
    "tc2_r": 0b010, 
    "lvds_dac": 0b101
}

defaultPtMemory = {
    0xFF : 0xFFFFFFFF
}

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
    def __init__(self, gain=4,peaktime=10,thr=0x08,baselines=[0x0f,0x0f,0x0f,0x0f,0x0f,0x0f,0x0f,0x0f]):
        assert gain in [0.67,1,2,4], "Incorrect gain value ({}). Correct are [0.67,1,2,4]".format(gain)
        assert peaktime in [10,15,20,35], "Incorrect peaking time value ({}). Correct are [10,15,20,35]".format(pt)
        assert thr in range(2**7), "Incorrect threshold value ({}).".format(thr)
        self.gain = gain
        self.pt = peaktime
        self.thr = thr
        self.baselines = baselines
    def setBaseline(self, new):
        assert len(new) == 8, "Incorrect baseline array: {}".format(new)
        for el in new:
            assert el >= 0 and el <= 31, "Incorrect value"
        self.baselines = new
    def setGain(self, gain):
        assert gain in [0.67,1,2,4], "Incorrect gain value ({}). Correct are [0.67,1,2,4]".format(gain)
        self.gain = gain
    def setPt(self, peaktime):
        assert peaktime in [10,15,20,35], "Incorrect peaking time value ({}). Correct are [10,15,20,35]".format(peaktime)
        self.pt = peaktime
    def setThr(self, thr):
        assert thr in range(2**7), "Incorrect threshold value ({}).".format(thr)
        self.thr = thr
    def getImage(self):
        gain = {0.67: 0b11, 1: 0b10, 2: 0b01, 4: 0b00}
        pt = {10: 0b00, 15: 0b01, 20: 0b10, 35: 0b11}
        cmds = {
            0x0: (defaultPtSettings["baseline_sel"] << 4) + (gain[self.gain] << 2) + pt[self.pt],
            0x1: (defaultPtSettings["tc1_c"] << 3) + (defaultPtSettings["tc1_r"]),
            0x2: (defaultPtSettings["tc2_c"] << 3) + (defaultPtSettings["tc2_r"]),
            0x3: (self.thr),
            0xD: defaultPtSettings["lvds_dac"]
        }
        for i,ch in enumerate(self.baselines):
            cmds[i+4] = ch
        return cmds
    def __str__(self):
        st = "gain: {}, pt: {}, thr: {}, baselines: {}".format(self.gain,self.pt,self.thr,self.baselines)
        return st
        
class MDCTDC_FPGA: 
    def __init__(self, addr, pasttrec):
        self.addr = "0x{:04X}".format(int(addr,16))
        self.pasttrec = pasttrec
    def found_baseline(self, scanning_time = 0.2):
        baselines = pt.found_baselines_for_board(self.addr, scanning_time)
        rounded = []
        for ch in baselines:
            if "err" in baselines[ch]: 
                print("Error: noize {} for FPGA {} ch {}".format(baselines[ch]["err"],self.addr, ch))
                continue
            if baselines[ch]["rms"] > 5: 
                print("Warning: noize rms is greater than 5 for FPGA {} ch {}".format(self.addr, ch))
                # return 
            # if baselines[ch]["rms"] > 1: print("Warning: noize stdev is greater than 1 for FPGA {} ch {}".format(self.addr, ch))
            base = round(baselines[ch]["mean"])
            rounded.append(base + 15)#self.pasttrec[ch // 8].baselines[ch % 8] = base + 15
        for i,past in enumerate(self.pasttrec):
            past.setBaseline(rounded[i*8 : i*8+8])
    def getImage(self):
        cmdlist = {}
        ncmd = [0,0,0,0]
        startaddr = [0,0,0,0]
        index = 0x10
        for pastn,past in enumerate(self.pasttrec):
            image = past.getImage()
            startaddr[pastn] = index
            for key in image:
                cmdlist[index] = (0x50 << 12) + (key << 8) + image[key]
                index += 1
            ncmd[pastn] = len(image)
            index += 1
        cmdlist[0x2] = 0x40004000 + (ncmd[0] << 8) + (ncmd[1] << 16+8) + startaddr[0] + (startaddr[1] << 16)
        cmdlist[0x3] = 0x40004000 + (ncmd[2] << 8) + (ncmd[3] << 16+8) + startaddr[2] + (startaddr[3] << 16)
        res = {**defaultPtMemory, **cmdlist} 
        return res
    def __str__(self):
        st = "FPGA {}\n".format(self.addr)
        for i,past in enumerate(self.pasttrec):
            st += "\tPASTTREC {}: {}\n".format(i,past)
        return st
    def __getitem__(self,key):
        return self.pasttrec[key]

class MDCTDC_OEP: 
    def __contains__(self, item):
        return item in self.fpga #[fpga.addr for fpga in self.fpga]
    def __init__(self, addr, fpga):
        self.addr = "0x{:04X}".format(int(addr,16))
        self.fpga = fpga
    def __str__(self):
        st = "OEP \t |    |\t        FPGA1       |\t        FPGA2       |\t        FPGA3       \n"
        st += "{}\t | -- ".format(self.addr)
        for fpga in self.fpga.values():
            st += "|\t\t\t{}\t\t".format(fpga.addr)
        st += "|\n"
        st += "\t\t | CH |\tPT1  PT2  PT3  PT4  |\tPT1  PT2  PT3  PT4  |\tPT1  PT2  PT3  PT4  \n"
        st += "\t\t | GA "
        for fpga in self.fpga.values():
            st += "|\t{:4.2f} {:4.2f} {:4.2f} {:4.2f}\t".format(*[past.gain for past in fpga.pasttrec])#(fpga.pasttrec[0].gain),(fpga.pasttrec[1].gain),(fpga.pasttrec[2].gain),(fpga.pasttrec[3].gain))
        st += "|\n"
        st += "\t\t | TH "    
        for fpga in self.fpga.values():
            st += "|\t0x{:02X} 0x{:02X} 0x{:02X} 0x{:02X}\t".format(*[past.thr for past in fpga.pasttrec])#(fpga.pasttrec[0].thr),(fpga.pasttrec[1].thr),(fpga.pasttrec[2].thr),(fpga.pasttrec[3].thr))
        st += "|\n"
        st += "\t\t | PT "    
        for fpga in self.fpga.values():
            st += "|\t{} {} {} {}\t".format(*[str(past.pt).rjust(4,"0") for past in fpga.pasttrec])#(fpga.pasttrec[0].pt),(fpga.pasttrec[1].pt),(fpga.pasttrec[2].pt),(fpga.pasttrec[3].pt))
        for ch in range(8):
            st += "|\n"
            st += "\t\t | B{} ".format(ch)    
            for fpga in self.fpga.values():
                st += "|\t0x{:02X} 0x{:02X} 0x{:02X} 0x{:02X}\t".format(*[past.baselines[ch] for past in fpga.pasttrec])#(fpga.pasttrec[0].baselines[ch]),(fpga.pasttrec[1].baselines[ch]),(fpga.pasttrec[2].baselines[ch]),(fpga.pasttrec[3].baselines[ch]))
        st +="|"
        return st
    def __getitem__(self, key):
        return self.fpga[key]

# class Configuration: #TODO

def generateDefaultConfiguration(mdctree):
    OEPs = {}
    for oep in mdctree:
        fpga_l = {}
        for fpga in mdctree[oep]:
            fpga_l[fpga] = MDCTDC_FPGA(fpga, [MDCTDC_PT(), MDCTDC_PT(), MDCTDC_PT(), MDCTDC_PT()])
        OEPs[oep] = MDCTDC_OEP(oep, fpga_l)
    return OEPs

def writeConfigurationToFile(file, conf): 
    with open(file,"w") as f:
        for oepaddr, oep in conf.items():
            print(oep, file=f)
    os.chmod(file, 0o777)  

def readConfigurationFromFile(file):
    OEPs = {}
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
                    # print("Found fpgas: ", fpga_addr)
                    state = 1
                elif state == 1:
                    if "PT1  PT2  PT3  PT4" in line:
                        state = 3
                elif state == 3:
                    for nt, token in enumerate(tokens[2:]):
                        if not token: continue
                        values = [el.strip() for el in token.split(" ")]
                        if setno == 0:
                            gain_arr.append([float(el) for el in values])
                        elif setno == 1:
                            thr_arr.append([int(el,16) for el in values])
                        elif setno == 2:
                            pt_arr.append([int(el) for el in values])
                        else:
                            ch_arr[setno-3].append([int(el,16) for el in values])
                    setno += 1
            fpgas = {}
            for i,fpga in enumerate(fpga_addr):
                thrs = thr_arr[i]
                pts = pt_arr[i]
                gas = gain_arr[i]
                chs = [ch_arr[ch][i] for ch in range(8)]
                pasttrecs = []
                for j in range(4):
                    pasttrecs.append(MDCTDC_PT(gas[j], pts[j], thrs[j], [el[j] for el in chs]))
                fpgas[fpga_addr[i]] = MDCTDC_FPGA(fpga_addr[i], pasttrecs)
            OEPs[oepaddr.strip()] = MDCTDC_OEP(oepaddr.strip(), fpgas)
    return OEPs

# def overwrite(base, changes):
#     newOep = copy.deepCopy(base)
#     for oep in changes:
#         if oep in newOep:
#             newOep[oep] = changes[oep]
    # return copy.deepCopy(newOep)        
    
def createImage(conf, path):
    Path(path).mkdir(parents=True, exist_ok=True)
    for oepaddr, oep in conf.items():
        for fpga in oep.fpga.values():
            fullpath = path + "/{}/".format(oep.addr)
            Path(fullpath).mkdir(parents=True, exist_ok=True)
            with open(fullpath + fpga.addr + ".hex", "w") as f:
                image = fpga.getImage()
                for i in image:
                    print("0xA0{:02X}".format(i),"0x{:08X}".format(image[i]), file = f)
                print("0xAA00 0x00000000",file=f)

def uploadImage(path, flash_settings, TDCs=[]):
    for oep in os.listdir(path):
        d = os.path.join(path, oep)
        if not os.path.isdir(d): continue
        if oep[:2] != "0x": continue
        if len(oep) != 6: continue
        for fpga in os.listdir(d):
            if fpga[-4:] != ".hex": continue
            if fpga[:2] != "0x": continue
            if len(TDCs) > 0:
                if fpga[:-4] not in TDCs: continue
            cmd = "{} {} {}".format(flash_settings,fpga[:-4], os.path.join(os.getcwd(),d,fpga)) 
            print("Running: ", cmd)
            if os.system(cmd) == 1:
                print("Error code returned")
                return

def found_all_baselines(conf, scaning_time = 0.2, plot=False):
    TDCs = []
    for oep in conf.values():
        TDCs = [*TDCs, *[el for el in oep.fpga]]
    baselines = pt.found_baselines_for_boards(TDCs, scaning_time=scaning_time, plot=plot)
    for oep in conf.values():
        for fpga in oep.fpga.values():
            # for ch in baselines[fpga.addr]:
            for i,past in enumerate(fpga.pasttrec):
                past.setBaseline([ round(el["mean"]) + 15 for el in list(baselines[fpga.addr].values())[8*i:8+8*i] ])
    