# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0
import os

import cocotb

from cocotb.triggers import Timer

from reader import read_wave

from cocotb_injector import CocotbInjector


@cocotb.test()
async def test_empty(dut):
    """ doesn't do anything. workaround for COCOTB_SIM define not working? """
    print("starting replay")
    
    # read_wave(wavefile, replay_block, inputs_only, excluded_sigs)
    replay_block = []
    wavefile = "../mcdt.vcd"
    excluded_sigs = []
    inputs_only = True
    data = read_wave(wavefile, replay_block, inputs_only, excluded_sigs)        # VcdReader对象
    print(data.signal_values)
    
    injector = CocotbInjector(dut)                                              # CocotbInjector对象

    sim_time = 0

    while True:
        # values为字典{'信号':'值',...}--存放仿真时刻sim_time时各信号量的值
        values = data.get_values_at(sim_time)   
        # if sim_time == 115000 or sim_time == 120000 or sim_time == 125000:
        #    print(sim_time)
        #    print(values)
        # 注入当前仿真时刻的信号与值
        injector.inject_values(values)
        
        previous_time = sim_time
        # 得到仿真时刻sim_time后的一个变化时刻，若无则返回None
        sim_time = data.get_next_event(sim_time)    
        
        if sim_time is None:
            break
        await Timer(sim_time - previous_time)