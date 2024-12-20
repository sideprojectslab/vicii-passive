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

from ezhdl   import *
from vic_pkg import *

import bus_logger as bl

class Registers(Entity):
	def __init__(self):
		self.i_clk  = Input(Wire())
		self.i_rst  = Input(Wire())
		self.i_strb = Input(t_vic_strb)
		self.i_a    = Input(t_vic_addr)
		self.i_db   = Input(t_vic_data)
		self.i_cs   = Input(Wire())
		self.i_rw   = Input(Wire())
		self.o_regs = Output(t_vic_regs)

		self.wen    = Signal(Wire())
		self.a_tmp  = Signal(t_vic_addr)
		self.d_tmp  = Signal(t_vic_data)

	def _run(self):

		if self.i_clk.posedge():

			if (self.i_strb.now == 10):
				self.a_tmp.nxt <<= self.i_a.now

			if (self.i_strb.now == 13) and (self.i_cs.now == 0) and (self.i_rw.now == 0):
				self.wen.nxt <<= 1

			if (self.i_strb.now == 14):
				self.d_tmp.nxt <<= self.i_db.now[8:0]

			if (self.i_strb.now == 15) and self.wen.now:
				self.wen.nxt <<= 0
				self.o_regs.nxt[self.a_tmp.now] <<= self.d_tmp.now
				bl.add(bl.reg_write_analyze(self.a_tmp.now.dump, self.d_tmp.now.dump, self.o_regs.now))

			if self.i_rst.now:
				self.wen.nxt <<= 0


	def _reset(self):
		# these values were dumped from a real VIC during the register timing test
		self.o_regs.nxt[0 ] <<= 56
		self.o_regs.nxt[1 ] <<= 91
		self.o_regs.nxt[2 ] <<= 56
		self.o_regs.nxt[3 ] <<= 99
		self.o_regs.nxt[4 ] <<= 56
		self.o_regs.nxt[5 ] <<= 107
		self.o_regs.nxt[6 ] <<= 56
		self.o_regs.nxt[7 ] <<= 115
		self.o_regs.nxt[8 ] <<= 56
		self.o_regs.nxt[9 ] <<= 123
		self.o_regs.nxt[10] <<= 56
		self.o_regs.nxt[11] <<= 131
		self.o_regs.nxt[12] <<= 56
		self.o_regs.nxt[13] <<= 139
		self.o_regs.nxt[14] <<= 56
		self.o_regs.nxt[15] <<= 147
		self.o_regs.nxt[16] <<= 0
		self.o_regs.nxt[17] <<= 15
		self.o_regs.nxt[18] <<= 55
		self.o_regs.nxt[19] <<= 0
		self.o_regs.nxt[20] <<= 0
		self.o_regs.nxt[21] <<= 255
		self.o_regs.nxt[22] <<= 8
		self.o_regs.nxt[23] <<= 0
		self.o_regs.nxt[24] <<= 28
		self.o_regs.nxt[25] <<= 15
		self.o_regs.nxt[26] <<= 0
		self.o_regs.nxt[27] <<= 0
		self.o_regs.nxt[28] <<= 128
		self.o_regs.nxt[29] <<= 255
		self.o_regs.nxt[30] <<= 0
		self.o_regs.nxt[31] <<= 0
		self.o_regs.nxt[32] <<= 11
		self.o_regs.nxt[33] <<= 0
		self.o_regs.nxt[34] <<= 8
		self.o_regs.nxt[35] <<= 0
		self.o_regs.nxt[36] <<= 0
		self.o_regs.nxt[37] <<= 11
		self.o_regs.nxt[38] <<= 11
		self.o_regs.nxt[39] <<= 11
		self.o_regs.nxt[40] <<= 11
		self.o_regs.nxt[41] <<= 11
		self.o_regs.nxt[42] <<= 11
		self.o_regs.nxt[43] <<= 11
		self.o_regs.nxt[44] <<= 11
		self.o_regs.nxt[45] <<= 11
		self.o_regs.nxt[46] <<= 11
