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
SHREG_LEN = 8

class GraphicsGen(Entity):
	def __init__(self):
		self.i_clk     = Input (Wire())
		self.i_rst     = Input (Wire())
		self.i_strb    = Input (t_vic_strb)
		self.i_vbrd    = Input (Wire())
		self.i_regs    = Input (t_vic_regs)

		self.i_actv      = Input (Wire())
		self.i_grfx    = Input (t_vic_grfx)
		self.i_data    = Input (t_vic_data)

		self.o_bgnd    = Output(Wire())
		self.o_colr    = Output(t_vic_colr)

		self.shreg     = Signal(Unsigned().bits(SHREG_LEN))
		self.xscroll   = Signal(Unsigned().upto(7))

		self.vbrd_1r   = Signal(Wire()    , ppl=4)
		self.actv_1r   = Signal(Wire()    , ppl=1)
		self.grfx_1r   = Signal(t_vic_grfx, ppl=1)
		self.data_1r   = Signal(t_vic_data, ppl=1)
		self.data_3r   = Signal(t_vic_data)
		self.mc_phy    = Signal(Wire())

		self.bg_colr   = Signal(Array([t_vic_colr]*4), ppl=1)

		self.ecm_ppl   = Signal(Wire(), ppl=2)
		self.mcm_ppl   = Signal(Wire(), ppl=2)
		self.bmm_ppl   = Signal(Wire(), ppl=2)

		self.ecm        = Signal(Wire())
		self.mcm        = Signal(Wire())
		self.bmm        = Signal(Wire())
		self.mcm_old    = Signal(Wire())

		self.gfx_val   = Signal(Unsigned().bits(2))
		self.gfx_bgnd  = Signal(Wire())


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

				# driving the pipeline
				self.vbrd_1r.nxt <<= self.i_vbrd.now

				if (self.i_strb.now == 15):

					# just advancing the pipeline
					self.actv_1r.nxt <<= self.actv_1r.tip
					self.grfx_1r.nxt <<= self.grfx_1r.tip
					self.data_1r.nxt <<= self.data_1r.tip

					if self.i_actv.now and not self.vbrd_1r.now:
						self.xscroll.nxt <<= self.i_regs.now[22][3:0]

					if self.i_actv.now:
						self.grfx_1r.nxt <<= self.i_grfx.now
						self.data_1r.nxt <<= self.i_data.now
						self.actv_1r.nxt <<= 1
					else:
						self.data_1r.nxt <<= 0
						self.actv_1r.nxt <<= 0

				################################################################
				#                     LATCHING MODE FLAGS                      #
				################################################################

				self.mc_phy.nxt  <<= not self.mc_phy.now

				# intentionally delaying the video mode selection flags
				# (see signal pipeline values)
				self.ecm_ppl.nxt <<= self.i_regs.now[17][6]
				self.bmm_ppl.nxt <<= self.i_regs.now[17][5]
				self.mcm_ppl.nxt <<= self.i_regs.now[22][4]

				if self.i_strb.now == 1:
					self.ecm.nxt <<= self.ecm.now | self.ecm_ppl.now
					self.bmm.nxt <<= self.bmm.now | self.bmm_ppl.now

				if self.i_strb.now == 3:
					self.ecm.nxt <<= self.ecm.now & self.ecm_ppl.now
					self.bmm.nxt <<= self.bmm.now & self.bmm_ppl.now

				if self.i_strb.now == 9:
					self.mcm.nxt <<= self.mcm_ppl.now

				if self.i_strb.now == 15:
					self.mcm_old.nxt <<= self.mcm.now
					if self.mcm.now != self.mcm_old.tip:
						self.mc_phy.nxt <<= 1

				################################################################
				#                    LOADING SHIFT REGISTER                    #
				################################################################

				# advancing shift register
				self.shreg.nxt[:1] <<= self.shreg.tip[-1:]
				self.shreg.nxt[0]  <<= 0

				if (self.i_strb.now // 2) == self.xscroll.now:
					# resetting the multi-color phase if data is enabled or by a
					# small amount into the right border. To be seen because it
					# seems a little too "ad-hoc" as a fix
					if self.actv_1r.now or (self.i_strb.now < 7):
						self.mc_phy.nxt <<= 0

					if self.actv_1r.now and not self.vbrd_1r.now:
						# bl.add("[GFX-GEN] Loading Shift Register")
						# latching delayed data
						self.data_3r.nxt <<= self.data_1r.now
						# loading the shift registers
						self.shreg.nxt[8:0] <<= self.grfx_1r.now

				################################################################
				#                       COLOR SELECTION                        #
				################################################################

				self.bg_colr.nxt[0] <<= self.i_regs.now[33][4:0]
				self.bg_colr.nxt[1] <<= self.i_regs.now[34][4:0]
				self.bg_colr.nxt[2] <<= self.i_regs.now[35][4:0]
				self.bg_colr.nxt[3] <<= self.i_regs.now[36][4:0]

				# pixel value selection is based on delayed mode flags
				mc_flag <<= self.data_3r.now[11]

				# bl.add(f"[GFX-GEN] MC-PHASE = {self.mc_phy.now}")
				if self.mcm_old.now:
					if self.bmm.now | mc_flag:
						if self.mc_phy.now == 0:
							gfx_val  <<= self.shreg.now[:-2]
							gfx_bgnd <<= not self.shreg.now[-1]
						else:
							gfx_val  <<= self.gfx_val.now
							gfx_bgnd <<= self.gfx_bgnd.now
					else:
						gfx_val  <<= join(self.shreg.now[-1], self.shreg.now[-1])
						gfx_bgnd <<= not self.shreg.now[-1]
				else:
					if self.bmm.now | mc_flag:
						gfx_val  <<= self.shreg.now[-1] << 1
						gfx_bgnd <<= not self.shreg.now[-1]
					else:
						gfx_val  <<= join(self.shreg.now[-1], self.shreg.now[-1])
						gfx_bgnd <<= not self.shreg.now[-1]

				# saving former pixel values
				self.gfx_val.nxt  <<= gfx_val
				self.gfx_bgnd.nxt <<= gfx_bgnd

				# color selection is based on current mode flags
				mode <<= self.get_mode(self.ecm.now, self.bmm.now, self.mcm.now)

				gfx_colr[0] <<= 0
				gfx_colr[1] <<= 0
				gfx_colr[2] <<= 0
				gfx_colr[3] <<= 0

				data_colr = self.data_3r.now

				if (mode == MODE.STD_TEXT):
					gfx_colr[0] <<= self.bg_colr.now[0]
					gfx_colr[1] <<= self.bg_colr.now[0]
					gfx_colr[2] <<= data_colr[12:8]
					gfx_colr[3] <<= data_colr[12:8]

				elif (mode == MODE.MCL_TEXT):
					if mc_flag:
						gfx_colr[0] <<= self.bg_colr.now[0]
						gfx_colr[1] <<= self.bg_colr.now[1]
						gfx_colr[2] <<= self.bg_colr.now[2]
						gfx_colr[3] <<= data_colr[11:8]
					else:
						gfx_colr[0] <<= self.bg_colr.now[0]
						gfx_colr[1] <<= self.bg_colr.now[0]
						gfx_colr[2] <<= data_colr[11:8]
						gfx_colr[3] <<= data_colr[11:8]

				elif (mode ==  MODE.STD_BMAP):
					gfx_colr[0] <<= data_colr[4:0]
					gfx_colr[1] <<= data_colr[4:0]
					gfx_colr[2] <<= data_colr[8:4]
					gfx_colr[3] <<= data_colr[8:4]

				elif (mode == MODE.MCL_BMAP):
					gfx_colr[0] <<= self.bg_colr.now[0]
					gfx_colr[1] <<= data_colr[8:4]
					gfx_colr[2] <<= data_colr[4:0]
					gfx_colr[3] <<= data_colr[12:8]

				elif (mode == MODE.ECM_TEXT):
					bg_sel      <<= data_colr[8:6]
					gfx_colr[0] <<= self.bg_colr.now[bg_sel]
					gfx_colr[1] <<= self.bg_colr.now[bg_sel]
					gfx_colr[2] <<= data_colr[12:8]
					gfx_colr[3] <<= data_colr[12:8]

				else:
					pass

				################################################################
				#                            OUTPUT                            #
				################################################################

				self.o_colr.nxt <<= gfx_colr[gfx_val]
				self.o_bgnd.nxt <<= gfx_bgnd

				################################################################
				#                           LOGGING                            #
				################################################################

#				bl.add(f"[GFX-GEN] Data & GFX:")
#				bl.add(f"    {bin(data_colr)}")
#				bl.add(f"    {bin(gfx_val)}")
#				bl.add("[GFX-GEN] Graphics Colors:")
#				bl.add(f"    {bl.COLOR[gfx_colr[0]]}")
#				bl.add(f"    {bl.COLOR[gfx_colr[1]]}")
#				bl.add(f"    {bl.COLOR[gfx_colr[2]]}")
#				bl.add(f"    {bl.COLOR[gfx_colr[3]]}")
#				bl.add("[GFX-GEN] Background Colors:")
#				bl.add(f"    {bl.COLOR[self.bg_colr.now[0]]}")
#				bl.add(f"    {bl.COLOR[self.bg_colr.now[1]]}")
#				bl.add(f"    {bl.COLOR[self.bg_colr.now[2]]}")
#				bl.add(f"    {bl.COLOR[self.bg_colr.now[3]]}")
#				bl.add(f"[GFX-GEN] Video Mode:")
#				bl.add(f"    {mode.dump}")
#				bl.add("[GFX-GEN] Is Background:")
#				bl.add(f"    {gfx_bgnd.dump}")
#				bl.add("[GFX-GEN] Xscroll:")
#				bl.add(f"    {self.xscroll.now.dump}")

		if self.i_rst.now:
			pass
