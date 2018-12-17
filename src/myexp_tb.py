from src.softmax import *


def bin2float (b):
    s, f = b.find('.')+1, int(b.replace('.',''), 2)
    return f/2.**(len(b)-s) if s else f

@block
def test_myexp(vhdl_output_path=None):

    x = Signal(intbv(0)[32:])
    exp_x = Signal(intbv(0)[32:])
    done, enable = [Signal(bool(False)) for i in range(2)]
    clk = Signal(bool(False))
    clk_gen_instance = clk_gen(clk, period=10)
    reset = ResetSignal(0, active=1, async=False)
    myexp_instance = myexp(clk, reset, exp_x, x, done, enable, M=16, f=16)

    liczba = 2.5

    @instance
    def reset_gen():
        reset.next = 0
        yield delay(5000)
        yield clk.negedge
        reset.next = 1

    @instance
    def stimulus():
        x.next = 0b101000000000000000  # calculate for exp(2.5)
        enable.next = 1
        yield delay(3000)
        print("x=", bin(x[:16], 16), ".", bin(x[16:], 16))
        print("exp_x=", bin(exp_x[:16], 16), ".", bin(exp_x[16:], 16))
        print("exp_x=", bin2float(str(bin(exp_x[:16], 16))+"."+str(bin(exp_x[16:], 16))))
        print("exp(", liczba, ")=", math.exp(liczba))
        raise StopSimulation()

    if vhdl_output_path is not None:
        myexp_instance.convert(hdl='VHDL', path=vhdl_output_path)

    return instances()


if __name__ == '__main__':
    trace_save_path = './out/test_mypower/'
    vhdl_output_path = './out/vhdl/'
    os.makedirs(os.path.dirname(trace_save_path), exist_ok=True)
    os.makedirs(os.path.dirname(vhdl_output_path), exist_ok=True)

    # tb = test_mypower(vhdl_output_path)
    tb = test_myexp()
    tb.config_sim(trace=True, directory=trace_save_path, name='test_mypower')
    tb.run_sim()
