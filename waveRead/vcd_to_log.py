# -*- coding: utf-8 -*-
# 转换规则
# 事件名   表达式（触发条件）
# "name" : {expression}
# "adder output fire" : {adder.io.out.valid && adder.io.out.ready}

# 根据转换规则，从波形中提取信息Log
# 输入：一个波形文件，一个转换规则描述文档
# 输出：从波形中提取的Log


import os
from waveRead.vcd_reader import VcdReader


# 读取规则
def getRules(filename):
    rules = {}
    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip('\n')
            eventName, expression = line.split(':')
            eventName = eventName.strip()[1:-1]     # 去除首尾字符
            expression = expression.strip()
            print(eventName, expression)
            rules[eventName] = expression
    return rules


# 从波形文件中读取数据结构 VcdReader
def getData(wavefile):
    replay_block = []
    # wavefile = "../mcdt.vcd"
    excluded_sigs = []
    inputs_only = False
    data = VcdReader(replay_block, wavefile, excluded_sigs, inputs_only)
    # print(data.signal_values)
    return data


# 求出在仿真时间为sim_time时的expression的值    是否为 1
def getValue(data, sim_time, expression):
    # values为字典{'信号':'值',...}--存放仿真时刻sim_time时各信号量的值
    values = data.get_values_at(sim_time)
    # 按照True的情况进行判断
    if expression.find('&&') == -1 and expression.find('||') == -1:
        if expression[0] == '!':
            return values[expression[1:]] == '0'
        else:
            return values[expression] == '1'
    elif expression.find('&&') != -1:
        left, right = expression.split('&&')
        left = left.strip()
        right = right.strip()
        k = 0
        if left[0] == '!':
            if values[left[1:]] == '0':
                k = k + 1
        else:
            if values[left] == '1':
                k = k + 1
        if right[0] == '!':
            if values[right[1:]] == '0':
                k = k + 1
        else:
            if values[right] == '1':
                k = k + 1
        if k == 2:
            return True
        else:
            return False

    elif expression.find('||') != -1:
        left, right = expression.split('||')
        left = left.strip()
        right = right.strip()
        if left[0] == '!':
            if values[left[1:]] == '0':
                return True
        else:
            if values[left] == '1':
                return True
        if right[0] == '!':
            if values[right[1:]] == '0':
                return True
        else:
            if values[right] == '1':
                return True
        return False


def writeTxT(f, txt):
    f.write(txt)  # 自带文件关闭功能，不需要再写f.close()
    f.write('\n')
    pass


# 根据转换规则，从波形中提取信息Log
# 规则表达式仅允许操作符&& || not，最多两个变量（一个位）
def vcd2log(rulesfile, wavefile, logfile):
    # 读取规则
    rules = getRules(rulesfile)

    # 从规则（字典）中提取事件名和对应的表达式
    eventNames = list(rules.keys())
    expressions = []
    for eventName in eventNames:
        expressions.append(rules[eventName])

    # 从波形文件中读取数据结构 VcdReader
    # wavefile = "../mcdt.vcd"
    data = getData(wavefile)

    # 字典{'信号': [(时间, '值'), ...], ...}
    # data.signal_values

    # 按照规则分析data，将结果存入result.txt
    with open(logfile, "w") as f:
        sim_time = 0
        while True:
            for i in range(len(eventNames)):
                event = getValue(data, sim_time, expressions[i])
                # print(value)
                if event:
                    txt = str(sim_time) + ' ' + eventNames[i]
                    # print(sim_time, eventNames[i])
                    writeTxT(f, txt)

            previous_time = sim_time
            # 得到仿真时刻sim_time后的一个变化时刻，若无则返回None
            sim_time = data.get_next_event(sim_time)
            if sim_time is None:
                break


rulesfile = "rules.txt"
wavefile = "../mcdt.vcd"
logfile = "result.txt"

# 根据转换规则，从波形中提取信息Log
vcd2log(rulesfile, wavefile, logfile)
# rules = {'clk': 'mcdt.inst_slva_fifo_2.clk_i',
#          'rstn': 'mcdt.inst_slva_fifo_2.rstn_i'}

