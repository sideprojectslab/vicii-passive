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
		self.i_en      = Input(Wire())
		self.frame     = Input(Wire())

		self.o_actv    = Output(Wire())
		self.o_prio    = Output(Wire())
		self.o_colr    = Output(t_vic_colr)

		self.acquire   = Signal(Wire())

		self.spen      = Signal(Unsigned().bits(8))
		self.prio      = Signal(Unsigned().bits(8))
		self.mxmc      = Signal(Unsigned().bits(8))
		self.xexp      = Signal(Unsigned().bits(8))
		self.yexp      = Signal(Unsigned().bits(8))

		self.colr      = Signal(Array([Unsigned().bits(4)]*8))
		self.mclr      = Signal(Array([Unsigned().bits(4)]*8))
		self.xpos      = Signal(Array([Unsigned().bits(9)]*8))
		self.ypos      = Signal(Array([Unsigned().bits(8)]*8))

		self.ydisp     = Signal(Unsigned().bits(8))
		self.xdisp     = Signal(Unsigned().bits(8))
		self.yincr     = Signal(Unsigned().bits(8))
		self.xincr     = Signal(Unsigned().bits(8))

		t_count         = Unsigned().upto(31)
		self.count_sprt = Signal(t_count)
		self.count_data = Signal(t_count)
		self.count_ylen = Signal(Array([Unsigned().bits(6)]*8))
		self.count_xlen = Signal(Array([Unsigned().bits(6)]*8))

		self.shreg      = Signal(Array([Unsigned().bits(24)]*8))
		self.sprt_val   = Signal(Unsigned().bits(2))
		self.mc_phy     = Signal(Unsigned().bits(8))


	def _run(self):

		if self.i_clk.posedge():

			self.spen.nxt <<= self.i_regs.now [21]
			self.prio.nxt <<= ~self.i_regs.now[27]
			self.mxmc.nxt <<= self.i_regs.now [28]
			self.xexp.nxt <<= self.i_regs.now [29]

			for i in range(8):
				self.colr.nxt[i] <<= self.i_regs.now[39 + i][4:0]
				self.ypos.nxt[i] <<= self.i_regs.now[i*2 + 1]
				self.xpos.nxt[i] <<= join(self.i_regs.now[16][i], self.i_regs.now[i*2])


			if self.i_strb.now[0]:

				################################################################
				#                       VERTICAL TRIGGER                       #
				################################################################

				# resetting counters and enable flags for those sprites that have been fully
				# displayed at the end of the visible screen

				bl.add(f"[SPRITES]: enabled = {bin(self.spen.now.dump)}")

				if (self.i_strb.now == 5) and (self.i_cycl.now == self.i_specs.now.cycl - 6):
					for i in range(8):

						# here we can activate a sprite right away as it gets sampled, if enabled
						if (self.spen.now[i] == 1                   ) and \
						   (self.ypos.now[i] == self.i_ypos.now[8:0]):
							self.ydisp     .nxt[i] <<= 1
							self.count_ylen.nxt[i] <<= 0
							self.yexp      .nxt[i] <<= self.i_regs.now[23][i]
							self.yincr     .nxt[i] <<= not self.yexp.now[i]

						elif (self.ydisp.now[i]):
							if (self.count_ylen.now[i] == 20) and (self.yincr.now[i] == 1):
								self.ydisp.nxt[i] <<= 0
							else:
								if self.yincr.now[i]:
									self.count_ylen.nxt[i] <<= self.count_ylen.now[i] + 1
								if self.yexp.now[i]:
									self.yincr.nxt[i] <<= not self.yincr.now[i]


				################################################################
				#                      SPRITE ACQUISITION                      #
				################################################################

				# initiate sprite data acquisition on all lines, because why not
				if (self.i_strb.now == 5) and (self.i_cycl.now == self.i_specs.now.cycl - 6):
					self.count_sprt.nxt <<= 0
					self.count_data.nxt <<= 3
					self.acquire   .nxt <<= 1

				# sprite data acquisition
				if self.acquire.now:
					if (self.i_strb.now == 7):
						if (self.count_data.now != 3):
							self.count_xlen.now[self.count_sprt.now] <<= 0
							self.xdisp     .now[self.count_sprt.now] <<= 0

							self.shreg.nxt[self.count_sprt.now][:8]  <<= self.shreg.nxt[self.count_sprt.now][-8:0]
							self.shreg.nxt[self.count_sprt.now][:-8] <<= self.i_data.now[8:]

							if (self.count_data.now == 2):
								if (self.count_sprt.now == 7):
									self.acquire.nxt <<= 0
								else:
									self.count_sprt.nxt <<= self.count_sprt.now + 1
							self.count_data.nxt <<= self.count_data.now + 1
						else:
							self.count_data.nxt <<= 0


				################################################################
				#                       SPRITE PLAYBACK                        #
				################################################################

				self.o_actv.nxt <<= 0
				self.o_prio.nxt <<= 0
				self.mc_phy.nxt <<= not self.mc_phy.now

				for i in range(7, -1, -1):

					# horizontal trigger
					if (self.ydisp.now[i]):
						if (self.xpos.now[i] == self.i_xpos.now) and (self.xdisp.now[i] == 0) and (self.count_xlen.now[i] == 0):
							self.xdisp .nxt[i] <<= 1
							self.xincr .nxt[i] <<= not self.xexp.now[i]
							self.mc_phy.nxt[i] <<= 0

						# execution
						if (self.xdisp.now[i]):

							# handle multi-color here
							if self.mxmc.now[i]:
								if self.mc_phy.nxt[i] == 0:
									sprt_val = self.shreg.now[i][:-2]
									self.sprt_val.nxt <<= sprt_val
								else:
									sprt_val = self.sprt_val.now
							else:
								sprt_val = self.shreg.now[i][-1] << 1

							self.o_actv.nxt <<= (sprt_val != 0)
							self.o_prio.nxt <<= self.prio.now[i]

							if sprt_val == 0b01:
								self.o_colr.nxt <<= self.mclr.now[0]
							elif sprt_val == 0b10:
								self.o_colr.nxt <<= self.colr.now[i]
							elif sprt_val == 0b11:
								self.o_colr.nxt <<= self.mclr.now[1]


							if (self.count_xlen.now[i] == 23) and (self.xincr.now[i] == 1):
								# horizontal end of a sprite
								self.xdisp.nxt[i] <<= 0
							else:
								if (self.xincr.now[i] == 1):
									self.count_xlen.nxt[i] <<= self.count_xlen.now[i] + 1
									self.shreg     .nxt[i] <<= self.shreg.now[i] << 1

								if self.xexp.now[i]:
									self.xincr.nxt[i] <<= not self.xincr.now[i]

			if self.i_rst.now:
				self.acquire.nxt <<= 0
				self.xdisp  .nxt <<= 0
				self.ydisp  .nxt <<= 0
