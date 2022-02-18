"""
==========================================================================
TwoSeqComboRTL_test.py
==========================================================================
Test cases for two sequentially integrated functional unit.

Author : Cheng Tan
  Date : November 27, 2019

"""

from pymtl3                       import *
from pymtl3.stdlib.test           import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL

from ..SeqMulAdderRTL             import SeqMulAdderRTL
from ..SeqMulShifterRTL           import SeqMulShifterRTL
from ....lib.opt_type             import *
from ....lib.messages             import *

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, FunctionUnit, DataType, PredicateType, CtrlType,
                 num_inports, num_outports, data_mem_size,
                 src0_msgs, src1_msgs, src2_msgs, src_predicate,
                 ctrl_msgs, sink_msgs ):

    s.src_in0       = TestSrcRTL( DataType,      src0_msgs     )
    s.src_in1       = TestSrcRTL( DataType,      src1_msgs     )
    s.src_in2       = TestSrcRTL( DataType,      src2_msgs     )
    s.src_predicate = TestSrcRTL( PredicateType, src_predicate )
    s.src_const     = TestSrcRTL( DataType,      src2_msgs     )
    s.src_opt       = TestSrcRTL( CtrlType,      ctrl_msgs     )
    s.sink_out      = TestSinkCL( DataType,      sink_msgs     )

    s.dut = FunctionUnit( DataType, PredicateType, CtrlType,
                          num_inports, num_outports, data_mem_size )

    s.dut.recv_in_count[0] //= 1
    s.dut.recv_in_count[1] //= 1
    s.dut.recv_in_count[2] //= 1
    s.dut.recv_in_count[3] //= 1

    connect( s.src_in0.send,       s.dut.recv_in[0]     )
    connect( s.src_in1.send,       s.dut.recv_in[1]     )
    connect( s.src_in2.send,       s.dut.recv_in[2]     )
    connect( s.src_predicate.send, s.dut.recv_predicate )
    connect( s.src_const.send,     s.dut.recv_const     )
    connect( s.src_opt.send,       s.dut.recv_opt       )
    connect( s.dut.send_out[0],    s.sink_out.recv      )

  def done( s ):
    return s.src_in0.done() and s.src_in1.done()  and s.src_in2.done() and\
           s.src_opt.done() and s.sink_out.done()

  def line_trace( s ):
    return s.dut.line_trace()

def run_sim( test_harness, max_cycles=1000 ):
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

def test_mul_alu():
  FU            = SeqMulAdderRTL
  DataType      = mk_data( 16, 1 )
  PredicateType = mk_predicate( 1, 1 )
  CtrlType      = mk_ctrl()
  num_inports   = 4
  num_outports  = 2
  data_mem_size = 8
  src_in0       = [ DataType(1, 1), DataType(2, 1), DataType(4, 1) ]
  src_in1       = [ DataType(2, 1), DataType(3, 1), DataType(3, 1) ]
  src_in2       = [ DataType(1, 1), DataType(3, 1), DataType(3, 1) ]
  src_predicate = [ PredicateType(1, 1), PredicateType(1, 0), PredicateType(1, 1) ]
  sink_out      = [ DataType(3, 1), DataType(9, 0), DataType(9, 1) ]
  src_opt       = [ CtrlType( OPT_MUL_ADD, b1( 1 ) ),
                    CtrlType( OPT_MUL_ADD, b1( 1 ) ),
                    CtrlType( OPT_MUL_SUB, b1( 0 ) ) ]
  th = TestHarness( FU, DataType, PredicateType, CtrlType,
                    num_inports, num_outports, data_mem_size,
                    src_in0, src_in1, src_in2, src_predicate, src_opt,
                    sink_out )
  run_sim( th )

def test_mul_shifter():
  FU            = SeqMulShifterRTL
  DataType      = mk_data( 16, 1 )
  PredicateType = mk_predicate( 1, 1 )
  CtrlType      = mk_ctrl()
  num_inports   = 4
  num_outports  = 2
  data_mem_size = 8
  FuInType      = mk_bits( clog2( num_inports + 1 ) )
  pickRegister  = [ FuInType( x+1 ) for x in range( num_inports ) ]
  src_in0       = [ DataType(1, 1), DataType(2, 1),  DataType(4, 1) ]
  src_in1       = [ DataType(2, 1), DataType(3, 1),  DataType(3, 1) ]
  src_in2       = [ DataType(1, 1), DataType(2, 1),  DataType(1, 1) ]
  src_predicate = [ PredicateType(1, 1), PredicateType(1, 0), PredicateType(1, 1) ]
  sink_out      = [ DataType(4, 1), DataType(24, 0), DataType(6, 1) ]
  src_opt       = [ CtrlType( OPT_MUL_LLS, b1( 1 ), pickRegister ),
                    CtrlType( OPT_MUL_LLS, b1( 1 ), pickRegister ),
                    CtrlType( OPT_MUL_LRS, b1( 1 ), pickRegister ) ]
  th = TestHarness( FU, DataType, PredicateType, CtrlType,
                    num_inports, num_outports, data_mem_size,
                    src_in0, src_in1, src_in2, src_predicate, src_opt,
                    sink_out )
  run_sim( th )

