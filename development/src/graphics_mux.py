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


	def _run(self):

		# concurrent statements
		self.o_push <<= self.xval & self.yval & (self.i_strb[0])

		if self.i_clk.posedge():
			specs = local(self.i_specs)

			if not (self.i_strb[0]):

				self.o_lstr <<= 0
				self.o_lend <<= 0

				if self.i_bord_actv:
					self.o_colr <<= self.i_bord_colr
				else:
					if ((self.i_sprt_actv == 0                              ) or
					    ((self.i_sprt_prio == 0) and (self.i_grfx_bgnd == 0))):
						self.o_colr <<= self.i_grfx_colr
					else:
						self.o_colr <<= self.i_sprt_colr

				if self.g_mark_lines:
					if ((self.i_xpos >= specs.xnul) and (self.i_xpos <= specs.xnul + 16) and
					    (self.i_ypos >= specs.ynul) and (self.i_ypos <= specs.yend     )):
						self.o_colr <<= self.i_ypos[4:0]

				#------------------------------------------------------------#
				#                   FRAME ALIGNMENT SIGNALS                  #
				#------------------------------------------------------------#

				if (self.i_xpos == specs.xnul):
					self.o_lstr <<= 1
					self.xval   <<= 1
					if (self.i_ypos == specs.ynul):
						self.yval   <<= 1
						self.o_fstr <<= 1

				if (self.i_xpos == specs.xend):
					self.o_lend <<= 1

				if (self.i_xpos == specs.xend + 1):
					self.xval   <<= 0
					self.o_fstr <<= 0
					if (self.i_ypos == specs.yend):
						self.yval <<= 0

			if self.i_rst:
				self.o_fstr <<= 0
				self.o_lstr <<= 0
				self.o_lend <<= 0
