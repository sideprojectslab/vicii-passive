
from ezhdl   import *
from vic_pkg import *

import bus_logger as bl

class BadLineDetect(Entity):
	def __init__(self):
		self.i_clk   = Input(Wire())
		self.i_rst   = Input(Wire())
		self.i_specs = Input(VicSpecs(H63))
		self.i_aec   = Input(Wire())
		self.i_strb  = Input(t_vic_strb)
		self.i_cycl  = Input(t_vic_cycl)
		self.i_ypos  = Input(t_vic_ppos)
		self.o_bdln  = Output(Wire())

	def _run(self):
		if self.i_clk.posedge():
			specs = self.i_specs.now

			if (self.i_strb.now == 10):
				if (self.i_cycl.now == specs.CYCL_REF - 1):
					self.o_bdln.nxt <<= 0
				else:
					self.o_bdln.nxt <<= 0
					if ((self.i_ypos.now >= 48) and (self.i_ypos.now < 248) and
					    (self.i_cycl.now >= specs.CYCL_REF                ) and
					    (self.i_cycl.now < specs.CYCL_REF + 40            )):
						self.o_bdln.nxt <<= not self.i_aec.now

				if self.o_bdln.nxt:
					bl.add("Badline")


			if self.i_rst.now:
				self.o_bdln.nxt <<= 0
