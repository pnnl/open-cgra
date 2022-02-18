"""
==========================================================================
CompRTL_test.py
==========================================================================
Test cases for functional unit Phi.

Author : Cheng Tan
  Date : November 27, 2019

"""

from pymtl3                       import *
from pymtl3.stdlib.test           import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL

from ..SelRTL                     import SelRTL
from ....lib.opt_type             import *
from ....lib.messages             import *

from pymtl3.passes.PassGroups     import *

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, FunctionUnit, DataType, PredicateType, CtrlType,
                 num_inports, num_outports, data_mem_size,
                 src_data1, src_data2, src_predicate,
                 src_ref0, src_opt, sink_msgs ):

    s.src_data1     = TestSrcRTL( DataType,      src_data1     )
    s.src_data2     = TestSrcRTL( DataType,      src_data2     )
    s.src_predicate = TestSrcRTL( PredicateType, src_predicate )
    s.src_ref0      = TestSrcRTL( DataType,      src_ref0      )
    s.src_opt       = TestSrcRTL( CtrlType,      src_opt       )
    s.sink_out      = TestSinkCL( DataType,      sink_msgs     )

    s.dut = FunctionUnit( DataType, PredicateType, CtrlType,
                          num_inports, num_outports, data_mem_size )

    for i in range( num_inports ):
      s.dut.recv_in_count[i] //= 1

    connect( s.src_data1.send,     s.dut.recv_in[1]     )
    connect( s.src_data2.send,     s.dut.recv_in[2]     )
    connect( s.src_predicate.send, s.dut.recv_predicate )
    connect( s.src_ref0.send,      s.dut.recv_in[0]     )
    connect( s.src_opt.send,       s.dut.recv_opt       )
    connect( s.dut.send_out[0],    s.sink_out.recv      )

  def done( s ):
    return s.src_data1.done() and s.src_data2.done() and\
           s.src_ref0.done()  and s.sink_out.done()

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

def test_Select():
  FU = SelRTL
  DataType      = mk_data( 32, 1 )
  PredicateType = mk_predicate( 1, 1 )
  # Selector needs more than 2 inputs
  CtrlType      = mk_ctrl(num_fu_in = 4)
  num_inports   = 4
  num_outports  = 1
  data_mem_size = 8
  FuInType      = mk_bits( clog2( num_inports + 1 ) )
  pickRegister  = [ FuInType( x+1 ) for x in range( num_inports ) ]
  src_data1     = [ DataType(9, 1), DataType(3, 1), DataType(4, 1) ]
  src_data2     = [ DataType(2, 1), DataType(7, 1), DataType(5, 1) ]
  src_predicate = [ PredicateType(1,1), PredicateType(1,1), PredicateType(1,1) ]
  src_ref0      = [ DataType(1, 1), DataType(0, 1), DataType(1, 1) ]
  src_opt       = [ CtrlType( OPT_SEL, b1( 0 ), pickRegister ),
                    CtrlType( OPT_SEL, b1( 0 ), pickRegister ),
                    CtrlType( OPT_SEL, b1( 0 ), pickRegister ) ]
  sink_out      = [ DataType(9, 1), DataType(7, 1), DataType(4, 1) ]
  th = TestHarness( FU, DataType, PredicateType, CtrlType,
                    num_inports, num_outports, data_mem_size,
                    src_data1, src_data2, src_predicate,
                    src_ref0, src_opt, sink_out )
  run_sim( th )

