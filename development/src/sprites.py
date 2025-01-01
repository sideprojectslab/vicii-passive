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

class Sprites(Entity):
	def __init__(self):
		self.i_clk     = Input(Wire())
		self.i_rst     = Input(Wire())
		self.i_specs   = Input(VicSpecs(H63))
		self.i_regs    = Input(t_vic_regs)
		self.i_strb    = Input(t_vic_strb)
		self.i_cycl    = Input(t_vic_cycl)
		self.i_xpos    = Input(t_vic_ppos)
		self.i_ypos    = Input(t_vic_ppos)
		self.i_data    = Input(t_vic_data)

		self.o_actv    = Output(Wire())
		self.o_prio    = Output(Wire())
		self.o_colr    = Output(t_vic_colr)

		# signals

		self.dma1_cycl = Signal(Unsigned().upto(65))
		self.dma2_cycl = Signal(Unsigned().upto(65))
		self.yexp_cycl = Signal(Unsigned().upto(65))
		self.strt_cycl = Signal(Unsigned().upto(65))
		self.acquire   = Signal(Wire())

		self.spen      = Signal(Unsigned().bits(8))
		self.prio      = Signal(Unsigned().bits(8))
		self.mxmc      = Signal(Unsigned().bits(8))
		self.xexp      = Signal(Unsigned().bits(8), ppl=3)
		self.yexp      = Signal(Unsigned().bits(8))

		self.colr      = Signal(Array([Unsigned().bits(4)]*8))
		self.mclr      = Signal(Array([Unsigned().bits(4)]*2))
		self.xpos      = Signal(Array([Unsigned().bits(9)]*8))
		self.ypos      = Signal(Array([Unsigned().bits(8)]*8))

		self.spdma     = Signal(Unsigned().bits(8))
		self.xtrig     = Signal(Unsigned().bits(8), ppl=5)
		self.ydisp     = Signal(Unsigned().bits(8))
		self.xdisp     = Signal(Unsigned().bits(8))
		self.yincr     = Signal(Unsigned().bits(8))
		self.xincr     = Signal(Unsigned().bits(8))

		t_count         = Unsigned().upto(31)
		self.count_sprt = Signal(t_count)
		self.count_data = Signal(t_count)
		self.count_ylen = Signal(Array([Unsigned().bits(6)]*8))
		self.count_xlen = Signal(Array([Unsigned().bits(6)]*8))
		self.count_halt = Unsigned().bits(8)

		self.shreg      = Signal(Array([Unsigned().bits(24)]*8))
		self.sprt_val   = Signal(Array([Unsigned().bits(2)]*8))
		self.mc_phy     = Signal(Unsigned().bits(8))


	def _run(self):

		# these will be added to the specs soon, at the moment these represent
		# the correct settings for PAL machines
		self.dma1_cycl.nxt <<= 54
		self.dma2_cycl.nxt <<= 55
		self.yexp_cycl.nxt <<= 55
		self.strt_cycl.nxt <<= 57

		if self.i_clk.posedge():

			# really just aliasing registers. Running on even cycles too makes
			# this behave like a concurrent statement for all intents & purposes
			self.spen.nxt <<=  self.i_regs.now[21]
			self.prio.nxt <<= ~self.i_regs.now[27]
			self.mxmc.nxt <<=  self.i_regs.now[28]
			self.yexp.nxt <<=  self.i_regs.now[23]

			for i in range(8):
				self.colr.nxt[i] <<= self.i_regs.now[39 + i][4:0]
				self.ypos.nxt[i] <<= self.i_regs.now[i*2 + 1]
				self.xpos.nxt[i] <<= join(self.i_regs.now[16][i], self.i_regs.now[i*2])

			self.mclr.nxt[0] <<= self.i_regs.now[37][4:0]
			self.mclr.nxt[1] <<= self.i_regs.now[38][4:0]


			# rising edges of DOD clock
			if self.i_strb.now[0]:
				self.xexp.nxt   <<= self.i_regs.now[29]
				self.xtrig.nxt  <<= 0
				self.o_actv.nxt <<= 0
				self.o_prio.nxt <<= 0

				bl.add(f"[SPRITES] x-display   = {bin(self.xdisp.now.dump)}")
				bl.add(f"[SPRITES] x-display   = {bin(self.xdisp.now.dump)}")
				bl.add(f"[SPRITES] y-display   = {bin(self.ydisp.now.dump)}")
				bl.add(f"[SPRITES] x-expansion = {bin(self.xexp.now.dump)}")
				bl.add(f"[SPRITES] y_expansion = {bin(self.yexp.now.dump)}")
				bl.add(f"[SPRITES] multicolor  = {bin(self.mxmc.now.dump)}")
				bl.add(f"[SPRITES] mc-phy      = {bin(self.mc_phy.now.dump)}")
				bl.add(f"[SPRITES] xy-incr     = {bin(self.xincr.now.dump)}, {bin(self.yincr.now.dump)}")

				for i in range(8):
					bl.add(f"[SPRITES][{i}] xy-pos = {self.xpos.now[i]}, {self.ypos.now[i]} | xy-count = {self.count_xlen.now[i].dump}, {self.count_ylen.now[i].dump}")

				# looping over the sprites
				for i in range(7, -1, -1):

					############################################################
					#                     SPRITE PLAYBACK                      #
					############################################################

					# horizontal trigger
					if (self.ydisp.now[i]):
						if ((self.xpos.now[i] == self.i_xpos.now) and
						    (self.xdisp.now[i] == 0             ) and
						    (self.count_xlen.now[i] == 0        )):
							self.xtrig.nxt[i] <<= 1

						if self.xtrig.now[i]:
							# bl.add(f"[SPRITES] Sprite {i} horizontal start")
							self.xdisp .nxt[i] <<= 1
							self.xincr .nxt[i] <<= not self.xexp.now[i]
							self.mc_phy.nxt[i] <<= 0

						# execution
						if (self.xdisp.now[i]):
							# handle multi-color here
							if self.mxmc.now[i]:
								if self.mc_phy.now[i] == 0:
									sprt_val = self.shreg.now[i][:-2]
								else:
									sprt_val = self.sprt_val.now[i]
							else:
								sprt_val = self.shreg.now[i][-1] << 1
							self.sprt_val.nxt[i] <<= sprt_val

							if sprt_val != 0b00:
								self.o_actv.nxt <<= 1
								self.o_prio.nxt <<= self.prio.now[i]

							if sprt_val == 0b01:
								self.o_colr.nxt <<= self.mclr.now[0]
							elif sprt_val == 0b10:
								self.o_colr.nxt <<= self.colr.now[i]
							elif sprt_val == 0b11:
								self.o_colr.nxt <<= self.mclr.now[1]

							bl.add(f"[SPRITES] Playing Sprite {i}, value = {sprt_val}, color: {self.o_colr.nxt}")

							if (self.count_xlen.now[i] == 23) and (self.xincr.now[i] == 1):
								# horizontal end of a sprite
								self.xdisp.nxt[i] <<= 0

							else:
								if (self.xincr.now[i] == 1):
									self.count_xlen.nxt[i] <<= self.count_xlen.now[i] + 1
									self.shreg.nxt[i]      <<= self.shreg.now[i] << 1
									self.mc_phy.nxt[i]     <<= not self.mc_phy.now[i]

								if self.xexp.now[i]:
									self.xincr.nxt[i] <<= not self.xincr.now[i]
								else:
									self.xincr.nxt[i] <<= 1

					############################################################
					#                     VERTICAL TRIGGER                     #
					############################################################

					if (self.i_strb.now == 1) and (self.i_cycl.now == 15):
						if (self.count_ylen.now[i] == 20) and (self.yincr.now[i] == 1):
							self.spdma.nxt[i] <<= 0
						else:
							if self.yincr.now[i]:
								self.count_ylen.nxt[i] <<= self.count_ylen.now[i] + 1

					if (self.i_strb.now == 1) and ((self.i_cycl.now == self.dma1_cycl.now) or (self.i_cycl.now == self.dma2_cycl.now)):
						if (not self.spdma.now[i]) and self.spen.now[i] and (self.ypos.now[i] == self.i_ypos.now[8:0]):
							self.spdma.nxt[i]      <<= 1
							self.yincr.nxt[i]      <<= 1
							self.count_ylen.nxt[i] <<= 0

					if (self.i_strb.now == 1) and (self.i_cycl.now == self.yexp_cycl.now):
						if self.spdma.now[i] and self.yexp.now[i]:
							self.yincr.nxt[i] <<= not self.yincr.now[i]
						else:
							self.yincr.nxt[i] <<= 1

					if (self.i_strb.now == 1) and (self.i_cycl.now == self.strt_cycl.now):
						if self.spdma.now[i]:
							if self.spen.now[i] and (self.ypos.now[i] == self.i_ypos.now[8:0]):
								self.ydisp.nxt[i] <<= 1 # non-blocking in kawari
						else:
							self.ydisp.nxt[i] <<= 0 # non-blocking in kawari

				################################################################
				#                      SPRITE ACQUISITION                      #
				################################################################

				if (self.i_strb.now == 1) and (self.i_cycl.now == self.strt_cycl.now):
					# initiate sprite data acquisition on all lines
					self.count_sprt.nxt <<= 0
					self.count_data.nxt <<= 3
					self.acquire   .nxt <<= 1

				# sprite data acquisition
				if self.acquire.now:

					self.count_xlen.nxt[self.count_sprt.now] <<= 0
					self.xdisp     .nxt[self.count_sprt.now] <<= 0

					if (self.i_strb.now == 7) or (self.i_strb.now == 15):
						bl.add(f"[SPRITES] Acquiring Sprite {i}, cycle {self.count_data.now.dump}")

						if (self.count_data.now != 3):
							if self.count_data.now == 0:
								self.shreg.nxt[self.count_sprt.now][24:16] <<= self.i_data.now[8:0]
							if self.count_data.now == 1:
								self.shreg.nxt[self.count_sprt.now][16: 8] <<= self.i_data.now[8:0]
							if self.count_data.now == 2:
								self.shreg.nxt[self.count_sprt.now][ 8: 0] <<= self.i_data.now[8:0]

							if (self.count_data.now == 2):
								if (self.count_sprt.now == 7):
									self.acquire.nxt <<= 0
								else:
									self.count_sprt.nxt <<= self.count_sprt.now + 1

							self.count_data.nxt <<= self.count_data.now + 1
						else:
							self.count_data.nxt <<= 0


			if self.i_rst.now:
				self.acquire.nxt <<= 0
				self.xdisp  .nxt <<= 0
				self.ydisp  .nxt <<= 0
