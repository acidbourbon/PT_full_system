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

class ConfStorage:
    """
    A class for storing prefilled sets of both PASTTREC settings and module memory content.

    Attributes

        defaultPtSettings: dict(str, int)
            Values of some default PASTTREC registers, that are the same for the whole system.

        memory_content_map: dict(str, dict(str, int))
            Default blocks of commands, that are flashed to module memory. The addr field corresponds to the address of a first command inside module memory. The len corresponds to the number of commands in a set.
    
        defaultPtMemory: dict(int, int)
            The actual default content of module memory. Each entry corresponds to the slow-control command for PASTTREC.
    """
    defaultPtSettings = {
        "baseline_sel": 0b1,  
        "tc1_c": 0b011,
        "tc1_r": 0b110,
        "tc2_c": 0b101,
        "tc2_r": 0b010, 
        "lvds_dac": 0b101
    }

    memory_content_map = {
        "blue_settings_pt10_g1_thr127":     { "addr": 0xC0, "len": 12},
        "black_settings_pt20_g1_thr127":    { "addr": 0xD0, "len": 12},
        "black_settings_pt15_g1_thr127":    { "addr": 0xE0, "len": 12},
        "fast_past_reading":                { "addr": 0xF0, "len": 16},
    }

    defaultPtMemory = {
        0xC0 : 0x00050018, # blue_settings_pt10_g1_thr127
        0xC1 : 0x0005011e,
        0xC2 : 0x00050215,
        0xC3 : 0x0005037f,
        0xC4 : 0x0005040f,
        0xC5 : 0x0005050f,
        0xC6 : 0x0005060f,
        0xC7 : 0x0005070f,
        0xC8 : 0x0005080f,
        0xC9 : 0x0005090f,
        0xCa : 0x00050a0f,
        0xCb : 0x00050b0f, # end blue_settings_pt10_g1_thr127
        0xD0 : 0x0005001a, # black_settings_pt20_g1_thr127
        0xD1 : 0x0005011e,
        0xD2 : 0x00050215,
        0xD3 : 0x0005037f,
        0xD4 : 0x0005040f,
        0xD5 : 0x0005050f,
        0xD6 : 0x0005060f,
        0xD7 : 0x0005070f,
        0xD8 : 0x0005080f,
        0xD9 : 0x0005090f,
        0xDa : 0x00050a0f,
        0xDb : 0x00050b0f, # end black_settings_pt20_g1_thr127
        0xE0 : 0x00050019, # black_settings_pt15_g1_thr127
        0xE1 : 0x0005011e,
        0xE2 : 0x00050215,
        0xE3 : 0x0005037f,
        0xE4 : 0x0005040f,
        0xE5 : 0x0005050f,
        0xE6 : 0x0005060f,
        0xE7 : 0x0005070f,
        0xE8 : 0x0005080f,
        0xE9 : 0x0005090f,
        0xEa : 0x00050a0f,
        0xEb : 0x00050b0f, # end black_settings_pt15_g1_thr127
        0xF0 : 0x00051000, # fast pasttrec reading block
        0xF1 : 0x00051100,
        0xF2 : 0x00051200,
        0xF3 : 0x00051300,
        0xF4 : 0x00051400,
        0xF5 : 0x00051500,
        0xF6 : 0x00051600,
        0xF7 : 0x00051700,
        0xF8 : 0x00051800,
        0xF9 : 0x00051900,
        0xFA : 0x00051A00,
        0xFB : 0x00051B00,
        0xFC : 0x00051C00,
        0xFD : 0x00051D00,
        0xFE : 0x00051E00,
        0xFF : 0x00051F00, # end fast pasttrec reading block
    }

class Helper:
    """
    A class contains useful functions, that can be used independently from all other code.
    """
    @staticmethod
    def getConnectedMDCtree():
        """
        Generate a dictionary, that contains all connected OEP’s and FPGA’s addresses. It should be the same as in NetworkMap.

        :return: Generated mdc_tree
        :rtype: dict(str, list(str))
        """
        t = TrbNet(libtrbnet=lib, daqopserver=host)
        boards = t.trb_read_uid(0xffff)
        hardware = t.trb_register_read( 0xffff, 0x42 )
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

    @staticmethod
    def getActiveMDCsubtree():
        """
        The same as getConnectedMDCtree(), but return only that boards that are not in standby mode.

        :return: Generated mdc_tree
        :rtype: dict(str, list(str))
        """
        full_tree = Helper.getConnectedMDCtree()
        for oep_key in list(full_tree.keys()):
            for board_key in list(full_tree[oep_key].keys()):
                standby_info = [el["standby"] for el in db.get_tdc_json(board_key)["board"]]
                if any(standby_info):
                    del full_tree[oep_key][board_key]
            if len(full_tree[oep_key]) == 0:
                del full_tree[oep_key]
        return full_tree


