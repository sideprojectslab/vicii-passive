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
#                                                                              #
#  Crucially, the ph0 signal LEADS slightly compared to the DOT clock, so      #
#  strobe-1 corresponds to the first half-cycle of the VIC clock where ph0     #
#  is zero for the entire time                                                 #
#       ______________                 _______________                 _____   #
#  ph0                |_______________|               |_______________|        #
#           _   _   _   _   _   _   _   _   _   _   _   _   _   _   _   _      #
#  dot    _| |_| |_| |_| |_| |_| |_| |_| |_| |_| |_| |_| |_| |_| |_| |_| |_    #
#                                                                              #
#  clk  _|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|_|   #
#  str                0 1 2 3 4 5 6 7 8 9 A B C D E F 0                        #
#                                                                              #
# ---------------------------------------------------------------------------- #

from ezhdl   import *
from vic_pkg import *

import bus_logger as bl
class Strobe(Entity):
	def __init__(self):
		self.i_clk  = Input (Wire())
		self.i_rst  = Input (Wire())
		self.i_ph0  = Input (Wire())
		self.o_strb = Output(t_vic_strb)

		self.ph0_1r = Signal(Wire())

	def _run(self):
		if self.i_clk.posedge():
			if self.ph0_1r.now == 1 and self.i_ph0.now == 0:
				self.o_strb.nxt <<= 1
				pass
			else:
				self.o_strb.nxt <<= self.o_strb.now + 1
			self.ph0_1r.nxt <<= self.i_ph0.now

			if self.o_strb.now[0]:
				bl.add(f"[STROBE] strobe = {self.o_strb.now.dump}")

			if self.i_rst.now:
				self.ph0_1r.nxt <<= 1
				self.o_strb.nxt <<= 0

	def _reset(self):
		pass
