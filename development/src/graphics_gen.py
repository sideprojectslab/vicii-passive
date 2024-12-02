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

MODE      = Enum("STD_TEXT", "MCL_TEXT", "STD_BMAP", "MCL_BMAP", "ECM_TEXT", "INVALID")
SHREG_LEN = 16

class GraphicsGen(Entity):
	def __init__(self):
		self.i_clk   = Input (Wire())
		self.i_rst   = Input (Wire())
		self.i_strb  = Input (t_vic_strb)
		self.i_en    = Input (Wire())
		self.i_regs  = Input (t_vic_regs)
		self.i_grfx  = Input (t_vic_grfx)
		self.i_data  = Input (t_vic_data)

		self.o_bgnd  = Output(Wire())
		self.o_colr  = Output(t_vic_colr)

		class InternalSignals(Record):
			def __init__(self):
				self.mode     = Unsigned().span(len(MODE))
				self.grfx     = type(t_vic_grfx)()
				self.en       = Wire()
				self.data     = type(t_vic_data)()
				self.mc_flag  = Wire()
				self.bg_sel   = Wire()
				self.shreg_bg = Unsigned().bits(SHREG_LEN)
				self.shreg_sc = Unsigned().bits(SHREG_LEN)
				self.shreg_mc = Array([Unsigned().bits(2)]*SHREG_LEN)
				self.gfx_colr = Array([t_vic_colr]*4)
				self.xscroll  = Unsigned().upto(7)
				self.loaded   = Wire()

		self.s = Signal(InternalSignals())


	def _run(self):
		if self.i_clk.posedge():
			v = local(self.s)

			ecm = self.i_regs[17][6]
			bmm = self.i_regs[17][5]
			mcm = self.i_regs[22][4]

			if(ecm == 0) and (bmm == 0) and (mcm == 0):
				mode = MODE.STD_TEXT
			elif (ecm == 0) and (bmm == 0) and (mcm == 1):
				mode = MODE.MCL_TEXT
			elif (ecm == 0) and (bmm == 1) and (mcm == 0):
				mode = MODE.STD_BMAP
			elif (ecm == 0) and (bmm == 1) and (mcm == 1):
				mode = MODE.MCL_BMAP
			elif (ecm == 1) and (bmm == 0) and (mcm == 0):
				mode = MODE.ECM_TEXT
			else:
				mode = MODE.INVALID

			# serializer
			if (self.i_strb & 1):
				v.shreg_mc[1:] <<= v.shreg_mc[0:-1]
				v.shreg_sc     <<= v.shreg_sc << 1

				# operate with a 1-pixel delay like the border unit, so that the outputs
				# of the two modules are aligned
				if (self.i_strb == 1):
					v.loaded  <<= 0
					v.xscroll <<= self.i_regs[22][3:0]
					v.data    <<= self.i_data
					v.grfx    <<= self.i_grfx
					v.en      <<= self.i_en

				if (v.en == 1) and (v.xscroll == 0) and not v.loaded:
					v.loaded <<= 1

					# loading the shift registers
					for i in range(4):
						j = i*2
						v.shreg_mc[j  ] <<= v.grfx[j+2:j]
						v.shreg_mc[j+1] <<= v.grfx[j+2:j]

					v.shreg_sc[8:0] <<= v.grfx

				if v.xscroll != 0:
					v.xscroll <<= v.xscroll - 1

				v.mode     <<= mode
				v.mc_flag  <<= v.data[11]
				v.bg_sel   <<= v.data[8:6]

				v.gfx_colr <<= Array([t_vic_colr]*4)
				if (v.mode == MODE.STD_TEXT):
					v.gfx_colr[0] <<= self.i_regs[33][4:0]
					v.gfx_colr[1] <<= v.data[12:8]

				elif (v.mode == MODE.MCL_TEXT):
					v.gfx_colr[0] <<= self.i_regs[33][4:0]
					v.gfx_colr[1] <<= self.i_regs[34][4:0]
					v.gfx_colr[2] <<= self.i_regs[35][4:0]
					v.gfx_colr[3] <<= v.data[11:8]

				elif (v.mode ==  MODE.STD_BMAP):
					v.gfx_colr[0] <<= v.data[4:0]
					v.gfx_colr[1] <<= v.data[8:4]

				elif (v.mode == MODE.MCL_BMAP):
					v.gfx_colr[0] <<= self.i_regs[33][4:0]
					v.gfx_colr[1] <<= v.data[8:4]
					v.gfx_colr[2] <<= v.data[4:0]
					v.gfx_colr[3] <<= v.data[12:8]

				elif (mode == MODE.ECM_TEXT):
					match v.bg_sel:
						case 0b00:
							v.gfx_colr[0] <<= self.i_regs[33][4:0]
						case 0b01:
							v.gfx_colr[0] <<= self.i_regs[34][4:0]
						case 0b10:
							v.gfx_colr[0] <<= self.i_regs[35][4:0]
						case 0b11:
							v.gfx_colr[0] <<= self.i_regs[36][4:0]

					v.gfx_colr[1] <<= v.data[12:8]

				if (v.mode == MODE.STD_TEXT):
					if v.shreg_sc[SHREG_LEN - 1] == 0:
						self.o_colr <<= v.gfx_colr[0]
						self.o_bgnd <<= 1
					else:
						self.o_colr <<= v.gfx_colr[1]
						self.o_bgnd <<= 0

				elif (v.mode == MODE.MCL_TEXT):
					if (v.mc_flag):
						self.o_colr <<= v.gfx_colr[v.shreg_mc[-1]]
						self.o_bgnd <<= not v.shreg_mc[-1][1]
					elif v.shreg_sc[-1] == 0:
						self.o_colr <<= v.gfx_colr[0]
						self.o_bgnd <<= 1
					else:
						self.o_colr <<= v.gfx_colr[3]
						self.o_bgnd <<= 0

				elif (v.mode == MODE.STD_BMAP) or (v.mode == MODE.ECM_TEXT):
					if v.shreg_sc[-1] == 0:
						self.o_colr <<= v.gfx_colr[0]
					else:
						self.o_colr <<= v.gfx_colr[1]
					self.o_bgnd <<= not v.shreg_sc[-1]

				elif (v.mode == MODE.MCL_BMAP):
					self.o_colr <<= v.gfx_colr[v.shreg_mc[-1]]
					self.o_bgnd <<= not v.shreg_mc[-1][1]

				else:
					self.o_colr <<= self.o_colr
					self.o_bgnd <<= 1

			self.s <<= v

			if self.i_rst:
				self.s.loaded <<= 0