class Configuration:
    """
    The main class for handling all the PASTTREC configurations.

    Attributes

        OEPs: list(MDCTDC_OEP)
            An array of all associated with this configuration OEP objects.

    """
    def __init__(self, mdc_tree=None, file=None):
        """
        Constructor. Either mdc_tree or file must be specified. If both, the configuration will be loaded from a file.

        Parameters
        mdc_tree (dict) - A tree that contains addresses of all boards.

        file (str) - Path to the configuration file.

        Returns
        The instance of Configuration class.

        Raises
        SyntaxError - If neither mdc_tree nor file specified.
        """
        if file:
            self.readConfigurationFromFile(file)
        elif mdc_tree:
            self.generateDefault(mdc_tree)
        else:
            raise SyntaxError("Either mdc_tree or file must be specified")
    def generateDefault(self,mdctree):
        """
        Default initialization of configuration object.

        Parameters
        mdc_tree (dict) - A tree that contains addresses of all boards.

        Returns
        this object.

        Return type
        Configuration
        """
        OEPs = {}
        for oep in mdctree:
            fpga_l = {}
            for fpga in mdctree[oep]:
                fpga_l[fpga] = MDCTDC_FPGA(fpga, [MDCTDC_PT(), MDCTDC_PT(), MDCTDC_PT(), MDCTDC_PT()])
            OEPs[oep] = MDCTDC_OEP(oep, fpga_l)
        self.OEPs = OEPs
        return self

    def found_all_baselines(self, scanning_time = 0.2, plot=False, apply_res=False):
        """
        Found the baselines for all FPGAs, present in the current configuration, using the noise method.

        Parameters
        scanning_time (float) - Duration of each step during data acquisition.

        plot (boolean) - if true, plots the noise level versus baseline for each channel.

        apply_res (boolean) - if true, after the baselines will be found, they will be applied for each channel.

        Returns
        this object.

        Return type
        Configuration
        """
        conf = self.OEPs
        TDCs = []
        for oep in conf.values():
            TDCs = [*TDCs, *[el for el in oep.fpga]]
        baselines = pt.found_baselines_for_boards(TDCs, scanning_time=scanning_time, plot=plot, apply_res=apply_res)
        for oep in conf.values():
            for fpga in oep.fpga.values():
                for i,past in enumerate(fpga.pasttrec):
                    past.setBaselines([ round(el["mean"]) + 15 for el in list(baselines[fpga.addr].values())[8*i:8+8*i] ])
        self.OEPs = conf
        return self
        
    def writeConfigurationToFile(self, file):
        """
        Save this configuration object to file.

        Parameters
        file (str) - path to a file

        Returns
        this object.

        Return type
        Configuration
        
        """
        conf = self.OEPs 
        with open(file,"w") as f:
            for oepaddr, oep in conf.items():
                print(oep, file=f)
        os.chmod(file, 0o777)  
        return self
    def readConfigurationFromFile(self, file):
        """
        Initialization of configuration object from file.

        Parameters
        file (str) - path to a file

        Returns
        this object.

        Return type
        Configuration
        """
        OEPs = {}
        with open(file,"r") as f:
            content = f.read().split("OEP 	 |    |	        FPGA1       |	        FPGA2       |	        FPGA3       ")
            for oep in content:
                if not oep: continue
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
        self.OEPs = OEPs
        return self

    def createImage(self, path):
        """
        Create a flashable image from this configuration object and save it on the disk.

        Parameters
        path (str) - path to a folder, where the image should be placed.

        Returns
        this object.

        Return type
        Configuration
        """
        conf = self.OEPs
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
        return self

    def applyChanges(self, allowed_tdc = []):
        """
        Temporary apply this configuration to selected TDCs. Kept until a power cycle or soft reset.

        Parameters
        allowed_tdc (list(str)) - list of TDCs, for which changes should be applied. If empty - apply for all boards in this configuration.

        Returns
        this object.

        Return type
        Configuration 
        """
        for oepaddr, oep in self.OEPs.items():
            for fpga_addr, fpga in oep.fpga.items():
                if len(allowed_tdc) != 0:
                    if fpga_addr not in allowed_tdc: continue
                pt.reset_board(fpga_addr)
                for past_n,pasttrec in enumerate(fpga.pasttrec):
                    image = pasttrec.getImage()
                    for reg, value in image.items():
                        pt.spi_set_pasttrec_register(fpga_addr, past_n, reg, value)
        return self

    @staticmethod
    def flashImage(path, flash_settings, TDCs=[]):
        """
        Flash image to selected TDCs.

        Parameters
        path (str) - Path to a saved image on disk, that should be flashed.

        flash_settings (str) - Path to flash_settings script with all required flags.

        TDCs (list(str)) - list of TDCs, that should be flashed. If empty - apply for all boards in this configuration.

        Returns
        None.
        """
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

    def __str__(self):
        st = ""
        for oep in self.OEPs.values():
            st += str(oep) + "\n"
        return st

    def __getitem__(self, key):
        """
        Indexing of configuration object allow to interact with OEP of FPGA objects.

        """
        if key in self.OEPs:
            return self.OEPs[key]
        for oep in self.OEPs.values():
            if key in oep.fpga:
                return oep.fpga[key]
        raise KeyError("Address not found")
    def __delitem__(self, key):
        if key in self.OEPs:
            del self.OEPs[key]
            return
        for oep in self.OEPs.values():
            if key in oep.fpga:
                del oep.fpga[key]
                return
        raise KeyError("Address not found")

