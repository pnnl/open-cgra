"""
==========================================================================
BranchRTL_test.py
==========================================================================
Test cases for functional unit branch.

Author : Cheng Tan
  Date : November 27, 2019

"""

from pymtl3                       import *
from pymtl3.stdlib.test           import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL

from ..BranchRTL                  import BranchRTL
from ....lib.opt_type             import *
from ....lib.messages             import *

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, FunctionUnit, DataType, PredicateType, CtrlType,
                 num_inports, num_outports, data_mem_size,
                 src_comp, src_predicate, src_opt, sink_if, sink_else ):

    s.src_comp      = TestSrcRTL( DataType,      src_comp      )
    s.src_predicate = TestSrcRTL( PredicateType, src_predicate )
    s.src_opt       = TestSrcRTL( CtrlType,      src_opt       )
    s.sink_if       = TestSinkCL( DataType,      sink_if       )
    s.sink_else     = TestSinkCL( DataType,      sink_else     )

    s.dut = FunctionUnit( DataType, PredicateType, CtrlType,
                          num_inports, num_outports, data_mem_size )

    for i in range( num_inports ):
      s.dut.recv_in_count[i] //= 1

    connect( s.src_comp.send,      s.dut.recv_in[0]     )
    connect( s.src_predicate.send, s.dut.recv_predicate )
    connect( s.src_opt.send,       s.dut.recv_opt       )
    connect( s.dut.send_out[0],    s.sink_if.recv       )
    connect( s.dut.send_out[1],    s.sink_else.recv     )

  def done( s ):
    return s.src_opt.done() and s.sink_if.done()  and s.sink_else.done() 

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

def test_Branch():
  FU            = BranchRTL
  DataType      = mk_data( 16, 1 )
  PredicateType = mk_predicate( 1, 1 )
  CtrlType      = mk_ctrl()
  num_inports   = 2
  num_outports  = 2
  data_mem_size = 8
  FuInType      = mk_bits( clog2( num_inports + 1 ) )
  src_comp      = [ DataType(0, 1), DataType(1, 1), DataType(0, 1) ]
  src_predicate = [ PredicateType(1, 0), PredicateType(1,0), PredicateType(1,1) ]
  src_opt       = [ CtrlType( OPT_BRH, b1( 1 ), [FuInType(1), FuInType(2)] ),
                    CtrlType( OPT_BRH, b1( 0 ), [FuInType(1), FuInType(2)] ),
                    CtrlType( OPT_BRH, b1( 0 ), [FuInType(1), FuInType(2)] ) ]
  sink_if       = [ DataType(0, 0), DataType(0, 0), DataType(0, 1) ]
  sink_else     = [ DataType(0, 0), DataType(0, 1), DataType(0, 0) ]
  th = TestHarness( FU, DataType, PredicateType, CtrlType,
                    num_inports, num_outports, data_mem_size,
                    src_comp, src_predicate, src_opt, sink_if, sink_else )
  run_sim( th )

def test_Branch_Start():
  FU            = BranchRTL
  DataType      = mk_data( 16, 1 )
  PredicateType = mk_predicate( 1, 1 )
  CtrlType      = mk_ctrl()
  num_inports   = 2
  num_outports  = 2
  data_mem_size = 8
  FuInType      = mk_bits( clog2( num_inports + 1 ) )
  src_comp      = [ DataType(0, 1), DataType(1, 1), DataType(0, 1) ]
  src_predicate = [ PredicateType(1, 0), PredicateType(1,0), PredicateType(1,1) ]
  src_opt       = [ CtrlType( OPT_BRH_START, b1( 0 ), [FuInType(0), FuInType(0)] ),
                    CtrlType( OPT_BRH_START, b1( 0 ), [FuInType(0), FuInType(0)] ),
                    CtrlType( OPT_BRH_START, b1( 0 ), [FuInType(0), FuInType(0)] ) ]
  sink_if       = [ DataType(0, 1), DataType(0, 0), DataType(0, 0) ]
  sink_else     = [ DataType(0, 0), DataType(0, 1), DataType(0, 1) ]
  th = TestHarness( FU, DataType, PredicateType, CtrlType,
                    num_inports, num_outports, data_mem_size,
                    src_comp, src_predicate, src_opt, sink_if, sink_else )
  run_sim( th )

