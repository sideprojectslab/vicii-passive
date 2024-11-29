
from ezhdl           import *
from vic_pkg         import *
from strobe          import *
from registers       import *
from sync            import *
from bad_line_detect import *
from video_matrix    import *
from border          import *
from graphics_gen    import *
from graphics_mux    import *


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
		self.regs  = Signal(t_vic_regs)

		self.strb  = Signal(t_vic_strb)
		self.cycl  = Signal(t_vic_cycl)
		self.lock  = Signal(Wire())
		self.xpos  = Signal(t_vic_ppos)
		self.ypos  = Signal(t_vic_ppos)
		self.bdln  = Signal(Wire())

		self.cc_vm = Signal(t_vic_data)
		self.gg_vm = Signal(t_vic_grfx)
		self.en_vm = Signal(Wire())

		self.bord_actv = Signal(Wire())
		self.bord_colr = Signal(t_vic_colr)

		self.grfx_colr = Signal(t_vic_colr)
		self.grfx_bgnd = Signal(Wire())

		self.sprt_actv = Signal(Wire())
		self.sprt_prio = Signal(Wire())
		self.sprt_colr = Signal(t_vic_colr)

		# generates 16 strobes for each cycle of phy0
		self.e_strobe = Strobe()
		self.e_strobe.i_clk  << self.i_clk
		self.e_strobe.i_rst  << self.i_rst
		self.e_strobe.i_ph0  << self.i_ph0
		self.e_strobe.o_strb >> self.strb

		# register interface
		self.e_registers = Registers()
		self.e_registers.i_clk  << self.i_clk
		self.e_registers.i_rst  << self.i_rst
		self.e_registers.i_strb << self.strb
		self.e_registers.i_a    << self.i_a
		self.e_registers.i_db   << self.i_db
		self.e_registers.i_cs   << self.i_cs
		self.e_registers.i_rw   << self.i_rw
		self.e_registers.regs   >> self.regs

		# synchronixe veritcal and horizontal position to the input raster
		self.e_sync = Sync()
		self.e_sync.i_clk   << self.i_clk
		self.e_sync.i_rst   << self.i_rst
		self.e_sync.i_a     << self.i_a
		self.e_sync.i_strb  << self.strb
		self.e_sync.i_specs << self.specs
		self.e_sync.o_lock  >> self.lock
		self.e_sync.o_cycl  >> self.cycl
		self.e_sync.o_xpos  >> self.xpos
		self.e_sync.o_ypos  >> self.ypos

		# detect bad-lines
		self.e_bdln_detect = BadLineDetect()
		self.e_bdln_detect.i_clk   << self.i_clk
		self.e_bdln_detect.i_rst   << self.i_rst
		self.e_bdln_detect.i_specs << self.specs
		self.e_bdln_detect.i_aec   << self.i_aec
		self.e_bdln_detect.i_strb  << self.strb
		self.e_bdln_detect.i_cycl  << self.cycl
		self.e_bdln_detect.i_ypos  << self.ypos
		self.e_bdln_detect.o_bdln  >> self.bdln

		# video matrix
		self.e_video_matrix = VideoMatrix(g_mark_bdln=False)
		self.e_video_matrix.i_clk   << self.i_clk
		self.e_video_matrix.i_rst   << self.i_rst
		self.e_video_matrix.i_bdln  << self.bdln
		self.e_video_matrix.i_cycl  << self.cycl
		self.e_video_matrix.i_db    << self.i_db
		self.e_video_matrix.i_specs << self.specs
		self.e_video_matrix.i_strb  << self.strb
		self.e_video_matrix.i_ypos  << self.ypos
		self.e_video_matrix.o_cc    >> self.cc_vm
		self.e_video_matrix.o_gg    >> self.gg_vm
		self.e_video_matrix.o_en    >> self.en_vm

		# boarder unit
		self.e_border = Border()
		self.e_border.i_clk   << self.i_clk
		self.e_border.i_rst   << self.i_rst
		self.e_border.i_specs << self.specs
		self.e_border.i_strb  << self.strb
		self.e_border.i_regs  << self.regs
		self.e_border.i_cycl  << self.cycl
		self.e_border.i_xpos  << self.xpos
		self.e_border.i_ypos  << self.ypos
		self.e_border.o_bord  >> self.bord_actv
		self.e_border.o_colr  >> self.bord_colr

		# graphics generator
		self.e_gfx_gen = GraphicsGen()
		self.e_gfx_gen.i_clk   << self.i_clk
		self.e_gfx_gen.i_rst   << self.i_rst
		self.e_gfx_gen.i_data  << self.cc_vm
		self.e_gfx_gen.i_grfx  << self.gg_vm
		self.e_gfx_gen.i_en    << self.en_vm
		self.e_gfx_gen.i_regs  << self.regs
		self.e_gfx_gen.i_strb  << self.strb
		self.e_gfx_gen.o_colr  >> self.grfx_colr
		self.e_gfx_gen.o_bgnd  >> self.grfx_bgnd

		# graphics mux
		self.e_gfx_mux = GraphicsMux(g_mark_lines = True)
		self.e_gfx_mux.i_clk       << self.i_clk
		self.e_gfx_mux.i_rst       << self.i_rst
		self.e_gfx_mux.i_specs     << self.specs
		self.e_gfx_mux.i_strb      << self.strb
		self.e_gfx_mux.i_xpos      << self.xpos
		self.e_gfx_mux.i_ypos      << self.ypos
		self.e_gfx_mux.i_bord_actv << self.bord_actv
		self.e_gfx_mux.i_bord_colr << self.bord_colr
		self.e_gfx_mux.i_grfx_colr << self.grfx_colr
		self.e_gfx_mux.i_grfx_bgnd << self.grfx_bgnd
		self.e_gfx_mux.i_sprt_actv << self.sprt_actv
		self.e_gfx_mux.i_sprt_prio << self.sprt_prio
		self.e_gfx_mux.i_sprt_colr << self.sprt_colr
		self.e_gfx_mux.o_push      >> self.o_push
		self.e_gfx_mux.o_colr      >> self.o_colr
		self.e_gfx_mux.o_lstr      >> self.o_lstr
		self.e_gfx_mux.o_fstr      >> self.o_fstr
		self.e_gfx_mux.o_lend      >> self.o_lend