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

from vic_pkg import *

log = []

def add(new):
	global log
	if isinstance(new, list):
		log.extend(new)
	else:
		log.append(new)


def clear():
	global log
	log = []


REG_NAMES = [
	"00-Sprite 0 X-position",
	"01-Sprite 0 Y-position",
	"02-Sprite 1 X-position",
	"03-Sprite 1 Y-position",
	"04-Sprite 2 X-position",
	"05-Sprite 2 Y-position",
	"06-Sprite 3 X-position",
	"07-Sprite 3 Y-position",
	"08-Sprite 4 X-position",
	"09-Sprite 4 Y-position",
	"10-Sprite 5 X-position",
	"11-Sprite 5 Y-position",
	"12-Sprite 6 X-position",
	"13-Sprite 6 Y-position",
	"14-Sprite 7 X-position",
	"15-Sprite 7 Y-position",
	"16-Sprite 8th X-position bit",
	"17-Control Register 1",
	"18-Raster Counter",
	"19-Light Pen X",
	"20-Light Pen Y",
	"21-Sprite Enabled",
	"22-Control Register 2",
	"23-Sprite Y Expansion",
	"24-Memory Pointers",
	"25-Interrupt Register",
	"26-Interrupt Enabled",
	"27-Sprite Data Priority",
	"28-Sprite Multicolor",
	"29-Sprite X Expansion",
	"30-Sprite-Sprite Collision",
	"31-Sprite-Data Collision",
	"32-Border Color",
	"33-Background Color 0",
	"34-Background Color 1",
	"35-Background Color 2",
	"36-Background Color 3",
	"37-Sprite Multicolor 0",
	"38-Sprite Multicolor 1",
	"39-Color Sprite 0",
	"40-Color Sprite 1",
	"41-Color Sprite 2",
	"42-Color Sprite 3",
	"43-Color Sprite 4",
	"44-Color Sprite 5",
	"45-Color Sprite 6",
	"46-Color Sprite 7",
	"47",
	"48",
	"49",
	"50",
	"51",
	"52",
	"53",
	"54",
	"55",
	"56",
	"57",
	"58",
	"59",
	"60",
	"61",
	"62",
	"63"
]

COLOR = [
	"Black"      , # 0000
	"White"      , # 0001
	"Red"        , # 0010
	"Cyan"       , # 0011
	"Purple"     , # 0100
	"Green"      , # 0101
	"Blue"       , # 0110
	"Yellow"     , # 0111
	"Orange"     , # 1000
	"Brown"      , # 1001
	"Pink"       , # 1010
	"Dark Grey"  , # 1011
	"Grey"       , # 1100
	"Light Green", # 1101
	"Light Blue" , # 1110
	"Light Grey"   # 1111
]

def get_video_mode(ecm, bmm, mcm):
	if(ecm == 0) and (bmm == 0) and (mcm == 0):
		mode = "STD_TEXT"
	elif (ecm == 0) and (bmm == 0) and (mcm == 1):
		mode = "MCL_TEXT"
	elif (ecm == 0) and (bmm == 1) and (mcm == 0):
		mode = "STD_BMAP"
	elif (ecm == 0) and (bmm == 1) and (mcm == 1):
		mode = "MCL_BMAP"
	elif (ecm == 1) and (bmm == 0) and (mcm == 0):
		mode = "ECM_TEXT"
	else:
		mode = "INVALID"
	return mode


def reg_write_analyze(reg, val, regs=t_vic_regs):
	ret = []
	name = REG_NAMES[reg]
	ret.append(f"[REGISTER] {name} Write: {val}")

	if reg in range(0, 16, 2):
		idx = reg // 2
		x_hi = (regs[16].val >> idx) & 1
		ret.append(f"    Sprite {idx} X (low) position => {val + (x_hi << 8)}")

	if reg in range(1, 16, 2):
		idx = reg // 2
		ret.append(f"    Sprite {idx} Y position => {val}")

	if reg == 17:
		ret.append(f"    Yscroll    => {val & 0b111}")
		ret.append(f"    RSEL       => {(val >> 3) & 1}")
		ret.append(f"    DEN        => {(val >> 4) & 1}")
		ecm = (val >> 6) & 1
		bmm = (val >> 5) & 1
		mcm = (regs[22].val >> 4) & 1
		mode = get_video_mode(ecm, bmm, mcm)
		ret.append(f"    Video Mode => {mode}")

	if reg == 22:
		ret.append(f"    Xscroll    => {val & 0b111}")
		ret.append(f"    CSEL       => {(val >> 3) & 1}")
		ecm = (regs[17].val >> 6) & 1
		bmm = (regs[17].val >> 5) & 1
		mcm = (val >> 4) & 1
		mode = get_video_mode(ecm, bmm, mcm)
		ret.append(f"    Video Mode => {mode}")

	if reg == 32:
		ret.append(f"    Border Color => {COLOR[val & 0xff]}")

	if reg in range(33, 37):
		idx = reg - 33
		ret.append(f"    Background Color [{idx}] => {COLOR[val & 0xff]}")

	return ret
