import math, myhdl, os
from myhdl import *
from src.axis import Axis
from src.clk_gen import clk_gen


# tuple with factorial
fact = [math.factorial(i) for i in range(20)]


# def bin2float(b):
#     s, f = b.find('.')+1, int(b.replace('.', ''), 2)
#     return f/2.**(len(b)-s) if s else f


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

    state_t = enum('COUNT', 'DONE')
    state = Signal(state_t.COUNT)

    accumulator = Signal(intbv(0)[64:])
    counter = Signal(intbv(0)[32:])
    fact_sig = [Signal(intbv(fact_val)[32:]) for fact_val in fact]
    for i in range(len(fact_sig)):
        fact_sig[i].driven = True
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
                            accumulator.next = accumulator + ((x_n // (fact_sig[counter] << f)) << f)
                            counter.next = counter + 1

                else:  # counter > M
                    state.next = state_t.DONE
                    counter.next = 0

        elif state == state_t.DONE:
            done.next = 1
            exp_x.next = accumulator[3*f:f]  # output is 32-bits
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

    accumulator = Signal(intbv(0)[b:])
    counter = Signal(intbv(0)[b:])
    counter2 = Signal(intbv(0)[b:])

    exp_list = [Signal(intbv(0)[b:]) for i in range(n)]
    temp = [Signal(intbv(0)[2*b:]) for i in range(n)]
    # temp_done = Signal(bool(False))

    in_list = [Signal(intbv(0)[b:]) for i in range(n)]
    out_list = [Signal(intbv(0)[b:]) for i in range(n)]
    done_exp = [Signal(bool(False)) for i in range(n)]
    enable_exp = [Signal(bool(False)) for i in range(n)]
    exp_instance = [None for i in range(n)]
    out_vector_c = Signal(intbv()[len(out_vector):])

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
                if counter < n:
                    enable_exp[counter].next = True
                    if done_exp[counter]:
                        enable_exp[counter].next = False
                        accumulator.next = accumulator + exp_list[counter]
                        counter.next = counter + 1
                else:
                    counter.next = 0
                    state.next = state_t.DONE
        elif state == state_t.DONE:
            done.next = True
            if counter < n:
                temp[counter].next = ((exp_list[counter] << f) // accumulator) << f
                counter.next = counter + 1
            elif counter == n:
                if counter2 < n:
                    out_list[counter2].next = temp[counter2][3 * f:f]
                    counter2.next = counter2 + 1
                else:
                    counter.next = counter + 1
            else:
                # print("temp[0]=", bin2float(str(bin(temp[0][:b], b)) + "." + str(bin(temp[0][b:], b))))
                # print("temp[1]=", bin2float(str(bin(temp[1][:b], b)) + "." + str(bin(temp[1][b:], b))))
                # print("temp[2]=", bin2float(str(bin(temp[2][:b], b)) + "." + str(bin(temp[2][b:0], b))))
                # print("out_list[0]=", bin2float(str(bin(out_list[0][:f], f)) + "." + str(bin(out_list[0][f:], f))))
                # print("out_list[1]=", bin2float(str(bin(out_list[1][:f], f)) + "." + str(bin(out_list[1][f:], f))))
                # print("out_list[2]=", bin2float(str(bin(out_list[2][:f], f)) + "." + str(bin(out_list[2][f:], f))))
                counter.next = 0
                counter2.next = 0
                accumulator.next = 0
                state.next = state_t.COUNT
        else:
            raise ValueError("Undefined state")

    out_vector_c = ConcatSignal(*out_list)

    @always_seq(clk.posedge, reset=reset)
    def map_out():
        out_vector.next = out_vector_c

    return instances()


# Testbench

@block
def test_softmax(vhdl_output_path=None):
    n = 3
    b = 32
    f = 16

    # axis_y = Axis(n*b)
    # axis_x = Axis(n*b)

    in_list = [Signal(intbv(1 << f)[b:]), Signal(intbv(2 << f)[b:]), Signal(intbv(3 << f)[b:])]
    in_vector = ConcatSignal(*reversed(in_list))

    done, enable = [Signal(bool(False)) for i in range(2)]

    out_vector = Signal(intbv(0)[b*n:])

    period = 10
    clk = Signal(bool(False))
    clk_gen_instance = clk_gen(clk, period=10)
    low_time = int(period / 2)
    high_time = period - low_time

    reset = ResetSignal(0, active=1, async=False)

    softmax_instance = softmax(clk, reset, out_vector, in_vector, n, done, enable, M=16, f=16)
    # softmax_instance2 = softmax(clk, reset, axis_y, axis_x, n, done, enable, M=16, f=16)


    # @instance
    # def drive_clk():
    #     while True:
    #         yield delay(low_time)
    #         clk.next = 1
    #         yield delay(high_time)
    #         clk.next = 0


    @instance
    def reset_gen():
        reset.next = 0
        yield delay(6001)
        yield clk.negedge
        reset.next = 1


    @instance
    def stimulus():
        enable.next = True
        yield delay(6000)
        print(bin(out_vector, n * b))
        raise StopSimulation()

    if vhdl_output_path is not None:
        softmax_instance.convert(hdl='VHDL', path=vhdl_output_path, initial_values=True)

    return instances()


if __name__ == '__main__':
    trace_save_path = './out/testbench/'
    vhdl_output_path = './out/vhdl/'
    os.makedirs(os.path.dirname(trace_save_path), exist_ok=True)
    os.makedirs(os.path.dirname(vhdl_output_path), exist_ok=True)

    tb = test_softmax(vhdl_output_path)
    # tb = test_softmax()
    tb.config_sim(trace=True, directory=trace_save_path, name='softmax_tb')
    tb.run_sim()

