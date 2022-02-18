"""
==========================================================================
ConstQueueRTL_test.py
==========================================================================
Test cases for constant queue.

Author : Cheng Tan
  Date : Jan 20, 2020

"""

from pymtl3                       import *
from pymtl3.stdlib.test           import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL

from ....fu.single.AdderRTL       import AdderRTL
from ....lib.opt_type             import *
from ....lib.messages             import *
from ..ConstQueueRTL              import ConstQueueRTL

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, DataType, PredicateType, ConfigType, src0_msgs,
                 src_const, ctrl_msgs, sink_msgs ):

    s.src_in0     = TestSrcRTL( DataType,   src0_msgs )
    s.src_opt     = TestSrcRTL( ConfigType, ctrl_msgs )
    s.sink_out    = TestSinkCL( DataType,   sink_msgs )

    s.alu         = AdderRTL( DataType, PredicateType, ConfigType,
                              2, 1, 8 )
    s.const_queue = ConstQueueRTL( DataType, src_const )

    s.alu.recv_in_count[0] //= 1
    s.alu.recv_in_count[1] //= 1

    connect( s.src_in0.send,    s.alu.recv_in[0]         )
    connect( s.alu.recv_in[1],  s.const_queue.send_const )
    connect( s.src_opt.send,    s.alu.recv_opt           )
    connect( s.alu.send_out[0], s.sink_out.recv          )

  def done( s ):
    return s.src_in0.done() and s.src_opt.done() and s.sink_out.done()

  def line_trace( s ):
    return s.const_queue.line_trace() + s.alu.line_trace()

def run_sim( test_harness, max_cycles=10 ):
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

def test_const_queue():
  DataType      = mk_data( 16, 1 )
  PredicateType = mk_predicate( 1, 1 )
  num_inports   = 2
  FuInType      = mk_bits( clog2( num_inports + 1 ) )
  pickRegister  = [ FuInType( x+1 ) for x in range( num_inports ) ]
  ConfigType    = mk_ctrl(num_inports)
  src_in0       = [ DataType(1,  1), DataType(3,  1), DataType(9, 1) ]
  src_const     = [ DataType(9,  1), DataType(8,  1), DataType(7, 1) ]
  sink_out      = [ DataType(10, 1), DataType(11, 1), DataType(2, 1) ]
  src_opt       = [ ConfigType( OPT_ADD, b1( 0 ), pickRegister ),
                    ConfigType( OPT_ADD, b1( 0 ), pickRegister ),
                    ConfigType( OPT_SUB, b1( 0 ), pickRegister ) ]
  th = TestHarness( DataType, PredicateType, ConfigType, src_in0,
                    src_const, src_opt, sink_out )
  run_sim( th )

