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

import bus_logger as bl

class Border(Entity):
	def __init__(self):
		self.i_specs = Input (t_vic_specs_h63)
		self.i_clk   = Input (Wire())
		self.i_rst   = Input (Wire())
		self.i_strb  = Input (t_vic_strb)
		self.i_cycl  = Input (t_vic_cycl)
		self.i_xpos  = Input (t_vic_ppos)
		self.i_ypos  = Input (t_vic_ppos)
		self.i_regs  = Input (t_vic_regs)
		self.o_vbrd  = Output(Wire())
		self.o_bord  = Output(Wire())
		self.o_colr  = Output(t_vic_colr)

		self.ff_main = Signal(Wire())
		self.ff_vert = Signal(Wire())

	def _run(self):
		if self.i_clk.posedge():

			specs   = self.i_specs.now
			ff_main = local(self.ff_main)
			ff_vert = local(self.ff_vert)

			reg_ec   = self.i_regs.now[32][4:0]
			reg_rsel = self.i_regs.now[17][3]
			reg_csel = self.i_regs.now[22][3]
			reg_den  = self.i_regs.now[17][4]

			edge_ll = specs.xfvc + 7 if (reg_csel == 0) else specs.xfvc
			edge_rr = specs.xlvc - 8 if (reg_csel == 0) else specs.xlvc + 1
			edge_hi = specs.yfvc + 4 if (reg_rsel == 0) else specs.yfvc
			edge_lo = specs.ylvc - 3 if (reg_rsel == 0) else specs.ylvc + 1


			if self.i_strb.now[0]:
				# vertical ff control
				if (self.i_cycl.now == specs.CYCLE_YFF):
					if (self.i_ypos.now == edge_lo):
						ff_vert <<= 1

					elif (self.i_ypos.now == edge_hi) and (reg_den == 1):
						ff_vert <<= 0

				elif (self.i_xpos.now == edge_ll):
					if (self.i_ypos.now == edge_lo):
						ff_vert <<= 1

					elif (self.i_ypos.now == edge_hi) and (reg_den == 1):
						ff_vert <<= 0

				# main ff control
				if (self.i_xpos.now == edge_rr):
					ff_main <<= 1
				elif (self.i_xpos.now == edge_ll) and (ff_vert == 0):
					ff_main <<= 0

				self.o_vbrd.nxt <<= ff_vert
				self.o_bord.nxt <<= ff_main
				self.o_colr.nxt <<= reg_ec

				self.ff_vert.nxt <<= ff_vert
				self.ff_main.nxt <<= ff_main

				if self.o_bord.now:
					bl.add("[BORDER] On")
				else:
					bl.add("[BORDER] Off")
				bl.add(f"    Left Edge  = {edge_ll}")
				bl.add(f"    Right Edge = {edge_rr}")
				bl.add(f"    Top Edge   = {edge_hi}")
				bl.add(f"    Bot Edge   = {edge_lo}")

			if self.i_rst.now:
				self.ff_main.nxt <<= 1
				self.ff_vert.nxt <<= 1
