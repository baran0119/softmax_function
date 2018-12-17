import math, myhdl, os
from myhdl import *
from src.axis import Axis
from src.clk_gen import clk_gen


def bin2float(b):
    s, f = b.find('.')+1, int(b.replace('.', ''), 2)
    return f/2.**(len(b)-s) if s else f


@block
def mypower(clk, reset, x_n, x, n, done, enable):
    """
        Function compute sequentially:
            x_n = x ** n

        Doesn't support for x**0, because it is unnecessary in this implementation.

        inputs: clk, reset, x, n, enable
        outputs: x_n, done
    """

    accumulator = Signal(intbv(0)[64:])
    counter = Signal(intbv(1)[32:])  # begin with 1, because x**1 = x
    # print("accumulator=", bin(accumulator[:32], 32), ".", bin(accumulator[31:], 32))
    state_t = enum('COUNT', 'DONE')
    state = Signal(state_t.COUNT)

    @always_seq(clk.posedge, reset=reset)
    def process():
        if state == state_t.COUNT:
            if enable:
                if counter <= n:
                    done.next = False
                    if counter == 1:  # x**1 = x
                        accumulator.next = x
                    elif counter <= n - 1:
                        accumulator.next = (accumulator * x) >> 16
                    else:  # last iteration: without shifting, because is ready for 64-bits Q32.32 output
                        accumulator.next = (accumulator * x)
                    counter.next = counter + 1
                else:  # counter > n
                    state.next = state_t.DONE
                    counter.next = 1  # reset with 1, because x**1 = x
        elif state == state_t.DONE:
            done.next = True
            x_n.next = accumulator
            accumulator.next = 1
            state.next = state_t.COUNT
        else:
            raise ValueError("Undefined state")

    return instances()


