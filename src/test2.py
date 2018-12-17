import math
import myhdl
from myhdl import *


def bin2float (b):
    s, f = b.find('.')+1, int(b.replace('.',''), 2)
    return f/2.**(len(b)-s) if s else f

#
# n = 3
# b = 32
# f = 16
#
# in_list = [Signal(intbv(1 << f)[b:]), Signal(intbv(2 << f)[b:]), Signal(intbv(3 << f)[b:])]
# # in_list = [Signal(intbv(0)[b:]) for i in range(n)]
#
# # in_list[0] = 1 << f
# # in_list[1] = 2 << f
# # in_list[2] = 3 << f
#
# for i in range(n):
#     print(bin(in_list[i], b))
#
#
# in_vector = ConcatSignal(*in_list)
# print(bin(in_vector, n*b))


# accumulator = Signal(intbv(0b00000000001000110010000100010001)[32:])
# temp = Signal(intbv(0b0000000000000000000000000001010000010101110111110000000000000000)[64:])
# temp2 = Signal(intbv(0)[64:])
#
# temp2 = (temp // accumulator) << 16
#
#
# print("accumulator=", bin(accumulator[:16], 16), ".", bin(accumulator[15:], 16))
# print("accumulator=", bin2float(str(bin(accumulator[:16], 16)) + "." + str(bin(accumulator[16:], 16))))
# print("temp=", bin(temp[:32], 32), ".", bin(temp[32:], 32))
# print("temp=", bin2float(str(bin(temp[:32], 32)) + "." + str(bin(temp[32:], 32))))
#
# print("temp2=", bin(temp2, 32))

#print("temp2=", bin(temp2[:32], 32), ".", bin(temp2[31:], 32))
#print("temp2=", bin2float(str(bin(temp2[:32], 32)) + "." + str(bin(temp2[31:], 32))))


x = Signal(intbv(0b1001100110011001)[32:])

print("x=", bin(x[12:4], 8))