class MDCTDC_PT: 
    """
    A class for handling the individual configurations for each PASTTREC.

        Attributes

        gain: float
        Value of gain for this PASTTREC. Acceptable values is only: 0.67, 1, 2, 4.

        pt: float
        Value of peaking time for this PASTTREC. Acceptable values is only: 10, 15, 20, 35.

        thr: float
        Value of threshold for this PASTTREC. Acceptable values are from range from 0 to 2^7.

        baselines: list(float)
        Values of baseline for each channel of this PASTTREC. Acceptable values are from range from 0 to 31.

        gain_map: dict(float, int)= {0.67: 0b11, 1: 0b10, 2: 0b01, 4: 0b00}
        Bit mask for each value of gain.

        pt_map: dict(float, int)= {10: 0b00, 15: 0b01, 20: 0b10, 35: 0b11}
        Bit mask for each value of peaking time.
    """

    gain_map = {0.67: 0b11, 1: 0b10, 2: 0b01, 4: 0b00}
    pt_map = {10: 0b00, 15: 0b01, 20: 0b10, 35: 0b11}
    def __init__(self, gain=4,peaktime=10,thr=0x08,baselines=[0x0f,0x0f,0x0f,0x0f,0x0f,0x0f,0x0f,0x0f]):
        """
        Constructor

        Parameters
        gain (float) - A value of gain.

        peaktime (float) - A value of peaking time.

        thr (float) - A value of threshold.

        baselines (list(float)) - Values of baseline levels.

        Returns
        The instance of MDCTDC_PT object.
        
        """

        assert gain in [0.67,1,2,4], "Incorrect gain value ({}). Correct are [0.67,1,2,4]".format(gain)
        assert peaktime in [10,15,20,35], "Incorrect peaking time value ({}). Correct are [10,15,20,35]".format(pt)
        assert thr in range(2**7), "Incorrect threshold value ({}).".format(thr)
        self.gain = gain
        self.pt = peaktime
        self.thr = thr
        self.baselines = baselines
    def setBaselines(self, new):
        """
        Set a new values for baselines. Automatically checks validity.

        Parameters
        ----------
        new : array(float)
            New baselines
        """

        assert len(new) == 8, "Incorrect baseline array: {}".format(new)
        for el in new:
            assert el >= 0 and el <= 31, "Incorrect value"
        self.baselines = new
    def setBaseline(self, ch, value):
        """
        Set a new value for one specific baseline. Automatically checks validity.

        Parameters
        ch (float) - Channel number.

        value (float) - New value of baseline for channel ch.

        Returns
        None
        """

        assert type(ch) == int and ch >= 0 and ch <= 7
        assert type(value) == int and value >= 0 and value <= 0x1F
        self.baselines[ch] = value
    def setGain(self, gain):
        """
        Set a new value for gain. Automatically checks validity.

        Parameters
        gain (float) - New value of gain.

        Returns
        None
        """

        assert gain in [0.67,1,2,4], "Incorrect gain value ({}). Correct are [0.67,1,2,4]".format(gain)
        self.gain = gain
    def setPt(self, peaktime):
        """
        Set a new value for peaking time. Automatically checks validity.

        Parameters
        peaktime (float) - New value of peaking time.

        Returns
        None
        """

        assert peaktime in [10,15,20,35], "Incorrect peaking time value ({}). Correct are [10,15,20,35]".format(peaktime)
        self.pt = peaktime
    def setThr(self, thr):
        """
        Set a new value for threshold. Automatically checks validity.

        Parameters
        thr (float) - New value of threshold.

        Returns
        None
        """

        assert thr in range(2**7), "Incorrect threshold value ({}).".format(thr)
        self.thr = thr
    def resetConfig(self):
        """
        Set all PASTTREC settings inside this MDCTDC_PT object to the default value.

        Returns
        None

        """

        self.setBaselines([0x0f,0x0f,0x0f,0x0f,0x0f,0x0f,0x0f,0x0f])
        self.setGain(4)
        self.setPt(10)
        self.setThr(0x08)
    def getImage(self):
        """
        Create an image of current PASTTREC settings.

        Returns
        A dictionary, that represents the actual PASTTREC registers content corresponding to its settings. Keys are register addresses, values are actual content.

        Return type
        dict(int, int)

        """

        cmds = {
            0x0: (ConfStorage.defaultPtSettings["baseline_sel"] << 4) + (self.gain_map[self.gain] << 2) + self.pt_map[self.pt],
            0x1: (ConfStorage.defaultPtSettings["tc1_c"] << 3) + (ConfStorage.defaultPtSettings["tc1_r"]),
            0x2: (ConfStorage.defaultPtSettings["tc2_c"] << 3) + (ConfStorage.defaultPtSettings["tc2_r"]),
            0x3: (self.thr),
            0xD: ConfStorage.defaultPtSettings["lvds_dac"]
        }
        for i,ch in enumerate(self.baselines):
            cmds[i+4] = ch
        return cmds
    def applySCCmd(self, cmd):
        """
        Emulates the execution of slow control command on this virtual PASTTREC. Changes the settings according to the specified command. Only in write mode.

        Parameters
        cmd (int) - A slow control command, that should be applied. For details, see the PASTTREC documentation.

        Returns
        None
        """

        reg_no = (cmd & 0xF00) >> 8
        if reg_no == 0:
            raw_gain = (cmd & 12) >> 2
            raw_pt = (cmd & 3) 
            self.setGain([key for key in self.gain_map if self.gain_map[key] == raw_gain][0])
            self.setPt([key for key in self.pt_map if self.pt_map[key] == raw_pt][0])
        elif reg_no == 3:
            self.setThr(cmd & 0x7F)
        elif reg_no >= 0x4 and reg_no <= 0xB:
            self.setBaseline( reg_no - 4, cmd & 0x1F)
    def applyDefaultConfSet(self, conf_set):
        """
        The same as applySCCmd(), but allows performing a list of commands executions, one by one.

        Parameters
        cmd (list(int)) - A list of slow control commands, that should be applied. For details, see the PASTTREC documentation.

        Returns
        None
        """

        addr,len = conf_set["addr"], conf_set["len"]
        for i in range(len):
            command = ConfStorage.defaultPtMemory[addr + i]
            self.applySCCmd(command)
    def __str__(self):
        st = "gain: {}, pt: {}, thr: {}, baselines: {}".format(self.gain,self.pt,self.thr,self.baselines)
        return st

    @classmethod
    def read_configuration(cls, TDC_str, pasttrec):
        """
        Create an MDCTDC_PT object and set its settings to the same as in real PASTTREC with a specified TDC address. Useful for reading data back from PASTTREC.

        Parameters
        TDC_str (str) - An address of assosiated TDC.

        pasttrec (int) - A PASTTREC number [0-3].

        Returns
        An MDCTDC_PT object with the same settings as in one of real ASICs.

        Return type
        MDCTDC_PT
        """

        regs = pt.read_PASTTREC_regs(TDC_str=TDC_str, pasttrec=pasttrec)
        obj = cls()
        for reg_n, val in regs.items():
            obj.applySCCmd((int(reg_n, 16) << 8) + int(val, 16))
        return obj
        
