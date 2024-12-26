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

from ezhdl            import *
from vic_pkg          import *
from strobe           import *
from registers        import *
from sync             import *
from bad_line_detect  import *
from video_matrix     import *
from border           import *
from graphics_gen     import *
from sprites          import *
from graphics_mux     import *


class VicPassive(Entity):
	def __init__(self):
		self.i_clk = Input(Wire())
		self.i_rst = Input(Wire())
		self.i_ph0 = Input(Wire())
		self.i_a   = Input(t_vic_addr)
		self.i_db  = Input(t_vic_data)
		self.i_aec = Input(Wire())
		self.i_cs  = Input(Wire())
		self.i_rw  = Input(Wire())

		self.o_push = Output(Wire())
		self.o_lstr = Output(Wire())
		self.o_lend = Output(Wire())
		self.o_fstr = Output(Wire())
		self.o_colr = Output(t_vic_colr)

		self.specs = Signal(VicSpecs(H63))

		# generates 16 strobes for each cycle of phy0
		self.e_strobe = Strobe()
		self.e_strobe.i_clk <<= self.i_clk
		self.e_strobe.i_rst <<= self.i_rst
		self.e_strobe.i_ph0 <<= self.i_ph0

		# register interface
		self.e_registers = Registers()
		self.e_registers.i_clk  <<= self.i_clk
		self.e_registers.i_rst  <<= self.i_rst
		self.e_registers.i_strb <<= self.e_strobe.o_strb
		self.e_registers.i_a    <<= self.i_a
		self.e_registers.i_db   <<= self.i_db
		self.e_registers.i_cs   <<= self.i_cs
		self.e_registers.i_rw   <<= self.i_rw

		# synchronixe veritcal and horizontal position to the input raster
		self.e_sync = Sync()
		self.e_sync.i_clk   <<= self.i_clk
		self.e_sync.i_rst   <<= self.i_rst
		self.e_sync.i_a     <<= self.i_a
		self.e_sync.i_strb  <<= self.e_strobe.o_strb
		self.e_sync.i_specs <<= self.specs

		# detect bad-lines
		self.e_bdln_detect = BadLineDetect()
		self.e_bdln_detect.i_clk   <<= self.i_clk
		self.e_bdln_detect.i_rst   <<= self.i_rst
		self.e_bdln_detect.i_specs <<= self.specs
		self.e_bdln_detect.i_aec   <<= self.i_aec
		self.e_bdln_detect.i_strb  <<= self.e_strobe.o_strb
		self.e_bdln_detect.i_cycl  <<= self.e_sync.o_cycl
		self.e_bdln_detect.i_ypos  <<= self.e_sync.o_ypos

		# video matrix
		self.e_video_matrix = VideoMatrix(g_mark_bdln=False)
		self.e_video_matrix.i_clk   <<= self.i_clk
		self.e_video_matrix.i_rst   <<= self.i_rst
		self.e_video_matrix.i_bdln  <<= self.e_bdln_detect.o_bdln
		self.e_video_matrix.i_cycl  <<= self.e_sync.o_cycl
		self.e_video_matrix.i_db    <<= self.i_db
		self.e_video_matrix.i_specs <<= self.specs
		self.e_video_matrix.i_strb  <<= self.e_strobe.o_strb
		self.e_video_matrix.i_ypos  <<= self.e_sync.o_ypos

		# boarder unit
		self.e_border = Border()
		self.e_border.i_clk   <<= self.i_clk
		self.e_border.i_rst   <<= self.i_rst
		self.e_border.i_specs <<= self.specs
		self.e_border.i_strb  <<= self.e_strobe.o_strb
		self.e_border.i_regs  <<= self.e_registers.o_regs
		self.e_border.i_cycl  <<= self.e_sync.o_cycl
		self.e_border.i_xpos  <<= self.e_sync.o_xpos
		self.e_border.i_ypos  <<= self.e_sync.o_ypos

		# graphics generator
		self.e_gfx_gen = GraphicsGen()
		self.e_gfx_gen.i_clk  <<= self.i_clk
		self.e_gfx_gen.i_rst  <<= self.i_rst
		self.e_gfx_gen.i_data <<= self.e_video_matrix.o_cc
		self.e_gfx_gen.i_grfx <<= self.e_video_matrix.o_gg
		self.e_gfx_gen.i_actv <<= self.e_video_matrix.o_en
		self.e_gfx_gen.i_regs <<= self.e_registers.o_regs
		self.e_gfx_gen.i_strb <<= self.e_strobe.o_strb
		self.e_gfx_gen.i_vbrd <<= self.e_border.o_vbrd

		# sprites
		self.e_sprites = Sprites()
		self.e_sprites.i_clk     <<= self.i_clk
		self.e_sprites.i_rst     <<= self.i_rst
		self.e_sprites.i_specs   <<= self.specs
		self.e_sprites.i_regs    <<= self.e_registers.o_regs
		self.e_sprites.i_strb    <<= self.e_strobe.o_strb
		self.e_sprites.i_cycl    <<= self.e_sync.o_cycl
		self.e_sprites.i_xpos    <<= self.e_sync.o_xpos
		self.e_sprites.i_ypos    <<= self.e_sync.o_ypos
		self.e_sprites.i_data    <<= self.i_db

		# graphics mux
		self.e_gfx_mux = GraphicsMux(g_mark_lines = False)
		self.e_gfx_mux.i_clk       <<= self.i_clk
		self.e_gfx_mux.i_rst       <<= self.i_rst
		self.e_gfx_mux.i_specs     <<= self.specs
		self.e_gfx_mux.i_strb      <<= self.e_strobe.o_strb
		self.e_gfx_mux.i_xpos      <<= self.e_sync.o_xpos
		self.e_gfx_mux.i_ypos      <<= self.e_sync.o_ypos
		self.e_gfx_mux.i_bord_actv <<= self.e_border.o_bord
		self.e_gfx_mux.i_bord_colr <<= self.e_border.o_colr
		self.e_gfx_mux.i_grfx_colr <<= self.e_gfx_gen.o_colr
		self.e_gfx_mux.i_grfx_bgnd <<= self.e_gfx_gen.o_bgnd
		self.e_gfx_mux.i_sprt_actv <<= self.e_sprites.o_actv
		self.e_gfx_mux.i_sprt_prio <<= self.e_sprites.o_prio
		self.e_gfx_mux.i_sprt_colr <<= self.e_sprites.o_colr

		# outputs
		self.o_push <<= self.e_gfx_mux.o_push
		self.o_colr <<= self.e_gfx_mux.o_colr
		self.o_lstr <<= self.e_gfx_mux.o_lstr
		self.o_fstr <<= self.e_gfx_mux.o_fstr
		self.o_lend <<= self.e_gfx_mux.o_lend
