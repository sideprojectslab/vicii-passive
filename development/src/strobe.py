
from ezhdl   import *
from vic_pkg import *

class Strobe(Entity):
	def __init__(self):
		self.i_clk  = Input (Wire())
		self.i_rst  = Input (Wire())
		self.i_ph0  = Input (Wire())
		self.o_strb = Output(t_vic_strb)

		self.ph0_1r = Signal(Wire())

	def _run(self):
		if self.i_clk.posedge():
			if self.ph0_1r.now == 1 and self.i_ph0.now == 0:
				self.o_strb.nxt <<= 1
				pass
			else:
				self.o_strb.nxt <<= self.o_strb.now + 1
			self.ph0_1r.nxt <<= self.i_ph0.now

			if self.i_rst.now:
				self.ph0_1r.nxt <<= 1
				self.o_strb.nxt <<= 0

	def _reset(self):
		pass
