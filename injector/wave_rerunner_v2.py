# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# test_my_design.py (extended)

# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# test_my_design.py (extended)

import os
from reader import read_wave
from cocotb_injector import CocotbInjector
import cocotb
from cocotb.triggers import Timer
from cocotb.triggers import FallingEdge, RisingEdge
from queue import Queue
from cocotb.simulator import *


class chnl_intf:
    def __init__(self, dut, ch_id):
        self.clk = dut.clk_i
        self.rstn = dut.rstn_i
        if ch_id == 0:
            self.chnl_data = dut.ch0_data_i
            self.ch_valid = dut.ch0_valid_i
            self.ch_ready = dut.ch0_ready_o
            self.ch_margin = dut.ch0_margin_o

        elif ch_id == 1:
            self.chnl_data = dut.ch1_data_i
            self.ch_valid = dut.ch1_valid_i
            self.ch_ready = dut.ch1_ready_o
            self.ch_margin = dut.ch1_margin_o

        elif ch_id == 2:
            self.chnl_data = dut.ch2_data_i
            self.ch_valid = dut.ch2_valid_i
            self.ch_ready = dut.ch2_ready_o
            self.ch_margin = dut.ch2_margin_o


class mcdt_intf:
    def __init__(self, dut):
        self.clk = dut.clk_i
        self.rst = dut.rstn_i
        self.mcdt_data = dut.mcdt_data_o
        self.mcdt_val = dut.mcdt_val_o
        self.mcdt_id = dut.mcdt_id_o


class chnl_trans:
    def __init__(self, ch_id, pkt_id):
        self.ch_id = ch_id
        self.pkt_id = pkt_id
        self.data_nidles = 0
        self.pkt_nidles = 1
        self.data_size = 10

        data = [1] * self.data_size
        for i in range(len(data)):
            data[i] = 0xC000_0000 + (self.ch_id << 24) + (self.pkt_id << 8) + i;
        self.data = data

    def set_pkt_id(self, pkt_id):
        self.pkt_id = pkt_id
        data = [1] * self.data_size
        for i in range(len(data)):
            data[i] = 0xC000_0000 + (self.ch_id << 24) + (self.pkt_id << 8) + i;
        self.data = data

    def set_data_nidles(self, data_nidles):
        self.data_nidles = data_nidles

    def set_pkt_nidles(self, pkt_nidles):
        self.pkt_nidles = pkt_nidles


class generator:
    def __init__(self):
        self.req_mb = Queue()

    def send_trans(self, ch_id):
        t = chnl_trans(ch_id, 0)
        self.req_mb.put(t)


class driver:
    def __init__(self, ch_id, name):
        self.ch_id = ch_id
        self.name = name
        self.req_mb = Queue()

    async def run(self):
        intf = self.intf
        await RisingEdge(intf.rstn)
        while True:
            await RisingEdge(intf.clk)
            if self.req_mb.empty() is False:
                t = self.req_mb.get_nowait()
                await cocotb.start(self.chnl_write(t))

    async def chnl_write(self, t):
        intf = self.intf
        num = len(t.data)
        for i in range(num):
            await RisingEdge(intf.clk)
            time_ns = get_sim_time()

            intf.ch_valid.value = 1
            intf.chnl_data.value = t.data[i]
            cocotb.log.info("%s %s drivered channle data %8x", time_ns, self.name, t.data[i])
            await FallingEdge(intf.clk)
            while intf.ch_ready.value != 1:
                await RisingEdge(intf.clk)

            for i in range(t.data_nidles):
                await self.chnl_idle(t)
        for i in range(t.pkt_nidles):
            await self.chnl_idle(t)

    async def chnl_idle(self, t):
        intf = self.intf
        await RisingEdge(intf.clk)

        intf.ch_valid.value = 0
        intf.chnl_data.value = 0

    def set_interface(self, intf):
        self.intf = intf


class mon_data_t:
    def __init__(self):
        self.data = 0
        self.data_id = 0


class chnl_monitor:
    def __init__(self, ch_id, name="chnl_monitor"):
        self.ch_id = ch_id
        self.name = name
        self.mon_mb = Queue()

    async def run(self):
        await self.mon_trans()

    async def mon_trans(self):
        intf = self.intf
        while True:
            m = mon_data_t()
            await RisingEdge(intf.clk)

            while str(intf.ch_valid.value) != '1' or str(intf.ch_ready.value) != '1':
                await RisingEdge(intf.clk)
            m.data = intf.chnl_data.value

            self.mon_mb.put(m)

            time_ns = get_sim_time()
            cocotb.log.info("%s %s monitored channle data %8x", time_ns, self.name, m.data)

    def set_interface(self, intf):
        self.intf = intf


class mcdt_monitor:
    def __init__(self, name="mcdt_monitor"):
        self.name = name
        self.mon_mb = Queue()

    async def run(self):
        await self.mon_trans()

    async def mon_trans(self):
        intf = self.intf
        while True:
            m = mon_data_t()
            await RisingEdge(intf.clk)
            while (intf.mcdt_val.value != 1):
                await RisingEdge(intf.clk)

            m.data = intf.mcdt_data.value
            m.data_id = intf.mcdt_id.value

            self.mon_mb.put(m)
            time_ns = get_sim_time()
            cocotb.log.info("%s %s monitored mcdt data %8x and id %0d", time_ns, self.name, m.data, m.data_id)

    def set_interface(self, intf):
        self.intf = intf


