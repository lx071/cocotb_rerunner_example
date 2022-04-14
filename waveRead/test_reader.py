# move to pytest
from .reader_base import ReaderBase


# import pytest
# 该类仅测试ReaderBase类和test_get_next_event()和test_get_values_at()
class MockReader(ReaderBase):
    def __init__(self, replay_block, wave_file, excluded_sigs, inputs_only):
        super().__init__(replay_block, wave_file, excluded_sigs, inputs_only)

    # 从波形中读取数据，得到字典{'信号':[(时间,'值'),...],...}
    def extract_values_from_wave(self, replay_block, excluded_sigs, inputs_only):
        return {'top.block_i.clk': [(0, '0'), (10, '1'), (20, '0')], 'top.block_i.din': [(0, 'X'), (20, '0'), (40, '1')]}


def test_get_next_event():
    data = MockReader("fake", "fake", [], False)

    next_time = data.get_next_event(5)
    assert next_time == 10

    next_time = data.get_next_event(20)
    assert next_time == 40

    next_time = data.get_next_event(40)
    assert next_time is None


def test_get_values_at():
    # 得到Reader，有属性excluded_sigs、inputs_only、signal_values、signal_changes、replay_blocks
    # excluded_sigs     包含的信号[]
    # inputs_only       False
    # signal_values     信号值 {'top.block_i.clk': [(0, '0'), (10, '1'), (20, '0')], 'top.block_i.din': [(0, 'X'), (20, '0'), (40, '1')]}
    # signal_changes    信号发生变化时间[0,10,20,40]
    # replay_blocks     ['fake']
    data = MockReader("fake", "fake", [], False)    

    # 得到仿真时刻10的各信号值
    # {'top.block_i.clk': '1', 'top.block_i.din': 'X'}
    signal_values = data.get_values_at(10)  

    assert signal_values['top.block_i.din'] == 'X'  # 断言判断信号值