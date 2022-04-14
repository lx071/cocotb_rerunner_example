# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0
import os


def nameChange(data, oldName, newName):
    # self.signal_values
    # 字典{'信号':[(时间,'值'),...],...}
    signal_values = data.signal_values
    # dict["c"] = dict.pop("a")
    if oldName in signal_values and newName not in signal_values:
        signal_values[newName] = signal_values.pop(oldName)
        vcd_name = data.sig_name_2_vcd_name[oldName]
        data.sig_name_2_vcd_name[newName] = data.sig_name_2_vcd_name.pop(oldName)
        data.vcd_name_2_sig_name[vcd_name] = newName
    elif oldName not in signal_values:
        print('oldName not exists')
        return
    elif newName in signal_values:
        print('newName already exists')
        return

    data.signal_values = signal_values
    data.countIO()


def andLogic(data, signal1, signal2, newSignal):
    pass


def orLogic(data, signal1, signal2, newSignal):
    pass


def notLogic(data, signal1, signal2, newSignal):
    pass


# 该类测试从wave文件中读取出数据结构
def test_empty():
    """ doesn't do anything. workaround for COCOTB_SIM define not working? """
    print("starting replay")

    from vcd_reader import VcdReader
    replay_block = []
    wavefile = "../mcdt.vcd"
    excluded_sigs = []
    inputs_only = True
    data = VcdReader(replay_block, wavefile, excluded_sigs, inputs_only)

    print(data.signal_values)
    print()
    print(data.sig_name_2_vcd_name)
    print()
    print(data.vcd_name_2_sig_name)
    print()

    nameChange(data, 'mcdt.ch0_data_i', 'ch0_data_i')
    andLogic(data)
    print(data.signal_values)
    print()
    print(data.sig_name_2_vcd_name)
    print()
    print(data.vcd_name_2_sig_name)
    print()



