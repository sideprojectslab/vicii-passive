# ---------------------------------------------------------------------------- #
#          .XXXXXXXXXXXXXXXX.  .XXXXXXXXXXXXXXXX.  .XX.                        #
#          XXXXXXXXXXXXXXXXX'  XXXXXXXXXXXXXXXXXX  XXXX                        #
#          XXXX                XXXX          XXXX  XXXX                        #
#          XXXXXXXXXXXXXXXXX.  XXXXXXXXXXXXXXXXXX  XXXX                        #
#          'XXXXXXXXXXXXXXXXX  XXXXXXXXXXXXXXXXX'  XXXX                        #
#                        XXXX  XXXX                XXXX                        #
#          .XXXXXXXXXXXXXXXXX  XXXX                XXXXXXXXXXXXXXXXX.          #
#          'XXXXXXXXXXXXXXXX'  'XX'                'XXXXXXXXXXXXXXXX'          #
# ---------------------------------------------------------------------------- #
#              Copyright 2023 Vittorio Pascucci (SideProjectsLab)              #
#                                                                              #
#  Licensed under the GNU GENERAL PUBLIC LICENSE Version 3 (the "License");    #
#  you may not use this file except in compliance with the License.            #
#  You may obtain a copy of the License at                                     #
#                                                                              #
#      https://www.gnu.org/licenses/                                           #
#                                                                              #
#  Unless required by applicable law or agreed to in writing, software         #
#  distributed under the License is distributed on an "AS IS" BASIS,           #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.    #
#  See the License for the specific language governing permissions and         #
#  limitations under the License.                                              #
# ---------------------------------------------------------------------------- #

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

		self.bord_actv   = Signal(Wire()    , ppl=8)
		self.bord_colr   = Signal(t_vic_colr, ppl=1)

		self.sprt_actv   = Signal(Wire()    , ppl=1)
		self.sprt_prio   = Signal(Wire()    , ppl=1)
		self.sprt_colr   = Signal(t_vic_colr, ppl=1)


	def _run(self):

		# concurrent statements
		self.o_push.nxt <<= self.xval.now & self.yval.now & (self.i_strb.now[0])

		if self.i_clk.posedge():
			specs = self.i_specs.now

			if not (self.i_strb.now[0]):

				self.sprt_actv.nxt <<= self.i_sprt_actv.now
				self.sprt_prio.nxt <<= self.i_sprt_prio.now
				self.sprt_colr.nxt <<= self.i_sprt_colr.now

				# driving the pipeline
				self.bord_actv.nxt <<= self.i_bord_actv.now
				self.bord_colr.nxt <<= self.i_bord_colr.now

				self.o_lstr.nxt <<= 0
				self.o_lend.nxt <<= 0

				if self.bord_actv.now:
					self.o_colr.nxt <<= self.bord_colr.now
				else:
					if ((self.sprt_actv.now == 0                                  ) or
					    ((self.sprt_prio.now == 0) and (self.i_grfx_bgnd.now == 0))):
						self.o_colr.nxt <<= self.i_grfx_colr.now
					else:
						self.o_colr.nxt <<= self.sprt_colr.now

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
