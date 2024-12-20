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

RAM_LEN  = 40

class VideoMatrix(Entity):

	def __init__(self, g_mark_bdln):
		self.g_mark_bdln = g_mark_bdln

		self.i_clk      = Input (Wire())
		self.i_rst      = Input (Wire())
		self.i_specs    = Input (VicSpecs(H63))
		self.i_strb     = Input (t_vic_strb)
		self.i_cycl     = Input (t_vic_cycl)
		self.i_bdln     = Input (Wire())
		self.i_ypos     = Input (t_vic_ppos)
		self.i_db       = Input (t_vic_data)
		self.o_cc       = Output(t_vic_data)
		self.o_gg       = Output(t_vic_grfx)
		self.o_en       = Output(Wire()    )

		self.ram        = Signal(Array([t_vic_data]*RAM_LEN))
		self.ram_wadd   = Signal(Unsigned().span(RAM_LEN))
		self.ram_radd   = Signal(Unsigned().span(RAM_LEN))
		self.count_line = Signal(Unsigned().upto(8)) # intentional for parking
		self.count_cycl = Signal(Unsigned().span(RAM_LEN))

	def _run(self):

		if self.i_clk.posedge():
			specs = self.i_specs.now
			CYCL_REF = specs.CYCL_REF

			# c-accesses are most stable on strobe 14-15
			if (self.i_strb.now == 13):
				if (self.i_cycl.now == CYCL_REF):
					self.ram_wadd.nxt <<= 0
				elif (self.ram_wadd.now < RAM_LEN - 1):
					self.ram_wadd.nxt <<= self.ram_wadd.now + 1

				if (self.i_bdln.now == 1):
					if (self.i_cycl.now == CYCL_REF):
						self.ram.nxt[self.ram_wadd.now] <<= self.i_db.now
						self.count_line.nxt <<= 0

					elif (self.ram_wadd.now < RAM_LEN - 1):
						# same, but without resetting the line counter
						self.ram.nxt[self.ram_wadd.now] <<= self.i_db.now
				else:
					if (self.i_cycl.now == CYCL_REF) and (self.count_line.now != 8):
						self.count_line.nxt <<= self.count_line.now + 1


			# start video matrix read soon enough for the data to be available
			# when it needs to be produced on the output
			if (self.i_strb.now == 2):
				if (self.count_cycl.now < RAM_LEN):
					self.count_cycl.nxt <<= self.count_cycl.now + 1

				if (self.i_cycl.now == CYCL_REF + 1):
					self.ram_radd.nxt   <<= 0
					self.count_cycl.nxt <<= 0

				elif (self.ram_radd.now < RAM_LEN - 1):
					self.ram_radd.nxt <<= self.ram_radd.now + 1

			if (self.i_strb.now == 7):
				if ((self.count_cycl.now != RAM_LEN) and
				    (self.i_ypos.now >= specs.yfvc ) and
				    (self.i_ypos.now <= specs.ylvc )):
					self.o_en.nxt <<= 1
					self.o_gg.nxt <<= self.i_db.now[8:0]
					self.o_cc.nxt <<= self.ram.now[self.ram_radd.now]

				elif (self.count_cycl.now != RAM_LEN):
					self.o_en.nxt <<= 1
					self.o_gg.nxt <<= self.i_db.now[8:0]
					self.o_cc.nxt <<= 0

				else:
					self.o_en.nxt <<= 0
					self.o_gg.nxt <<= 0
					self.o_cc.nxt <<= 0

			if self.i_rst.now:
				for i in range(RAM_LEN):
					self.ram.nxt[i] <<= 0
				self.o_en.nxt <<= 0
				self.o_gg.nxt <<= 0
				self.o_cc.nxt <<= 0


	def _rst(self):
		pass
