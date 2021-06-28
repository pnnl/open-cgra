"""
==========================================================================
TileRTL_test.py
==========================================================================
Test cases for Tile.

Author : Cheng Tan
  Date : Mar 2, 2019

"""

from pymtl3                               import *
from pymtl3.stdlib.test                   import TestSinkCL
from pymtl3.stdlib.test.test_srcs         import TestSrcRTL

from ..TileRTL                            import TileRTL
from ...lib.opt_type                      import *
from ...lib.messages                      import *
from ...fu.triple.ThreeMulAdderShifterRTL import ThreeMulAdderShifterRTL
from ...fu.flexible.FlexibleFuRTL         import FlexibleFuRTL
from ...fu.single.AdderRTL                import AdderRTL
from ...fu.single.MemUnitRTL              import MemUnitRTL
from ...fu.single.MulRTL                  import MulRTL
from ...fu.single.SelRTL                  import SelRTL
from ...fu.single.ShifterRTL              import ShifterRTL
from ...fu.single.LogicRTL                import LogicRTL
from ...fu.single.PhiRTL                  import PhiRTL
from ...fu.single.CompRTL                 import CompRTL
from ...fu.single.BranchRTL               import BranchRTL
from ...fu.triple.ThreeMulAdderShifterRTL import ThreeMulAdderShifterRTL
from ...mem.ctrl.CtrlMemRTL               import CtrlMemRTL

from pymtl3.passes.backends.verilog       import TranslationImportPass

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, DUT, FunctionUnit, FuList, DataType, CtrlType,
                 ctrl_mem_size, data_mem_size,
                 num_fu_inports, num_fu_outports,
                 src_data, src_opt, opt_waddr, sink_out ):

#    s.num_tile_inports  = num_tile_inports
#    s.num_tile_outports = num_tile_outports

    AddrType    = mk_bits( clog2( ctrl_mem_size ) )

    s.src_opt   = TestSrcRTL( CtrlType, src_opt )
    s.opt_waddr = TestSrcRTL( AddrType, opt_waddr )
    s.src_data  = [ TestSrcRTL( DataType, src_data[i]  )
                  for i in range( 4 ) ]
    s.sink_out  = [ TestSinkCL( DataType, sink_out[i] )
                  for i in range( 4 ) ]

    s.dut = DUT( DataType, CtrlType, ctrl_mem_size, data_mem_size,
                 len(src_opt), num_fu_inports, num_fu_outports,
                 4, 4, FunctionUnit, FuList )

    connect( s.src_opt.send,   s.dut.recv_wopt  )
    connect( s.opt_waddr.send, s.dut.recv_waddr )

    for i in range( 4 ):
      connect( s.src_data[i].send, s.dut.recv_data[i] )
    for i in range( 4 ):
      connect( s.dut.send_data[i],  s.sink_out[i].recv )

    s.dut.to_mem_raddr.rdy   //= 0
    s.dut.from_mem_rdata.en  //= 0
    s.dut.from_mem_rdata.msg //= DataType( 0, 0 )
    s.dut.to_mem_waddr.rdy   //= 0
    s.dut.to_mem_wdata.rdy   //= 0

  def done( s ):
    done = True
    for i in range( 4 ):
      if not s.sink_out[i].done():# and not s.src_data[i].done():
        done = False
        break
    return done

  def line_trace( s ):
    return s.dut.line_trace()

def run_sim( test_harness, max_cycles=100 ):
  test_harness.elaborate()
  test_harness.dut.verilog_translate_import = True
  test_harness.dut.config_verilog_import = VerilatorImportConfigs(vl_Wno_list =         ['UNSIGNED', 'UNOPTFLAT', 'WIDTH', 'WIDTHCONCAT', 'ALWCOMBORDER'])
  test_harness = TranslationImportPass()(test_harness)
  test_harness.apply( SimulationPass() )
  test_harness.sim_reset()

  # Run simulation
  ncycles = 0
  print()
  print( "{}:{}".format( ncycles, test_harness.line_trace() ))
  while not test_harness.done() and ncycles < max_cycles:
    test_harness.tick()
    ncycles += 1
    print( "{}:{}".format( ncycles, test_harness.line_trace() ))

  # Check timeout
  assert ncycles < max_cycles

  test_harness.tick()
  test_harness.tick()
  test_harness.tick()

