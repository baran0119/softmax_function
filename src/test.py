# from softmax import Top

import math
import myhdl

#N = 4  # liczba elementow wektora
#b = 32 # bitow na slowo
#F = 2 ** 8


# in_lista = [Signal(intbv(0)[b:]) for i in range(N)]
# for i in range(N):
#     print(bin(in_lista[i], b))
#
# in_vector = ConcatSignal(*reversed(in_lista))
# print(bin(in_vector, N*b))
#
# #out_vector = Signal(intbv(0)[N:])
# # print(out_vector)
# out_vector = Signal(intbv(0)[N*b:])
# print(bin(out_vector, N*b))
# out_lista = [0 for i in range(N)]
# for i in range(N):
#     out_lista[i] = out_vector((i+1)*b-1, i*b)  # slicing
#
# for i in range(N):
#     print(bin(out_lista[i], b))

# testVector = []
# testVector.extend(random.randint(0,10) for i in range(N))
# for i in range(N):
#     print(str(i)+':')
#     print(testVector[i])
#     print(bin(testVector[i], b))
#     # print(F*testVector[i])
#     # print(bin(F*testVector[i], b))
#     # print(math.exp(F*testVector[i]))
#     # print(bin(math.exp(F*testVector[i]), b))
#     print(math.exp(testVector[i]))
#     print(bin(math.exp(testVector[i]), b))


# silnia = tuple([math.factorial(i) for i in range(N)])
# for i in range(N):
# #     print(str(i)+':')

# W = b*N
# # ind = tuple([(i+1)*b-1, i*b for i in range(W,0,-b)])
#
# left_i = tuple([i-1 for i in range(W,0,-b)])
# right_i =  tuple([i-b for i in range(W,0,-b)])
#
# print(left_i)
# print(right_i)

def softmax2(v, N):
    ret = [0 for i in range(N)]
    suma = 0
    for i in range(N):
        ret[i] = math.exp(v[i])
        suma += ret[i]
    return [i / suma for i in ret]
#
#
# def myexp(x, N):
#     ret = 1 + x
#     for n in range(2, N):
#         ret = ret + (x**n / math.factorial(n))
#     return ret
#
a = [1, 2, 3]
N = len(a)
# x = 2
# b = myexp(x, N=5)
b = softmax2(a, N)

# y0 = math.exp(x)
print(b)
# print(myhdl.bin(b, 32))
# print(y0)
# print(abs(y0-b))

print([round(i, 3) for i in b])