@block
def myexp(clk, reset, exp_x, x, done, enable, M, f):
    """
        Function compute sequentially:
            exp(x) = sum ( x**n / n! ) from n to N
        Formula: Maclaurin series (for fixed-point x)
        32-bits x in Q-format: Q16.16
        see https://en.wikipedia.org/wiki/Q_(number_format)

              integer bits     fractional bits
             x x x ... x x x . x x x ... x x x
            |_____ ..._____|   |_____ ..._____|
            31            16   15             0

        During calculations is used double-precision (accumulator and mypower is 64-bits)

        inputs: clk(bool), reset(bool), x(32b), enable(bool), M(uint), F(uint)
        outputs: exp_x(32b), done(bool)
    """

    # tuple with factorial
    fact = tuple([math.factorial(i) for i in range(M+1)])

    state_t = enum('COUNT', 'DONE')
    state = Signal(state_t.COUNT)

    accumulator = Signal(intbv(0)[64:])
    counter = Signal(intbv(0)[32:])

    x_n = Signal(intbv(0)[64:])
    done_power, enable_power = [Signal(bool(False)) for i in range(2)]
    power_instance = mypower(clk, reset, x_n, x, counter, done_power, enable_power)

    @always_seq(clk.posedge, reset=reset)
    def process():
        if state == state_t.COUNT:
            if enable:
                done.next = False
                if counter <= M:

                    # simplify for counter= 0 and 1, because exp(x) = 1 + x for n = {0,1} (see Maclaurin series)
                    if counter == 0:
                        accumulator.next = (1 << (2*f))
                        counter.next = counter + 1
                    elif counter == 1:
                        accumulator.next = accumulator + (x << f)
                        counter.next = counter + 1

                    else:  # counter >= 2:
                        enable_power.next = True  # turn on mypower block
                        if done_power:            # and wait for it
                            enable_power.next = False
                            accumulator.next = accumulator + ((x_n // (fact[counter] << f)) << 16)
                            counter.next = counter + 1

                else:  # counter > M
                    state.next = state_t.DONE
                    counter.next = 0

        elif state == state_t.DONE:
            done.next = 1
            exp_x.next = accumulator[48:16]  # output is 32-bits
            accumulator.next = 0
            state.next = state_t.COUNT
        else:
            raise ValueError("Undefined state")

    return instances()


@block
def softmax(clk, reset, out_vector, in_vector, n, done, enable, M=16, f=16):
#def softmax(clk, reset, out_list, in_list, n, done, enable, M=16, f=16):
    """
        Function compute softmax function:
        see https://en.wikipedia.org/wiki/Softmax_function

        32-bits in Q-format: Q16.16
        see https://en.wikipedia.org/wiki/Q_(number_format)

              integer bits     fractional bits
             x x x ... x x x . x x x ... x x x
            |_____ ..._____|   |_____ ..._____|
            31            16   15             0

        During calculations is used double-precision (64-bits)

        inputs: clk(bool), reset(bool), ..., enable(bool), M(uint), f(uint)
        outputs: ..., done(bool)

        ---> List of signals as a port is not supported
    """

    b = 32

    state_t = enum('COUNT', 'DONE')
    state = Signal(state_t.COUNT)

    accumulator = Signal(intbv(0)[32:])
    counter = Signal(intbv(0)[32:])
    counter2 = Signal(intbv(0)[32:])

    exp_list = [Signal(intbv(0)[32:]) for i in range(n)]
    temp = [Signal(intbv(0)[64:]) for i in range(n)]
    in_list = [Signal(intbv(0)[32:]) for i in range(n)]
    out_list = [Signal(intbv(0)[32:]) for i in range(n)]
    done_exp = [Signal(bool(False)) for i in range(n)]
    enable_exp = [Signal(bool(False)) for i in range(n)]
    exp_instance = [None for i in range(n)]

    for i in range(n):
        in_list[i] = in_vector((i+1)*b-1, i*b)  # slicing
        exp_instance[i] = myexp(clk, reset, exp_list[i], in_list[i], done_exp[i], enable_exp[i], M, f)


    # W = b*N
    # # ind = tuple([(i+1)*b-1, i*b for i in range(W,0,-b)])
    #
    # left_i = tuple([i-1 for i in range(W,0,-b)])
    # right_i =  tuple([i-b for i in range(W,0,-b)])
    #
    # print(left_i)
    # print(right_i)

    @always_seq(clk.posedge, reset=reset)
    def process():
        if state == state_t.COUNT:
            if enable:
                done.next = False
                enable_exp[0].next = True
                if counter <= n+1:
                    if done_exp[0]:
                        enable_exp[0].next = False
                        accumulator.next = accumulator + exp_list[0]
                        counter.next = counter + 1
                        enable_exp[1].next = True
                    if done_exp[1]:
                        # print("exp_list[0]=", bin(exp_list[0][:16], 16), ".", bin(exp_list[0][16:], 16))
                        print("exp_list[0]=", bin2float(str(bin(exp_list[0][:16], 16)) + "." + str(bin(exp_list[0][16:], 16))))
                        # print("accumulator=", bin(accumulator, 32))
                        enable_exp[1].next = False
                        accumulator.next = accumulator + exp_list[1]
                        counter.next = counter + 1
                        enable_exp[2].next = True
                    if done_exp[2]:
                        # print("exp_list[1]=", bin(exp_list[1][:16], 16), ".", bin(exp_list[1][16:], 16))
                        print("exp_list[1]=", bin2float(str(bin(exp_list[1][:16], 16)) + "." + str(bin(exp_list[1][16:], 16))))
                        # print("accumulator=", bin(accumulator, 32))
                        enable_exp[2].next = False
                        accumulator.next = accumulator + exp_list[2]
                        counter.next = counter + 1
                else:
                    # print("exp_list[2]=", bin(exp_list[2][:16], 16), ".", bin(exp_list[2][16:], 16))
                    print("exp_list[2]=", bin2float(str(bin(exp_list[2][:16], 16)) + "." + str(bin(exp_list[2][16:], 16))))
                    # print("accumulator=", bin(accumulator[:16], 16), ".", bin(accumulator[15:], 16))
                    print("accumulator=", bin2float(str(bin(accumulator[:16], 16)) + "." + str(bin(accumulator[16:], 16))))

                    temp[0].next = ((exp_list[0] << 16) // accumulator) << 16
                    temp[1].next = ((exp_list[1] << 16) // accumulator) << 16
                    temp[2].next = ((exp_list[2] << 16) // accumulator) << 16


                # I can't use counter as index for lists - Error: list index out of range
                # so i decided to do it manually like above
                # if counter <= n:
                #     enable_exp[int(counter)].next = True
                #     if done_exp[int(counter)]:
                #         enable_exp[int(counter)].next = False
                #         accumulator.next = accumulator + exp_list[int(counter)]
                #         counter.next = counter + 1
                # else:  # counter > n
                #     if counter2 <= n:
                #         temp[int(counter2)].next = exp_list[int(counter2)] << f
                #         temp[int(counter2)].next = (temp[int(counter2)] // accumulator) << f
                #         out_list[int(counter2)].next = temp[48:16]
                #         counter2.next = counter2 + 1
                #     else:
                #         counter2.next = 0

                    state.next = state_t.DONE
                    counter.next = 0

        elif state == state_t.DONE:
            done.next = True
            print("done")
            # print("temp[0]=", bin(temp[0], 64))
            # print("temp[1]=", bin(temp[1], 64))
            # print("temp[2]=", bin(temp[2], 64))
            # print("exp_list[0]=", bin(exp_list[0], b))
            # print("exp_list[1]=", bin(exp_list[1], b))
            # print("exp_list[2]=", bin(exp_list[2], b))
            print("temp[0]=", bin2float(str(bin(temp[0][:32], 32)) + "." + str(bin(temp[0][32:0], 32))))
            print("temp[1]=", bin2float(str(bin(temp[1][:32], 32)) + "." + str(bin(temp[1][32:0], 32))))
            print("temp[2]=", bin2float(str(bin(temp[2][:32], 32)) + "." + str(bin(temp[2][32:0], 32))))

            out_list[0].next = temp[0][48:16]
            out_list[1].next = temp[1][48:16]
            out_list[2].next = temp[2][48:16]

            # last step - for some reason, doesn't work
            out_vector.next = ConcatSignal(*out_list)

            accumulator.next = 0
            state.next = state_t.COUNT
        else:
            raise ValueError("Undefined state")

    return instances()


# Testbench

@block
def test_softmax(vhdl_output_path=None):

    # axis_y = Axis(32)
    # axis_x = Axis(32)

    n = 3
    b = 32
    f = 16

    in_list = [Signal(intbv(1 << f)[b:]), Signal(intbv(2 << f)[b:]), Signal(intbv(3 << f)[b:])]
    in_vector = ConcatSignal(*reversed(in_list))

    done, enable = [Signal(bool(False)) for i in range(2)]

    out_vector = Signal(intbv(0)[b*n:])

    clk = Signal(bool(False))
    clk_gen_instance = clk_gen(clk, period=10)
    reset = ResetSignal(0, active=1, async=False)

    softmax_instance = softmax(clk, reset, out_vector, in_vector, n, done, enable, M=16, f=16)

    @instance
    def reset_gen():
        reset.next = 0
        yield delay(7000)
        yield clk.negedge
        reset.next = 1


    @instance
    def stimulus():
        enable.next = True
        yield delay(10000)
        print(bin(out_vector, n * b))
        raise StopSimulation()

    if vhdl_output_path is not None:
        softmax_instance.convert(hdl='VHDL', path=vhdl_output_path)

    return instances()


if __name__ == '__main__':
    trace_save_path = './out/testbench/'
    vhdl_output_path = './out/vhdl/'
    os.makedirs(os.path.dirname(trace_save_path), exist_ok=True)
    os.makedirs(os.path.dirname(vhdl_output_path), exist_ok=True)

    # tb = test_softmax(vhdl_output_path)
    tb = test_softmax()
    tb.config_sim(trace=True, directory=trace_save_path, name='softmax_tb')
    tb.run_sim()

