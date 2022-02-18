"""
==========================================================================
MulRTL_test.py
==========================================================================
Test cases for Muliplier.

Author : Cheng Tan
  Date : November 27, 2019

"""

from pymtl3                       import *
from pymtl3.stdlib.test           import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL

from ..AdderRTL                   import AdderRTL
from ..ShifterRTL                 import ShifterRTL
from ..MulRTL                     import MulRTL
from ..LogicRTL                   import LogicRTL
from ....mem.const.ConstQueueRTL  import ConstQueueRTL
from ....lib.opt_type             import *
from ....lib.messages             import *

import pytest
from itertools import product

import hypothesis
from hypothesis import strategies as st

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, FunctionUnit, DataType, PredicateType, ConfigType,
                 num_inports, num_outports, data_mem_size,
                 src0_msgs, src1_msgs, src_predicate, src_const,
                 ctrl_msgs, sink_msgs ):

    s.src_in0       = TestSrcRTL( DataType,      src0_msgs     )
    s.src_in1       = TestSrcRTL( DataType,      src1_msgs     )
    s.src_in2       = TestSrcRTL( DataType,      src1_msgs     )
    s.src_predicate = TestSrcRTL( PredicateType, src_predicate )
    s.src_opt       = TestSrcRTL( ConfigType,    ctrl_msgs     )
    s.sink_out      = TestSinkCL( DataType,      sink_msgs     )

    s.const_queue = ConstQueueRTL( DataType, src_const )
    s.dut = FunctionUnit( DataType, PredicateType, ConfigType,
                          num_inports, num_outports, data_mem_size )

    for i in range( num_inports ):
      s.dut.recv_in_count[i] //= 1

    connect( s.src_in0.send,       s.dut.recv_in[0]         )
    connect( s.src_in1.send,       s.dut.recv_in[1]         )
    connect( s.src_in2.send,       s.dut.recv_in[2]         )
    connect( s.src_predicate.send, s.dut.recv_predicate     )
    connect( s.dut.recv_const,     s.const_queue.send_const )
    connect( s.src_opt.send,       s.dut.recv_opt           )
    connect( s.dut.send_out[0],    s.sink_out.recv          )

  def done( s ):
    return s.src_in0.done() and s.src_in1.done() and\
           s.src_opt.done() and s.sink_out.done()

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

@pytest.mark.parametrize(
  'input_a, input_b',
  product( range( 3, 4 ), range( 2, 3 ) )
)
def test_mul0( input_a, input_b ):
  FU            = MulRTL
  DataType      = mk_data( 32, 1 )
  PredicateType = mk_predicate( 1, 1 )
  num_inports   = 4
  num_outports  = 1
  ConfigType    = mk_ctrl(num_inports)
  FuInType      = mk_bits( clog2( num_inports + 1 ) )
  data_mem_size = 8
  src_in0       = [ DataType( input_a, 1 ) ]
  src_in1       = [ DataType( input_b, 1 ) ]
  src_predicate = [ PredicateType(1,1) ]
  src_const     = [ DataType( 0, 1) ]
  sink_out      = [ DataType( input_a * input_b, 1 ) ]
  src_opt       = [ ConfigType( OPT_MUL, b1( 0 ), 
                    [FuInType(1), FuInType(3), FuInType(0), FuInType(0)] ) ]
  th = TestHarness( FU, DataType, PredicateType, ConfigType,
                    num_inports, num_outports, data_mem_size,
                    src_in0, src_in1, src_predicate, src_const,
                    src_opt, sink_out )
  run_sim( th )

