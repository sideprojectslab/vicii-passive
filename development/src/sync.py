
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
			specs = self.i_specs.now

			shreg <<= join(self.shreg_old.now[8:], self.i_a.now[2:])

			if self.i_strb.now == 2:

				self.shreg_old.nxt <<= shreg

				if (self.cycl_i.now < specs.cycl - 1):
					self.cycl_i.nxt <<= self.cycl_i.now + 1
				else:
					self.cycl_i.nxt <<= 0

					if (self.ypos_i.now < specs.ylen - 1):
						self.ypos_i.nxt <<= self.ypos_i.now + 1
					else:
						self.ypos_i.nxt <<= 0


				if self.cycl_i.now == specs.CYCL_REF:

					if self.state.now == ST_UNLOCKED:
						print("Unlocked!!!")
						if self.is_refresh(shreg):
							self.state.nxt  <<= ST_LLOCKING
							self.refpat.nxt <<= join(shreg[8:], shreg[8:6])
						else:
							# skip a cycle and try again
							self.cycl_i.nxt <<= specs.CYCL_REF + 2

					elif self.state.now == ST_LLOCKING:
						if (shreg == self.refpat.now):
							# if is_refresh(shreg) then
							self.state.nxt        <<= ST_LLOCKED
							self.count_unlock.nxt <<= UNLOCK_CYCLES
							self.refpat.nxt       <<= join(shreg[8:], shreg[8:6])
						else:
							# skip a cycle and start over
							self.state.nxt  <<= ST_UNLOCKED
							self.cycl_i.nxt <<= specs.CYCL_REF + 2

					elif self.state.now == ST_LLOCKED:
						if (shreg == 0b1111111111):
							print("Locked!!!")
							self.state.nxt        <<= ST_LOCKED
							self.ypos_i.nxt       <<= specs.ylen - 1
							self.refpat.nxt       <<= 0b1110010011
							self.count_unlock.nxt <<= UNLOCK_CYCLES

						elif (shreg == self.refpat.now):
							self.refpat.nxt       <<= join(self.refpat.now[8:], self.refpat.now[8:6])
							self.count_unlock.nxt <<= UNLOCK_CYCLES

						elif (self.count_unlock.now != 0):
							self.refpat.nxt       <<= join(self.refpat.now[6:], self.refpat.now[8:6])
							self.count_unlock.nxt <<= self.count_unlock.now - 1

						else:
							# skip a cycle and start over
							self.state.nxt  <<= ST_UNLOCKED
							self.cycl_i.nxt <<= specs.CYCL_REF + 2

					elif self.state.now == ST_LOCKED:
						if (self.ypos_i.now == specs.ylen - 1):
							if (shreg == 0b1111111111):
								self.refpat.nxt       <<= 0b1110010011
								self.count_unlock.nxt <<= UNLOCK_CYCLES

							elif self.count_unlock.now != 0:
								self.refpat.nxt       <<= 0b1110010011
								self.count_unlock.nxt <<= self.count_unlock.now - 1

							else:
								# skip a cycle and start over
								self.state.nxt  <<= ST_UNLOCKED
								self.cycl_i.nxt <<= specs.CYCL_REF + 2

						else:
							if (shreg == self.refpat.now):
								self.refpat.nxt       <<= join(self.refpat.now[8:], self.refpat.now[8:6])
								self.count_unlock.nxt <<= UNLOCK_CYCLES

							elif self.count_unlock.now != 0:
								self.count_unlock.nxt <<= self.count_unlock.now - 1
								self.refpat.nxt       <<= join(self.refpat.now[8:], self.refpat.now[8:6])

							else:
								# skip a cycle and start over
								self.state.nxt  <<= ST_UNLOCKED
								self.cycl_i.nxt <<= specs.CYCL_REF + 2

			# advancing the pixel counter on odd strobe cycles
			if (self.i_strb.now[0]):
				if (self.o_xpos.now < specs.xlen - 1):
					self.o_xpos.nxt <<= self.o_xpos.now + 1
				else:
					self.o_xpos.nxt <<= 0

			# position outputs are latched on the last strobe of a character
			# cycle, so that they are constant and correct during the whole
			# cycle
			if (self.i_strb.now == 15):
				# cycl_i already contains the next cycle index
				self.o_cycl.nxt <<= self.cycl_i.now

				# y coordinate cycles automatically
				if (self.cycl_i.now == 0):
					if (self.o_ypos.now < specs.ylen - 1):
						self.o_ypos.nxt <<= self.o_ypos.now + 1
					else:
						self.o_ypos.nxt <<= 0

				# on the reference cycle we re-synchronize all counters with
				# appropriate offsets
				if (self.cycl_i.now == specs.CYCL_REF + 1):
					self.o_xpos.nxt <<= specs.xref

					if (self.ypos_i.now == 0):
						self.o_ypos.nxt <<= specs.yref

			self.o_lock.nxt <<= int(self.state.now == ST_LOCKED)

			if self.state.now == ST_LOCKED:
				bl.add(f"X-RASTER = {self.o_xpos.now}")
				bl.add(f"Y-RASTER = {self.o_ypos.now}")
				bl.add(f"CYCLE    = {self.o_cycl.now}")

			if self.i_rst.now:
				self.state.nxt        <<= ST_LOCKED
				self.count_unlock.nxt <<= UNLOCK_CYCLES
				self.shreg_old.nxt    <<= 0b111001
				self.refpat.nxt       <<= 0b1110010011
				self.cycl_i.nxt       <<= specs.CYCL_REF - 1
				self.o_cycl.nxt       <<= specs.CYCL_REF - 1
				self.ypos_i.nxt       <<= 0
				self.o_ypos.nxt       <<= 0
