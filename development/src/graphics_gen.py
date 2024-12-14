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

MODE      = EnumDef("STD_TEXT", "MCL_TEXT", "STD_BMAP", "MCL_BMAP", "ECM_TEXT", "INVALID")

# we have an additional cell in the shift register to implement an additional cycle delay
SHREG_LEN = 9

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

		self.shreg_sc = Signal(Unsigned().bits(SHREG_LEN))
		self.shreg_mc = Signal(Array([Unsigned().bits(2)]*SHREG_LEN))
		self.xscroll  = Signal(Unsigned().upto(7))

		self.en_1r    = Signal(Wire())
		self.grfx_1r  = Signal(t_vic_grfx)
		self.data_1r  = Signal(t_vic_data)
		self.data_2r  = Signal(t_vic_data)

		self.bg_colr  = Signal(Array([t_vic_colr]*4), ppl=2)

		self.ecm_ppl  = Signal(Wire(), ppl=2)
		self.mcm_ppl  = Signal(Wire(), ppl=2)
		self.bmm_ppl  = Signal(Wire(), ppl=2)

		self.ecm      = Signal(Wire())
		self.mcm      = Signal(Wire())
		self.bmm      = Signal(Wire())
		self.mcm_old  = Signal(Wire())

		self.bgnd_sc  = Signal(Wire())
		self.bgnd_mc  = Signal(Wire())

	@classmethod
	def get_mode(cls, ecm, bmm, mcm):
		if(ecm == 0) and (bmm == 0) and (mcm == 0):
			return MODE.STD_TEXT # single-color
		elif (ecm == 0) and (bmm == 0) and (mcm == 1):
			return MODE.MCL_TEXT # multi-color decided by the color memory
		elif (ecm == 0) and (bmm == 1) and (mcm == 0):
			return  MODE.STD_BMAP # single-color
		elif (ecm == 0) and (bmm == 1) and (mcm == 1):
			return MODE.MCL_BMAP # multi-color
		elif (ecm == 1) and (bmm == 0) and (mcm == 0):
			return MODE.ECM_TEXT
		else:
			return MODE.INVALID


	def _run(self):

		mode     = Enum(MODE)
		mc_flag  = Wire()
		gfx_colr = Array([t_vic_colr]*4)
		gfx_val  = Unsigned().bits(2)
		gfx_bgnd = Wire()
		bg_sel   = Wire()

		if self.i_clk.posedge():

			if (self.i_strb.now & 1):

				################################################################
				#                    LATCHING NEW CHARACTER                    #
				################################################################

				if (self.i_strb.now == 15):
					self.xscroll.nxt <<= self.i_regs.now[22][3:0]
					if self.i_en.now:
						self.grfx_1r.nxt <<= self.i_grfx.now
						self.data_1r.nxt <<= self.i_data.now
						self.en_1r  .nxt <<= 1
					else:
						self.data_1r.nxt <<= 0
						self.en_1r  .nxt <<= 0

				################################################################
				#                    LOADING SHIFT REGISTER                    #
				################################################################

				self.shreg_mc.nxt[1:] <<= self.shreg_mc.now[:-1]
				self.shreg_mc.nxt[0]  <<= 0
				self.shreg_sc.nxt[:1] <<= self.shreg_sc.now[-1:]
				self.shreg_sc.nxt[0]  <<= 0

				if (self.i_strb.now // 2) == self.xscroll.now:
					if self.en_1r.now:

						bl.add("[GFX-GEN] Loading Shift Register")

						self.data_2r.nxt <<= self.data_1r.now
						# loading the shift registers
						for i in range(4):
							j = i*2
							self.shreg_mc.nxt[j  ] <<= self.grfx_1r.now[j+2:j]
							self.shreg_mc.nxt[j+1] <<= self.grfx_1r.now[j+2:j]

						self.shreg_sc.nxt[8:0] <<= self.grfx_1r.now


				# intentionally delaying the video mode selection flags
				# (see signal pipeline values)
				self.ecm_ppl.nxt <<= self.i_regs.now[17][6]
				self.bmm_ppl.nxt <<= self.i_regs.now[17][5]
				self.mcm_ppl.nxt <<= self.i_regs.now[22][4]

				if self.i_strb.now == 3:
					self.ecm.nxt     <<= self.ecm.nxt | self.ecm_ppl.now
					self.bmm.nxt     <<= self.bmm.nxt | self.bmm_ppl.now
					bl.add(f"[GFX-GEN] Latching ECM/BMM 1:")
					bl.add(f"    ECM = {self.ecm.nxt.dump}")
					bl.add(f"    BMM = {self.bmm.nxt.dump}")

				if self.i_strb.now == 5:
					self.ecm.nxt     <<= self.ecm.nxt & self.ecm_ppl.now
					self.bmm.nxt     <<= self.bmm.nxt & self.bmm_ppl.now
					bl.add(f"[GFX-GEN] Latching ECM/BMM 2:")
					bl.add(f"    ECM = {self.ecm.nxt.dump}")
					bl.add(f"    BMM = {self.bmm.nxt.dump}")

				if self.i_strb.now == 11:
					self.mcm.nxt     <<= self.mcm_ppl.now
					#self.mcm_old.nxt <<= self.mcm_old.now & self.mcm_ppl.now
					bl.add(f"[GFX-GEN] Latching MCM 1:")
					bl.add(f"    MCM = {self.mcm.nxt.dump}")
				if self.i_strb.now == 15:
					self.mcm_old.nxt <<= self.mcm.now
					bl.add(f"[GFX-GEN] Latching MCM 2:")
					bl.add(f"    MCM (old) = {self.mcm.now.dump}")

				################################################################
				#                       COLOR SELECTION                        #
				################################################################

				self.bg_colr.nxt[0] <<= self.i_regs.now[33][4:0]
				self.bg_colr.nxt[1] <<= self.i_regs.now[34][4:0]
				self.bg_colr.nxt[2] <<= self.i_regs.now[35][4:0]
				self.bg_colr.nxt[3] <<= self.i_regs.now[36][4:0]
				bg_sel              <<= self.data_2r.now[8:6]

				# pixel value selection is based on delayed mode flags
				mc_flag <<= self.data_2r.now[11]

				if self.mcm_old.now:
					if self.bmm.now | mc_flag:
						gfx_val  <<= self.shreg_mc.now[-1]
						gfx_bgnd <<= not self.shreg_mc.now[-1][1]
					else:
						gfx_val  <<= join(self.shreg_sc.now[-1], self.shreg_sc.now[-1])
						gfx_bgnd <<= not self.shreg_sc.now[-1]
				else:
					if self.bmm.now | mc_flag:
						gfx_val  <<= self.shreg_sc.now[-1] << 1
						gfx_bgnd <<= not self.shreg_sc.now[-1]
					else:
						gfx_val  <<= join(self.shreg_sc.now[-1], self.shreg_sc.now[-1])
						gfx_bgnd <<= not self.shreg_sc.now[-1]


				# color selection is based on current mode flags
				mode <<= self.get_mode(self.ecm.now, self.bmm.now, self.mcm.now)

				if (mode == MODE.STD_TEXT):
					gfx_colr[0] <<= self.bg_colr.now[0]
					gfx_colr[2] <<= self.data_2r.now[12:8]

				elif (mode == MODE.MCL_TEXT):
					gfx_colr[0] <<= self.bg_colr.now[0]
					gfx_colr[1] <<= self.bg_colr.now[1]
					gfx_colr[2] <<= self.bg_colr.now[2]
					gfx_colr[3] <<= self.data_2r.now[11:8]

				elif (mode ==  MODE.STD_BMAP):
					gfx_colr[0] <<= self.data_2r.now[4:0]
					gfx_colr[2] <<= self.data_2r.now[8:4]

				elif (mode == MODE.MCL_BMAP):
					gfx_colr[0] <<= self.bg_colr.now[0]
					gfx_colr[1] <<= self.data_2r.now[8:4]
					gfx_colr[2] <<= self.data_2r.now[4:0]
					gfx_colr[3] <<= self.data_2r.now[12:8]

				elif (mode == MODE.ECM_TEXT):
					match bg_sel:
						case 0b00:
							gfx_colr[0] <<= self.bg_colr.now[0]
						case 0b01:
							gfx_colr[0] <<= self.bg_colr.now[1]
						case 0b10:
							gfx_colr[0] <<= self.bg_colr.now[2]
						case 0b11:
							gfx_colr[0] <<= self.bg_colr.now[3]
					gfx_colr[2] <<= self.data_2r.now[12:8]

				else:
					gfx_colr[0] <<= 0
					gfx_colr[1] <<= 0
					gfx_colr[2] <<= 0
					gfx_colr[3] <<= 0

				################################################################
				#                            OUTPUT                            #
				################################################################

				self.o_colr.nxt <<= gfx_colr[gfx_val]
				self.o_bgnd.nxt <<= gfx_bgnd

				################################################################
				#                           LOGGING                            #
				################################################################

				self.bgnd_sc.nxt <<= not self.shreg_sc.now[-1]
				self.bgnd_mc.nxt <<= not self.shreg_mc.now[-1][1]

				bl.add("[GFX-GEN] Graphics Colors:")
				bl.add(f"    {bl.COLOR[gfx_colr[0]]}")
				bl.add(f"    {bl.COLOR[gfx_colr[1]]}")
				bl.add(f"    {bl.COLOR[gfx_colr[2]]}")
				bl.add(f"    {bl.COLOR[gfx_colr[3]]}")
				bl.add("[GFX-GEN] Background Colors:")
				bl.add(f"    {bl.COLOR[self.bg_colr.now[0]]}")
				bl.add(f"    {bl.COLOR[self.bg_colr.now[1]]}")
				bl.add(f"    {bl.COLOR[self.bg_colr.now[2]]}")
				bl.add(f"    {bl.COLOR[self.bg_colr.now[3]]}")
				bl.add("[GFX-GEN] Video Mode:")
				bl.add(f"    {mode.dump}")
				bl.add("[GFX-GEN] Color Bits:")
				bl.add(f"    SC: {self.shreg_sc.now[-1].dump}")
				bl.add(f"    MC: {self.shreg_mc.now[-1].dump}")
				bl.add("[GFX-GEN] Is Background:")
				bl.add(f"    SC: {self.bgnd_sc.now.dump}")
				bl.add(f"    MC: {self.bgnd_mc.now.dump}")
				bl.add("[GFX-GEN] Xscroll:")
				bl.add(f"    {self.xscroll.now.dump}")

		if self.i_rst.now:
			pass
