"""
==========================================================================
RetRTL_test.py
==========================================================================
Test cases for functional unit Ret.

Author : Cheng Tan
  Date : September 21, 2021

"""

from pymtl3                       import *
from pymtl3.stdlib.test           import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL

from ..RetRTL                     import RetRTL
from ....lib.opt_type             import *
from ....lib.messages             import *

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, FunctionUnit, DataType, PredicateType, CtrlType,
                 num_inports, num_outports, data_mem_size,
                 src_in, src_predicate, src_opt, sink ):

    s.src_in        = TestSrcRTL( DataType,      src_in        )
    s.src_predicate = TestSrcRTL( PredicateType, src_predicate )
    s.src_opt       = TestSrcRTL( CtrlType,      src_opt       )
    s.sink          = TestSinkCL( DataType,      sink          )

    s.dut = FunctionUnit( DataType, PredicateType, CtrlType,
                          num_inports, num_outports, data_mem_size )

    for i in range( num_inports ):
      s.dut.recv_in_count[i] //= 1

    connect( s.src_in.send,        s.dut.recv_in[0]     )
    connect( s.src_predicate.send, s.dut.recv_predicate )
    connect( s.src_opt.send,       s.dut.recv_opt       )
    connect( s.dut.send_out[0],    s.sink.recv          )

  def done( s ):
    return s.src_opt.done() and s.sink.done()

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

def test_Ret():
  FU            = RetRTL
  DataType      = mk_data( 16, 1 )
  PredicateType = mk_predicate( 1, 1 )
  CtrlType      = mk_ctrl()
  num_inports   = 2
  num_outports  = 2
  data_mem_size = 8
  FuInType      = mk_bits( clog2( num_inports + 1 ) )
  src_in        = [ DataType(1, 1), DataType(2, 1), DataType(3, 1) ]
  src_predicate = [ PredicateType(1, 0), PredicateType(1,0), PredicateType(1,1) ]
  src_opt       = [ CtrlType( OPT_RET, b1( 1 ), [FuInType(1), FuInType(0)] ),
                    CtrlType( OPT_RET, b1( 0 ), [FuInType(1), FuInType(0)] ),
                    CtrlType( OPT_RET, b1( 1 ), [FuInType(1), FuInType(0)] ) ]
  sink          = [ DataType(1, 0), DataType(2, 1), DataType(3, 1) ]
  th = TestHarness( FU, DataType, PredicateType, CtrlType,
                    num_inports, num_outports, data_mem_size,
                    src_in, src_predicate, src_opt, sink )
  run_sim( th )

