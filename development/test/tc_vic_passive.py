import sys
sys.dont_write_bytecode = True

from ezpath import *

add_rel_path("../src")
add_rel_path("../lib")

from ezhdl           import *
from vic_passive     import *
from frame_render    import *
from frame_render_xl import *

input_path  = get_abs_path("frame_dump.txt")

class VicTest(Entity):
	def __init__(self):
		self.ifile = open(input_path)
		self.lines = self.ifile.readlines()

		self.dut      = VicPassive()
		self.render   = FrameRender()
		self.renderxl = FrameRenderXl()
		self.clkgen   = ClockGen(16.0e6)

		self.clk = Signal(Wire())
		self.rst = Signal(Wire())

		self.clk << self.clkgen.clk

		self.dut.i_clk << self.clk
		self.dut.i_rst << self.rst

		self.render.i_clk  << self.clk
		self.render.i_rst  << self.rst
		self.render.i_colr << self.dut.o_colr
		self.render.i_push << self.dut.o_push
		self.render.i_fstr << self.dut.o_fstr
		self.render.i_lend << self.dut.o_lend
		self.render.i_lstr << self.dut.o_lstr

		self.renderxl.i_clk  << self.clk
		self.renderxl.i_rst  << self.rst
		self.renderxl.i_colr << self.dut.o_colr
		self.renderxl.i_push << self.dut.o_push
		self.renderxl.i_fstr << self.dut.o_fstr
		self.renderxl.i_lend << self.dut.o_lend
		self.renderxl.i_lstr << self.dut.o_lstr


	@procedure
	def _run(self):
		yield from posedge(self.clk)
		self.rst.nxt <<= 1

		yield from posedge(self.clk)
		self.rst.nxt <<= 0

		for _ in range(1):
			for l in self.lines:
				yield from posedge(self.clk)
				line_val = int(l.split()[1])
				self.dut.i_ph0.nxt <<= (line_val >> 21) & 1
				self.dut.i_db.nxt  <<= (line_val >> 9) & (2**12 - 1)
				self.dut.i_a.nxt   <<= (line_val >> 3) & (2**6 - 1)
				self.dut.i_rw.nxt  <<= (line_val >> 2) & 1
				self.dut.i_cs.nxt  <<= (line_val >> 1) & 1
				self.dut.i_aec.nxt <<= (line_val >> 0) & 1

		SimpleSim.stop()


if __name__ == "__main__":
	SimpleSim.vcd_path = get_abs_path("waves.vcd")
	SimpleSim.vcd_timescale = "ns"
	SimpleSim.vcd_live = False
	testcase = VicTest()
	SimpleSim.run(testcase)

	testcase.renderxl.save("frame_analysis.xlsx")
	input("Press any key to exit simulation")