
from ezhdl     import *
from vic_pkg   import *
from registers import *


class GraphicsMux(Entity):
	def __init__(self, g_mark_lines=False):

		self.g_mark_lines = g_mark_lines

		self.i_specs     = Input(t_vic_specs_h63)
		self.i_clk       = Input(Wire())
		self.i_rst       = Input(Wire())
		self.i_strb      = Input(t_vic_strb)
		self.i_xpos      = Input(t_vic_ppos)
		self.i_ypos      = Input(t_vic_ppos)
		self.i_bord_actv = Input(Wire())
		self.i_bord_colr = Input(t_vic_colr)

		self.i_grfx_colr = Input(t_vic_colr)
		self.i_grfx_bgnd = Input(Wire())

		self.i_sprt_actv = Input(Wire())
		self.i_sprt_prio = Input(Wire())
		self.i_sprt_colr = Input(t_vic_colr)

		self.o_push      = Output(Wire())
		self.o_lstr      = Output(Wire())
		self.o_lend      = Output(Wire())
		self.o_fstr      = Output(Wire())
		self.o_colr      = Output(t_vic_colr)

		self.xval        = Signal(t_vic_ppos)
		self.yval        = Signal(t_vic_ppos)


	def _run(self):

		# concurrent statements
		self.o_push.nxt <<= self.xval.now & self.yval.now & (self.i_strb.now[0])

		if self.i_clk.posedge():
			specs = self.i_specs.now

			if not (self.i_strb.now[0]):

				self.o_lstr.nxt <<= 0
				self.o_lend.nxt <<= 0

				if self.i_bord_actv.now:
					self.o_colr.nxt <<= self.i_bord_colr.now
				else:
					if ((self.i_sprt_actv.now == 0                                  ) or
					    ((self.i_sprt_prio.now == 0) and (self.i_grfx_bgnd.now == 0))):
						self.o_colr.nxt <<= self.i_grfx_colr.now
					else:
						self.o_colr.nxt <<= self.i_sprt_colr.now

				if self.g_mark_lines:
					if ((self.i_xpos.now >= specs.xnul) and (self.i_xpos.now <= specs.xnul + 16) and
					    (self.i_ypos.now >= specs.ynul) and (self.i_ypos.now <= specs.yend     )):
						self.o_colr.nxt <<= self.i_ypos.now[4:0]

				#------------------------------------------------------------#
				#                   FRAME ALIGNMENT SIGNALS                  #
				#------------------------------------------------------------#

				if (self.i_xpos.now == specs.xnul):
					self.o_lstr.nxt <<= 1
					self.xval.nxt   <<= 1
					if (self.i_ypos.now == specs.ynul):
						self.yval.nxt   <<= 1
						self.o_fstr.nxt <<= 1

				if (self.i_xpos.now == specs.xend):
					self.o_lend.nxt <<= 1

				if (self.i_xpos.now == specs.xend + 1):
					self.xval.nxt   <<= 0
					self.o_fstr.nxt <<= 0
					if (self.i_ypos.now == specs.yend):
						self.yval.nxt <<= 0

			if self.i_rst.now:
				self.o_fstr.nxt <<= 0
				self.o_lstr.nxt <<= 0
				self.o_lend.nxt <<= 0