class MDCTDC_FPGA: 
    """
    A class for handling all 4 PASTTREC configurations for every specific TDC.

    Attributes

    addr: str
    Address of this TDC

    pasttrec: list(MDCTDC_PT)
    An array of MDCTDC_PT objects.

    """
    def __init__(self, addr, pasttrec):
        """
        Constructor

        Parameters
        addr (str) - TDC address.

        pasttrec (list(MDCTDC_PT)) - Array of MDCTDC_PT objects.

        Returns
        The instance of MDCTDC_FPGA object.
        
        """

        self.addr = "0x{:04X}".format(int(addr,16))
        self.pasttrec = pasttrec
    def found_baseline(self, scanning_time = 0.2):
        """
        Found the baselines for all PASTTRECs of this TDC. The founded values are assigned only to the virtual PASTTRECs of this FPGA after scanning, but not to the real PASTTRECs.

        Parameters
        scanning_time (float) - Duration of each step during data acquisition.

        Returns
        None

        """

        baselines = pt.found_baselines_for_board(self.addr, scanning_time)
        rounded = []
        for ch in baselines:
            if "err" in baselines[ch]: 
                print("Error: noize {} for FPGA {} ch {}".format(baselines[ch]["err"],self.addr, ch))
                continue
            base = round(baselines[ch]["mean"])
            rounded.append(base + 15)#self.pasttrec[ch // 8].baselines[ch % 8] = base + 15
        for i,past in enumerate(self.pasttrec):
            past.setBaselines(rounded[i*8 : i*8+8])
    def getImage(self):
        """
        Generate a flashable image of this TDC.

        Returns
        The memory content of TDC for automatic applying of current virtual FPGA settings for real PASTTRECs during the power cycle. Keys are the addresses, values - corresponding content of each memory cell.

        Return type
        dict(int, int)

        """
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
        res = {**ConfStorage.defaultPtMemory, **cmdlist} 
        return res
    def resetConfig(self):
        """
        Set all settings of all associated virtual PASTTRECs to the default values.

        Returns
        None

        """
        for pasttrec in self.pasttrec:
            pasttrec.resetConfig()
    def __str__(self):
        st = "FPGA {}\n".format(self.addr)
        for i,past in enumerate(self.pasttrec):
            st += "\tPASTTREC {}: {}\n".format(i,past)
        return st
    def __getitem__(self,key):
        return self.pasttrec[key]

    @classmethod
    def read_configuration(cls,TDC_str):
        """
        Create an MDCTDC_FPGA object and set its settings to the same as in real PASTTRECs of specified TDC. Useful for reading data back from PASTTREC.

        Parameters
        TDC_str (str) - Address of real TDC, from which the settings should read back.

        Returns
        The instance of MDCTDC_FPGA, with the same settings as in real TDC.

        Return type
        MDCTDC_FPGA


        """
        past = [MDCTDC_PT.read_configuration(TDC_str=TDC_str, pasttrec=i) for i in range(4)]
        return cls(TDC_str, past)

class MDCTDC_OEP: 
    """
    A class for handling all the PASTTREC's configurations, associated with specific OEP.

        Attributes

        addr: str
        Address of this TDC

        fpga: list(MDCTDC_FPGA)
        An array of MDCTDC_FPGA objects.

    """
    def __contains__(self, item):
        return item in self.fpga #[fpga.addr for fpga in self.fpga]
    def __init__(self, addr, fpga):
        """
        Constructor

        Parameters
        addr (str) - A OEP address.

        fpga (list(MDCTDC_FPGA).) - Array of virtual connected MDCTDC_FPGA objects.

        Returns
        The instance of MDCTDC_FPGA object.
        
        """
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
    def resetConfig(self):
        """
        Set all settings of all associated PASTTRECs to the default values.

        Returns
        None

        """

        for fpga in self.fpga:
            self.fpga[fpga].resetConfig()
    