from cocotb.binary import BinaryValue
from cocotb.handle import Force

from cocotb.handle import NonHierarchyIndexableObject

from injector_base import InjectorBase

from functools import reduce

from cocotb.simulator import *


class CocotbInjector(InjectorBase):
    def __init__(self, dut, prefix=""):
        self.coco_dut = dut
        self.prefix = prefix        # 前缀
        self.error_signals = []     # 错误信号

        super().__init__()

    # 去除前缀prefix
    def remove_prefix(self, str, prefix):       
        if str.startswith(prefix):      # 如果前缀为prefix
            return str[len(prefix):]    # 返回去除前缀后的字符串
        return str  # or whatever       # 如果前缀不为prefix，直接返回

    # 通过波形文件中的信号名，从cocotb的dut顶层层层向下，得到对应的信号实例
    def get_cocotb_sig(self, sig_name):
        # reduce(function, iterable[, initializer])
        # function -- 函数，有两个参数; iterable -- 可迭代对象;  initializer -- 可选，初始参数
        # 函数将一个数据集合（链表，元组等）中的所有数据进行下列操作：
        
        # reduce的工作过程是 ：在迭代sequence(tuple ，list ，dictionary， string等可迭代物)的过程中，
        # 首先把 前两个元素传给 函数参数，函数加工后，然后把得到的结果和第三个元素作为两个参数传给函数参数， 
        # 函数加工后得到的结果又和第四个元素作为两个参数传给函数参数，依次类推。 
        # 如果传入了 initial 值， 那么首先传的就不是 sequence 的第一个和第二个元素，而是 initial值和 第一个元素。经过这样的累计计算之后合并序列到一个单一返回值
        # getattr() 函数用于返回一个对象属性值。
        # self.remove_prefix(sig_name, self.prefix).split('.')[1:]为列表，存放该信号与顶层之间的每一个模块名
         return reduce(getattr, self.remove_prefix(sig_name, self.prefix).split('.')[1:], self.coco_dut)

    # 注入信号值
    # values为字典{'信号':'值',...}--存放仿真时刻sim_time时各信号量的值
    def inject_values(self, values):
        for sig_name, value in values.items():
            # structs/arrays injection not supported yet.
            # print(sig_name, value)
            if value is None:
                continue

            if '{' in value:
                print("skipping hier signal?: ", sig_name)
                continue

            if sig_name in self.error_signals:  # 为错误信号
                continue

            # 得到cocotb中对应的信号实例
            coco_sig = self.get_cocotb_sig(sig_name)

            bin_value = BinaryValue(value)
    
            try:
                # coco_sig <= Force(bin_value)
                coco_sig.value = bin_value
                sim_time = get_sim_time()[1]
                # print(sim_time)
                # if sim_time == 115000 or sim_time == 120000 or sim_time == 125000 or sim_time == 130000:
                #     self.coco_dut._log.info("%s :%s data :%s", sim_time, sig_name, bin_value)
            except ValueError:
                print("Value error. The values requested to inject are: ", values)
            except TypeError:
                self.error_signals.append(sig_name)
                print("Type error. Signal name is: ", sig_name, " sig value: ", value)