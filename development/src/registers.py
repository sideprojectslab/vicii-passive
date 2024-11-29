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
		self.i_strb = Signal(t_vic_strb)
		self.i_a    = Signal(t_vic_addr)
		self.i_db   = Signal(t_vic_data)
		self.i_cs   = Signal(Wire())
		self.i_rw   = Signal(Wire())

		self.wen    = Signal(Wire())
		self.a_tmp  = Signal(t_vic_addr)
		self.d_tmp  = Signal(t_vic_data)

		self.regs   = Output(t_vic_regs)


	def _run(self):
		if self.i_clk.posedge():
			if (self.i_strb.now == 10) and (self.i_cs.now == 0) and (self.i_rw.now == 0):
				self.wen.nxt   <<= 1
				self.a_tmp.nxt <<= self.i_a.now
				self.d_tmp.nxt <<= self.i_db.now[8:0]

			if (self.i_strb.now == 15) and (self.wen.now == 1):
				self.wen.nxt <<= 0
				self.regs.nxt[self.a_tmp.now] <<= self.d_tmp.now
				bl.add(bl.reg_write_analyze(self.a_tmp.now.val, self.d_tmp.now.val, self.regs.now))

			if self.i_rst.now:
				self.wen.nxt <<= 0