class chnl_agent:
    def __init__(self, ch_id, chnl_driver_name="chnl_driver0", chnl_monitor_name="chnl_monitor", name="chnl_agent"):
        self.name = name
        self.driver = driver(ch_id, chnl_driver_name)
        self.monitor = chnl_monitor(ch_id, chnl_monitor_name)

    async def run(self):
        await cocotb.start(self.driver.run())
        await cocotb.start(self.monitor.run())

    def set_interface(self, vif):
        self.vif = vif
        self.driver.set_interface(vif)
        self.monitor.set_interface(vif)


class chnl_checker:
    def __init__(self, name="chnl_checker"):
        self.name = name
        self.error_count = 0
        self.cmp_count = 0
        self.in_mbs = [Queue(), Queue(), Queue()]
        self.out_mb = Queue()

    async def run(self, clk):
        await self.do_compare(clk)

    async def do_compare(self, clk):
        im = mon_data_t()
        om = mon_data_t()
        while True:
            while self.out_mb.empty():
                await RisingEdge(clk)
            om = self.out_mb.get()
            if om.data_id == 0 or om.data_id == 1 or om.data_id == 2:
                while self.in_mbs[om.data_id].empty():
                    await RisingEdge(clk)
                im = self.in_mbs[om.data_id].get()
            else:
                cocotb.log.info("id %0d is not available", om.data_id)

            if om.data != im.data:
                self.error_count = self.error_count + 1
                cocotb.log.info(
                    "[CMPFAIL] Compared failed! mcdt out data %8x ch_id %0d is not equal with channel in data %8x",
                    om.data, om.data_id, im.data)
            else:
                cocotb.log.info(
                    "[CMPSUCD] Compared succeeded! mcdt out data %8x ch_id %0d is equal with channel in data %8x",
                    om.data, om.data_id, im.data)

            self.cmp_count = self.cmp_count + 1


class chnl_root_test:
    def __init__(self, name="chnl_root_test"):
        self.name = name
        self.agents = [chnl_agent(0, "chnl_driver0", "chnl_monitor0", "chnl_agent0"),
                       chnl_agent(1, "chnl_driver1", "chnl_monitor1", "chnl_agent1"),
                       chnl_agent(2, "chnl_driver2", "chnl_monitor2", "chnl_agent2")]
        self.mcdt_mon = mcdt_monitor()
        self.chker = chnl_checker()
        self.generators = [generator(), generator(), generator()]
        for i in range(3):
            self.agents[i].monitor.mon_mb = self.chker.in_mbs[i]
            self.agents[i].driver.req_mb = self.generators[i].req_mb
        self.mcdt_mon.mon_mb = self.chker.out_mb

    async def run(self, clk):
        for agent in self.agents:
            await cocotb.start(agent.run())
        await cocotb.start(self.mcdt_mon.run())
        await cocotb.start(self.chker.run(clk))

        # for i in range(3):
        #     self.generators[i].send_trans(i)

        cocotb.log.info("%s instantiated and connected objects", self.name)

    def set_interface(self, ch0_vif, ch1_vif, ch2_vif, mcdt_vif):
        self.agents[0].set_interface(ch0_vif)
        self.agents[1].set_interface(ch1_vif)
        self.agents[2].set_interface(ch2_vif)
        self.mcdt_mon.set_interface(mcdt_vif)


@cocotb.test()
async def test_empty(dut):
    chnl0_if = chnl_intf(dut, 0)
    chnl1_if = chnl_intf(dut, 1)
    chnl2_if = chnl_intf(dut, 2)
    mcdt_if = mcdt_intf(dut)

    # await cocotb.start(generate_clock(dut))  # run the clock "in the background"
    # await cocotb.start(generate_rst(dut))  # run the clock "in the background"

    test = chnl_root_test()
    test.set_interface(chnl0_if, chnl1_if, chnl2_if, mcdt_if)
    await cocotb.start(test.run(dut.clk_i))

    cocotb.log.info("***************** finished********************")

    """ doesn't do anything. workaround for COCOTB_SIM define not working? """
    print("starting replay")

    replay_block = []
    wavefile = "../mcdt.vcd"
    excluded_sigs = []
    inputs_only = False
    data = read_wave(wavefile, replay_block, inputs_only, excluded_sigs)        # VcdReader对象
    print(data.signal_values)
    
    injector = CocotbInjector(dut)                                              # CocotbInjector对象

    sim_time = 0

    while True:
        # values为字典{'信号':'值',...}--存放仿真时刻sim_time时各信号量的值
        values = data.get_values_at(sim_time)   

        # 注入当前仿真时刻的信号与值
        injector.inject_values(values)
        
        previous_time = sim_time
        # 得到仿真时刻sim_time后的一个变化时刻，若无则返回None
        sim_time = data.get_next_event(sim_time)    
        
        if sim_time is None:
            break
        await Timer(sim_time - previous_time)