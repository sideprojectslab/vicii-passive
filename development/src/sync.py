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

from   ezhdl      import *
from   vic_pkg    import *
import bus_logger as bl

UNLOCK_CYCLES = 3

ST_UNLOCKED = 0
ST_LLOCKING = 1
ST_LLOCKED  = 2
ST_LOCKED   = 3
ST_NUM      = 4

class Sync(Entity):

	def __init__(self):
		self.i_clk   = Input(Wire())
		self.i_rst   = Input(Wire())
		self.i_specs = Input (VicSpecs(H63))
		self.i_a     = Input (t_vic_addr)
		self.i_strb  = Input (t_vic_strb)
		self.o_lock  = Output(Wire())
		self.o_cycl  = Output(t_vic_cycl)
		self.o_xpos  = Output(t_vic_ppos)
		self.o_ypos  = Output(t_vic_ppos)

		self.state        = Signal(Unsigned(ST_UNLOCKED).span(ST_NUM))
		self.shreg_old    = Signal(Unsigned().bits(10))
		self.refpat       = Signal(self.shreg_old)
		self.count_unlock = Signal(Unsigned().upto(UNLOCK_CYCLES))
		self.cycl_i       = Signal(t_vic_cycl)
		self.ypos_i       = Signal(t_vic_ppos)

	@classmethod
	def is_refresh(cls, shreg) -> bool:
		return ((shreg == 0b1110010011) or
			    (shreg == 0b1001001110) or
			    (shreg == 0b0100111001) or
			    (shreg == 0b0011100100))


	def _run(self):
		if self.i_clk.posedge():
			shreg = Unsigned().bits(10)
			specs = self.i_specs

			shreg <<= join(self.shreg_old[8:], self.i_a[2:])

			if self.i_strb == 2:

				self.shreg_old <<= shreg

				if (self.cycl_i < specs.cycl - 1):
					self.cycl_i <<= self.cycl_i + 1
				else:
					self.cycl_i <<= 0

					if (self.ypos_i < specs.ylen - 1):
						self.ypos_i <<= self.ypos_i + 1
					else:
						self.ypos_i <<= 0


				if self.cycl_i == specs.CYCL_REF:

					if self.state == ST_UNLOCKED:
						if self.is_refresh(shreg):
							self.state  <<= ST_LLOCKING
							self.refpat <<= join(shreg[8:], shreg[8:6])
						else:
							# skip a cycle and try again
							self.cycl_i <<= specs.CYCL_REF + 2

					elif self.state == ST_LLOCKING:
						if (shreg == self.refpat):
							# if is_refresh(shreg) then
							self.state        <<= ST_LLOCKED
							self.count_unlock <<= UNLOCK_CYCLES
							self.refpat       <<= join(shreg[8:], shreg[8:6])
						else:
							# skip a cycle and start over
							self.state  <<= ST_UNLOCKED
							self.cycl_i <<= specs.CYCL_REF + 2

					elif self.state == ST_LLOCKED:
						if (shreg == 0b1111111111):
							self.state        <<= ST_LOCKED
							self.ypos_i       <<= specs.ylen - 1
							self.refpat       <<= 0b1110010011
							self.count_unlock <<= UNLOCK_CYCLES

						elif (shreg == self.refpat):
							self.refpat       <<= join(self.refpat[8:], self.refpat[8:6])
							self.count_unlock <<= UNLOCK_CYCLES

						elif (self.count_unlock != 0):
							self.refpat       <<= join(self.refpat[6:], self.refpat[8:6])
							self.count_unlock <<= self.count_unlock - 1

						else:
							# skip a cycle and start over
							self.state  <<= ST_UNLOCKED
							self.cycl_i <<= specs.CYCL_REF + 2

					elif self.state == ST_LOCKED:
						if (self.ypos_i == specs.ylen - 1):
							if (shreg == 0b1111111111):
								self.refpat       <<= 0b1110010011
								self.count_unlock <<= UNLOCK_CYCLES

							elif self.count_unlock != 0:
								self.refpat       <<= 0b1110010011
								self.count_unlock <<= self.count_unlock - 1

							else:
								# skip a cycle and start over
								self.state  <<= ST_UNLOCKED
								self.cycl_i <<= specs.CYCL_REF + 2

						else:
							if (shreg == self.refpat):
								self.refpat       <<= join(self.refpat[8:], self.refpat[8:6])
								self.count_unlock <<= UNLOCK_CYCLES

							elif self.count_unlock != 0:
								self.count_unlock <<= self.count_unlock - 1
								self.refpat       <<= join(self.refpat[8:], self.refpat[8:6])

							else:
								# skip a cycle and start over
								self.state  <<= ST_UNLOCKED
								self.cycl_i <<= specs.CYCL_REF + 2

			# advancing the pixel counter on odd strobe cycles
			if (self.i_strb[0]):
				if (self.o_xpos < specs.xlen - 1):
					self.o_xpos <<= self.o_xpos + 1
				else:
					self.o_xpos <<= 0

			# position outputs are latched on the last strobe of a character
			# cycle, so that they are constant and correct during the whole
			# cycle
			if (self.i_strb == 15):
				# cycl_i already contains the next cycle index
				self.o_cycl <<= self.cycl_i

				# y coordinate cycles automatically
				if (self.cycl_i == 0):
					if (self.o_ypos < specs.ylen - 1):
						self.o_ypos <<= self.o_ypos + 1
					else:
						self.o_ypos <<= 0

				# on the reference cycle we re-synchronize all counters with
				# appropriate offsets
				if (self.cycl_i == specs.CYCL_REF + 1):
					self.o_xpos <<= specs.xref

					if (self.ypos_i == 0):
						self.o_ypos <<= specs.yref

			self.o_lock <<= int(self.state == ST_LOCKED)

			if self.state == ST_LOCKED:
				bl.add(f"[SYNC] X-RASTER = {self.o_xpos.now.val}")
				bl.add(f"[SYNC] Y-RASTER = {self.o_ypos.now.val}")
				bl.add(f"[SYNC] CYCLE    = {self.o_cycl.now.val}")

			if self.i_rst:
				self.state        <<= ST_LOCKED
				self.count_unlock <<= UNLOCK_CYCLES
				self.shreg_old    <<= 0b111001
				self.refpat       <<= 0b1110010011
				self.cycl_i       <<= specs.CYCL_REF - 1
				self.o_cycl       <<= specs.CYCL_REF - 1
				self.ypos_i       <<= 0
				self.o_ypos       <<= 0
