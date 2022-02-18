"""
==========================================================================
TileCL_test.py
==========================================================================
Test cases for Tile.

Author : Cheng Tan
  Date : Dec 28, 2019

"""

from pymtl3                               import *
from pymtl3.stdlib.test                   import TestSinkCL
from pymtl3.stdlib.test.test_srcs         import TestSrcRTL

from ..TileCL                             import TileCL
from ...lib.opt_type                      import *
from ...lib.messages                      import *
from ...fu.single.AdderRTL                import AdderRTL
from ...fu.single.MemUnitRTL              import MemUnitRTL
from ...fu.triple.ThreeMulAdderShifterRTL import ThreeMulAdderShifterRTL
from ...fu.flexible.FlexibleFuRTL         import FlexibleFuRTL
from ...mem.ctrl.CtrlMemCL                import CtrlMemCL

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, DUT, FunctionUnit, FuList, DataType, PredicateType,
                 CtrlType, ctrl_mem_size, data_mem_size,
                 num_tile_inports, num_tile_outports,
                 src_data, src_opt, src_const, sink_out ):

    s.num_tile_inports  = num_tile_inports
    s.num_tile_outports = num_tile_outports

    AddrType    = mk_bits( clog2( ctrl_mem_size ) )

    s.src_data  = [ TestSrcRTL( DataType, src_data[i]  )
                  for i in range( num_tile_inports  ) ]
    s.sink_out  = [ TestSinkCL( DataType, sink_out[i] )
                  for i in range( num_tile_outports ) ]

    s.dut = DUT( FunctionUnit, FuList, DataType, PredicateType, CtrlType,
                 ctrl_mem_size, data_mem_size, len(src_opt), src_const,
                 src_opt )

    for i in range( num_tile_inports ):
      connect( s.src_data[i].send, s.dut.recv_data[i] )
    for i in range( num_tile_outports ):
      connect( s.dut.send_data[i],  s.sink_out[i].recv )

    if MemUnitRTL in FuList:
      s.dut.to_mem_raddr.rdy   //= 0
      s.dut.from_mem_rdata.en  //= 0
      s.dut.from_mem_rdata.msg //= DataType( 0, 0 )
      s.dut.to_mem_waddr.rdy   //= 0
      s.dut.to_mem_wdata.rdy   //= 0

  def done( s ):
    done = True
    for i in range( s.num_tile_outports ):
      if not s.sink_out[i].done():# and not s.src_data[i].done():
        done = False
        break
    return done

  def line_trace( s ):
    return s.dut.line_trace()

def run_sim( test_harness, max_cycles=100 ):
  test_harness.elaborate()
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

def test_tile_alu():
  num_tile_inports  = 4
  num_tile_outports = 4
  num_xbar_inports  = 6
  num_xbar_outports = 8
  ctrl_mem_size     = 8
  data_mem_size     = 8
  num_fu_in         = 4 # number of inputs of FU is fixed inside the tile
  RouteType         = mk_bits( clog2( num_xbar_inports + 1 ) )
  AddrType          = mk_bits( clog2( ctrl_mem_size ) )
  FuInType          = mk_bits( clog2( num_fu_in + 1 ) )
  pickRegister      = [ FuInType( x+1 ) for x in range( num_fu_in ) ]
  DUT               = TileCL
  FunctionUnit      = FlexibleFuRTL
  FuList            = [AdderRTL, MemUnitRTL]
  DataType          = mk_data( 16, 1 )
  PredicateType     = mk_predicate( 1, 1 )
  CtrlType          = mk_ctrl( num_fu_in, num_xbar_inports, num_xbar_outports )
  src_opt           = [ CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                        RouteType(0), RouteType(0), RouteType(0), RouteType(0),
                        RouteType(4), RouteType(3), RouteType(0), RouteType(0)] ),
                        CtrlType( OPT_ADD, b1( 0 ), pickRegister, [
                        RouteType(0), RouteType(0), RouteType(0), RouteType(5),
                        RouteType(4), RouteType(1), RouteType(0), RouteType(0)] ),
                        CtrlType( OPT_SUB, b1( 0 ), pickRegister, [
                        RouteType(5), RouteType(0), RouteType(0), RouteType(5),
                        RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ) ]
  src_data          = [ [DataType(2, 1)],# DataType( 3, 1)],
                        [],#DataType(3, 1), DataType( 4, 1)],
                        [DataType(4, 1)],# DataType( 5, 1)],
                        [DataType(5, 1), DataType( 7, 1)] ]
  src_const         = [ DataType(5, 1), DataType(0, 0), DataType(7, 1) ]
  sink_out          = [ [DataType(5, 1, 0)],# DataType( 4, 1)],
                        [],
                        [],
                        [DataType(9, 1, 0), DataType( 5, 1, 0)]]#, DataType(4, 1)] ]
  th = TestHarness( DUT, FunctionUnit, FuList, DataType,
                    PredicateType, CtrlType,
                    ctrl_mem_size, data_mem_size,
                    num_tile_inports, num_tile_outports,
                    src_data, src_opt, src_const, sink_out )
  run_sim( th )

