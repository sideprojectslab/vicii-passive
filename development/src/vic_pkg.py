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

from __future__ import annotations

from ezhdl import *

H63 = "H63"
H64 = "H64"
H65 = "H65"

class VicSpecs(HwType):

	def __init__(self, version):

		self.CSMP_STRB = 15
		self.GSMP_STRB = 7
		self.CYCL_REF  = 14 # -1 from the docs because they start from 1... :(
		self.CYCL_VEND = 54 # like above :(
		self.CYCLE_YFF = 62 # same same :(

		if version == H63:
			self.cycl = 63       # number of character cycles in a line
			self.xref = 16       # value of xpos on the 1st clock cycle of the 1st character access after the refresh pattern
			self.xnul = 480 + 5  # solely needed to center the picture
			self.xend = 380 + 5  # ((xnul + xres) % xlen) - 1
			self.xlen = 504      # number of pixels in a line
			self.xres = 404      # visible pixels in a line
			self.xfvc = 24       # first video coordinate (after border)
			self.xlvc = 24 + 319 # last video coordinate  (before border)

			self.yref = 0
			self.ynul = 8
			self.yend = 8 + 283
			self.ylen = 312
			self.yres = 284
			self.yfvc = 51
			self.ylvc = 51 + 199

		elif version == H64:
			raise Exception(f"Version {version} not supported")
		elif version == H65:
			raise Exception(f"Version {version} not supported")
		else:
			raise Exception(f"Version {version} not supported")


t_vic_specs_h63 = VicSpecs(H63)
#t_vic_specs_h64 = VicSpecs(H64)
#t_vic_specs_h65 = VicSpecs(H65)

t_vic_regs = Array([Unsigned().bits(8)]*64)
t_vic_strb = Unsigned().bits(4)
t_vic_addr = Unsigned().bits(6)
t_vic_data = Unsigned().bits(12)
t_vic_grfx = Unsigned().bits(8)
t_vic_cycl = Unsigned().upto(65)
t_vic_ppos = Unsigned().upto(518)
t_vic_colr = Unsigned().bits(4)