import platform
import pytest

@pytest.mark.skipif('Linux' not in platform.platform(),
                    reason="requires linux (gcc)")
def test_tile_alu():
  num_connect_inports  = 4
  num_connect_outports = 4
  num_fu_inports    = 4
  num_fu_outports   = 2
  num_xbar_inports  = num_fu_outports + num_connect_inports
  num_xbar_outports = num_fu_inports + num_connect_outports
  ctrl_mem_size     = 3
  data_mem_size     = 8
  num_fu_in         = 4
  RouteType    = mk_bits( clog2( num_xbar_inports + 1 ) )
  AddrType     = mk_bits( clog2( ctrl_mem_size ) )
  DUT          = TileRTL
  FunctionUnit = FlexibleFuRTL
  FuList       = [ AdderRTL, MulRTL, LogicRTL, ShifterRTL, PhiRTL, CompRTL, BranchRTL, MemUnitRTL, SelRTL ]
  DataType     = mk_data( 32, 1 )
  CtrlType     = mk_ctrl( num_fu_in, num_xbar_inports, num_xbar_outports )
  FuInType     = mk_bits( clog2( num_fu_in + 1 ) )
  pickRegister = [ FuInType( x+1 ) for x in range( num_fu_in ) ]
  opt_waddr    = [ AddrType( 0 ), AddrType( 1 ), AddrType( 2 ) ]

  src_opt      = [ CtrlType( OPT_NAH, pickRegister, [
                   RouteType(0), RouteType(0), RouteType(0), RouteType(0),
                   RouteType(4), RouteType(3), RouteType(0), RouteType(0)] ),
                   CtrlType( OPT_ADD, pickRegister, [
                   RouteType(0), RouteType(0), RouteType(0), RouteType(5),
                   RouteType(4), RouteType(1), RouteType(0), RouteType(0)] ),
                   CtrlType( OPT_SUB, pickRegister, [
                   RouteType(5), RouteType(0), RouteType(0), RouteType(5),
                   RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ) ]
  src_data     = [ [DataType(2, 1)],# DataType( 3, 1)],
                   [],#DataType(3, 1), DataType( 4, 1)],
                   [DataType(4, 1)],# DataType( 5, 1)],
                   [DataType(5, 1), DataType( 7, 1)] ]
  src_const    = [ DataType(5, 1), DataType(0, 0), DataType(7, 1) ]
  sink_out     = [ [DataType(5, 1)],# DataType( 4, 1)],
                   [],
                   [],
                   [DataType(9, 1), DataType( 5, 1)]]

  """
  src_opt      = [ CtrlType( OPT_NAH, [
                   RouteType(4), RouteType(3), RouteType(2), RouteType(1),
                   RouteType(4), RouteType(3), RouteType(2), RouteType(1)] ),
                   CtrlType( OPT_ADD, [
                   RouteType(3), RouteType(3), RouteType(3), RouteType(5),
                   RouteType(4), RouteType(1), RouteType(1), RouteType(1)] ),
                   CtrlType( OPT_SUB, [
                   RouteType(5), RouteType(5), RouteType(2), RouteType(2),
                   RouteType(1), RouteType(1), RouteType(1), RouteType(1)] ) ]
  src_data     = [ [DataType(2, 1), DataType( 3, 1)],
                   [DataType(3, 1), DataType( 4, 1)],
                   [DataType(4, 1), DataType( 5, 1)],
                   [DataType(5, 1), DataType( 6, 1)] ]
  sink_out     = [ [DataType(5, 1), DataType( 5, 1), DataType( 3, 1)],
                   [DataType(4, 1), DataType( 5, 1), DataType( 3, 1)],
                   [DataType(3, 1), DataType( 5, 1)],
                   [DataType(2, 1), DataType( 9, 1)] ]
  """
  th = TestHarness( DUT, FunctionUnit, FuList, DataType, CtrlType,
                    ctrl_mem_size, data_mem_size,
                    num_fu_inports, num_fu_outports,
                    src_data, src_opt, opt_waddr, sink_out )
  run_sim( th )

