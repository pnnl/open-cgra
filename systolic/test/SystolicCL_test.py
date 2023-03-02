"""
==========================================================================
SystolicCL_test.py
==========================================================================
Test cases for Systolic Array with CL data/config memory.

Author : Cheng Tan
  Date : Dec 28, 2019

"""

from pymtl3                       import *
from pymtl3.stdlib.test           import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL

from ...lib.opt_type              import *
from ...lib.messages              import *
from ...lib.ctrl_helper           import *

from ...fu.flexible.FlexibleFuRTL import FlexibleFuRTL
from ...fu.single.AdderRTL        import AdderRTL
from ...fu.single.MemUnitRTL      import MemUnitRTL
from ...fu.double.SeqMulAdderRTL  import SeqMulAdderRTL
from ..SystolicCL                 import SystolicCL

import os

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, DUT, FunctionUnit, FuList, DataType, PredicateType,
                 CtrlType, width, height, ctrl_mem_size, data_mem_size,
                 src_opt, preload_data, preload_const, sink_out ):

    s.num_tiles = width * height
    AddrType = mk_bits( clog2( ctrl_mem_size ) )

    s.sink_out  = [ TestSinkCL( DataType, sink_out[i] )
                  for i in range( height-1 ) ]

    s.dut = DUT( FunctionUnit, FuList, DataType, PredicateType, CtrlType,
                 width, height, ctrl_mem_size, data_mem_size, ctrl_mem_size,
                 src_opt, preload_data, preload_const )

    for i in range( height-1 ):
      connect( s.dut.send_data[i],  s.sink_out[i].recv )

  def line_trace( s ):
    return s.dut.line_trace()

def run_sim( test_harness, max_cycles=6 ):
  test_harness.elaborate()
  test_harness.apply( SimulationPass() )
  test_harness.sim_reset()

  # Run simulation
  ncycles = 0
  print()
  print( "{}:{}".format( ncycles, test_harness.line_trace() ))
  while ncycles < max_cycles:
    test_harness.tick()
    ncycles += 1
    print( "----------------------------------------------------" )
    print( "{}:{}".format( ncycles, test_harness.line_trace() ))

  # Check timeout
#  assert ncycles < max_cycles

  test_harness.tick()
  test_harness.tick()
  test_harness.tick()

