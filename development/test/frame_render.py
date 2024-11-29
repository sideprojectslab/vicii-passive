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

from   ezpath  import *
from   ezhdl   import *
from   vic_pkg import *

import numpy as np
import matplotlib.pyplot as plt

MAX_HRES = 504
MAX_VRES = 312

class FrameRender(Entity):
	def __init__(self):
		self.i_clk  = Input(Wire())
		self.i_rst  = Input(Wire())
		self.i_push = Input(Wire())
		self.i_lstr = Input(Wire())
		self.i_lend = Input(Wire())
		self.i_fstr = Input(Wire())
		self.i_colr = Input(t_vic_colr)

		self.xpos  = 0
		self.ypos  = 0
		self.frame = np.array([[[127]*3]* MAX_HRES] * MAX_VRES)

		self.frame_count = 0

		self.color = [
			[0x00, 0x00, 0x00], # black
			[0xff, 0xff, 0xff], # white
			[0x9f, 0x4e, 0x44], # red
			[0x6a, 0xbf, 0xc6], # cyan
			[0xa0, 0x57, 0xa3], # purple
			[0x5c, 0xab, 0x5e], # green
			[0x50, 0x45, 0x9b], # blue
			[0xc9, 0xd4, 0x87], # yellow
			[0xa1, 0x68, 0x3c], # orange
			[0x6d, 0x54, 0x12], # brown
			[0xcb, 0x7e, 0x75], # pink
			[0x62, 0x62, 0x62], # dark grey
			[0x89, 0x89, 0x89], # grey
			[0x9a, 0xe2, 0x9b], # light green
			[0x88, 0x7e, 0xcb], # light blue
			[0xad, 0xad, 0xad]  # light grey
		]

		self.fig, self.ax = plt.subplots()
		self.im = self.ax.imshow(self.frame)  # Initial plot
		plt.axis('off')  # Optional: Hide axes for a cleaner look


	def _run(self):
		if self.i_clk.posedge():
			if self.i_push.now == 1:
				if(self.xpos > MAX_HRES - 1):
					self.xpos = MAX_HRES - 1

				if(self.ypos > MAX_VRES - 1):
					self.ypos = MAX_VRES - 1

				if self.i_lstr.now == 1:
					self.xpos = 0
					if self.i_fstr.now == 1:
						self.ypos = 0
						self.frame_count += 1

				self.frame[self.ypos][self.xpos] = self.color[self.i_colr.now]

				self.xpos += 1
				if self.i_lend.now == 1:
					self.ypos += 1

					if (self.frame_count == 2) or True:
						self.im.set_data(self.frame)  # Update the image data
						plt.draw()
						plt.pause(0.00001)

			if self.i_clk.now:
				pass
