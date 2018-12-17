
def my_softmax(clk, reset, axis_s_raw, axis_m_sum, n=8):


    t_State = enum("STATE1", "STATE2")
    state = Signal(state_t.COUNT)
@always_seq(clk.posedge, reset=reset)


    return instances()



t_State = enum("WAITING", "CALCULATING")

N = 4   # number of elements in vector
b = 32  # bits in word
M = 10  # number of elements Maclaurin series
        # the same for factorial tuple


@block
def Top(out_vector, done, in_vector, start, clock, reset):
    """
        This module computes softmax function.

        Ports:
        -----
        out_vector: softmax function of the input vector
        done: output flag indicated completion of the computation
        vector: input vector (sequence)
        start: input that starts the computation on a posedge
        clock: clock input
        reset: reset input

    """
    # input bit width
    W = len(in_vector)

    # tuple with factorial
    fact = tuple([math.factorial(i) for i in range(M)])

    # indices for vector
    left_i = tuple([i - 1 for i in range(W, 0, -b)])
    right_i = tuple([i - b for i in range(W, 0, -b)])

    # Softmax function
    @instance
    def process():
        a = intbv(0)[32:]
        b = intbv(0)[32:]
        c = intbv(0)[32:]
        d = intbv(0)[32:]
        sum = intbv(0)[32:]
        e = intbv(0)[32:]

        i = intbv(0, min=0, max=N)
        m = intbv(0, min=0, max=M)

        state = t_State.WAITING

        while True:
            yield clock.posedge, reset.posedge

            if reset:
                state = t_State.WAITING
                a.next = 0
                b.next = 0
                c.next = 0
                d.next = 0
                sum.next = 0
                done.next = False
                i[:] = 0

            else:
                if state == t_State.WAITING:
                    if start:
                        #for i in range(N):
                        a[:] = in_vector(left_i(int[0]),right_i(int[0]))
                        b[:] = in_vector(left_i(int[1]),right_i(int[1]))
                        c[:] = in_vector(left_i(int[2]),right_i(int[2]))
                        d[:] = in_vector(left_i(int[3]),right_i(int[3]))
                        done.next = False
                        state = t_State.CALCULATING

                elif state == t_State.CALCULATING:
                    # sum.next = 0
                    # for i in range(N):
                    #     e = 0
                    #     # exp from Maclaurin series
                    #     for m in range(M):
                    #         e = e + ((vector[i] ** m) / fact[int(m)])
                    #     sum += e
                    #     ret[i] = e
                    # e**a
                    e = 0
                    for m in range(M):
                        e += (a**m // fact[int(m)])
                    a = e
                    sum += e

                    # e**b
                    e = 0
                    for m in range(M):
                        e += (b**m // fact[int(m)])
                    b = e
                    sum += e

                    # e**c
                    e = 0
                    for m in range(M):
                        e += (c**m // fact[int(m)])
                    c = e
                    sum += e

                    # e**d
                    e = 0
                    for m in range(M):
                        e += (d**m // fact[int(m)])
                    d = e
                    sum += e

                    # a = a/sum
                    # b = b/sum
                    # c = c/sum
                    # d = d/sum

                    out_vector = ConcatSignal(*reversed([a, b, c, d]))
                    done.next = True
    return instances()