# ------------------------------------------------------------------
# To emulate systolic array
# left bottom is 0, 0
# right top   is 1, 1
# 1: North, 2: South, 3: West, 4: East
# 5 - 8: registers
# ------------------------------------------------------------------
def test_systolic_2x2():
  num_tile_inports  = 4
  num_tile_outports = 4
  num_xbar_inports  = 6
  num_xbar_outports = 8
  ctrl_mem_size     = 8
  width             = 2
  height            = 3
  RouteType         = mk_bits( clog2( num_xbar_inports + 1 ) )
  AddrType          = mk_bits( clog2( ctrl_mem_size ) )
  num_tiles         = width * height
  ctrl_mem_size     = 8
  data_mem_size     = 2
  # number of inputs of FU is fixed inside the tile
  num_fu_in         = 4

  DUT               = SystolicCL
  FunctionUnit      = FlexibleFuRTL
  FuList            = [AdderRTL, MemUnitRTL, SeqMulAdderRTL]
  DataType          = mk_data( 16, 1 )
  PredicateType     = mk_predicate( 1, 1 )
  CtrlType          = mk_ctrl( num_fu_in, num_xbar_inports, num_xbar_outports )
  FuInType          = mk_bits( clog2( num_fu_in + 1 ) )
  pickRegister      = [ FuInType( x+1 ) for x in range( num_fu_in ) ]
  
  # Brief explanation about the control signal:
  # CtrlType(optType, isCurOptPredicateBased, [registersUsedForComputation], [portsWithDataToBeRouted], [predicatesForFutureComputation])
  #  - `optType` can be found in lib/opt_type.py, there are currently more or less 40 operation/computation types supported, which represented in 6 bits.
  #  - `isCurOptPredicateBased` indicates whether this operation is predicate-based. Specifically, if set as `false`, this operation will be executed.
  #    If `true`, the execution of this operation depends on the predicate bit embedded in the data message. Normally, the predicate in the data message
  #    is calculated by the `phi` operation (to enable control-flow). Just set this field as `b1(0)` if no control-flow is involved.
  #  - `[registersUsedForComputation]` is a list contains `num_fu_in` (i.e., 4 in this case) items. It indicates the register ID that will be used
  #    for computation. There are 4 possible inputs in this tile configuration, so the length of the list is 4. Note that maybe less than 4 operations
  #    are used for computations. For example, `NOT` requires one, `Add` requires two, `MAC` requires three, and the complex FU that contains two
  #    parallel adders require four. In addition, the register ID starts from 1 as 0 is reserved to indicate invalid. For example, if data `a` is
  #    located in the second register while data `b` is located in the first register, to perform `a - b`, `[registersUsedForComputation]` should be
  #    set as `[2,1,0,0]`.
  #  - `[portsWithDataToBeRouted]` indicates how the data will be routed on the xbar. It contains `num_xbar_outports` items, which means each outport
  #    picks one inport for data delivery. In this case, we can see there are 8 items. The first 4 are the tile's outports (i.e., North, South, West,
  #    East). The second 4 are the 4 registers used for computation (i.e., `[registersUsedForComputation]`). Each item can choose the value ranging
  #    from 0 to 6. 0 is reserved indicating invalid, 1-4 indicate the inport N, S, W, and E. And 5-6 indicate the two outports of the functional unit.
  #  - `[predicatesForFutureComputation]` is used to indicate that the predicate bit in the result message will be calculated based on the data coming
  #    from this port. Ignore this field if no control-flow is involved.
  
  src_opt       = [[CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [ 
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                   ],
                   [CtrlType( OPT_NAH, b1( 0 ), pickRegister, [ 
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [ 
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_LD_CONST, b1( 0 ), pickRegister, [
                    RouteType(5), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0)] ),
                   ],
                   [CtrlType( OPT_NAH, b1( 0 ), pickRegister, [ 
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST, b1( 0 ), pickRegister, [
                    RouteType(2), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST, b1( 0 ), pickRegister, [
                    RouteType(2), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST, b1( 0 ), pickRegister, [
                    RouteType(2), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                   ],
                   [CtrlType( OPT_NAH, b1( 0 ), pickRegister, [ 
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_NAH, b1( 0 ), pickRegister, [ 
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST_ADD, b1( 0 ), pickRegister, [ 
                    RouteType(2), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST_ADD, b1( 0 ), pickRegister, [
                    RouteType(2), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                   ],
                   [CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(0), RouteType(0)] ),
                   ],
                   [CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                    CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                    CtrlType( OPT_NAH, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(0),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST_ADD, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                    CtrlType( OPT_MUL_CONST_ADD, b1( 0 ), pickRegister, [
                    RouteType(0), RouteType(0), RouteType(0), RouteType(5),
                    RouteType(2), RouteType(0), RouteType(3), RouteType(0)] ),
                   ]
                  ]
  preload_mem   = [DataType(1, 1), DataType(2, 1), DataType(3, 1), DataType(4, 1)]
  preload_const = [[DataType(0, 1), DataType(1, 1)],
                   [DataType(0, 0), DataType(2, 1), DataType(3, 1)], # offset address used for loading
                   [DataType(2, 1)], [DataType(4, 1)], # preloaded data
                   [DataType(6, 1)], [DataType(8, 1)]] # preloaded data
  """
  1 3      2 6     14 20
       x        =  
  2 4      4 8     30 44
  """
  sink_out = [[DataType(14, 1), DataType(20, 1)], [DataType(30, 1), DataType(44, 1)]]
  th = TestHarness( DUT, FunctionUnit, FuList, DataType, PredicateType,
                    CtrlType, width, height, ctrl_mem_size, len(preload_mem),
                    src_opt, preload_mem, preload_const, sink_out )
  run_sim( th )


