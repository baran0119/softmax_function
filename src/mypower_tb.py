from src.softmax import *

@block
def test_mypower(vhdl_output_path=None):

    x_n = Signal(intbv(0)[64:])
    x, n = [Signal(intbv(0)[32:]) for i in range(2)]
    done, enable = [Signal(bool(0)) for i in range(2)]
    clk = Signal(bool(False))
    clk_gen_instance = clk_gen(clk, period=10)
    reset = ResetSignal(0, active=1, async=False)

    mypower_instance = mypower(clk, reset, x_n, x, n, done, enable)

    @instance
    def reset_gen():
        reset.next = 0
        yield delay(5000)
        yield clk.negedge
        reset.next = 1


    @instance
    def stimulus():
        x.next = (5 << 16)  # fixed-point Q16.16
        n.next = 4
        enable.next = 1
        yield delay(1000)
        # print("x = ", int(bin(x), 2))
        # print("n = ", int(bin(n), 2))
        print("x**n = ", int(bin(x_n[:32]), 2))
        print("x=", bin(x[:16], 16), ".", bin(x[16:], 16))
        print("n=", bin(n, 32))
        print("x_n=", bin(x_n[:32], 32), ".", bin(x_n[32:], 32))
        raise StopSimulation()

    if vhdl_output_path is not None:
        mypower_instance.convert(hdl='VHDL', path=vhdl_output_path)

    return instances()


if __name__ == '__main__':
    trace_save_path = './out/test_mypower/'
    vhdl_output_path = './out/vhdl/'
    os.makedirs(os.path.dirname(trace_save_path), exist_ok=True)
    os.makedirs(os.path.dirname(vhdl_output_path), exist_ok=True)

    # tb = test_mypower(vhdl_output_path)
    tb = test_mypower()
    tb.config_sim(trace=True, directory=trace_save_path, name='test_mypower')
    tb.run_sim()
