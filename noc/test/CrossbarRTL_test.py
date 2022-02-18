"""
==========================================================================
CrossbarRTL_test.py
==========================================================================
Test cases for Crossbar.

Author : Cheng Tan
  Date : Dec 9, 2019

"""

from pymtl3                       import *
from pymtl3.stdlib.test           import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL

from ..CrossbarRTL                import CrossbarRTL
from ...lib.opt_type              import *
from ...lib.messages              import *

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, CrossbarUnit, DataType, PredicateType, CtrlType,
                 num_inports, num_outports,
                 src_data, src_routing, sink_out ):

    s.num_inports  = num_inports
    s.num_outports = num_outports

    s.src_opt      = TestSrcRTL( CtrlType, src_routing )
    s.src_data     = [ TestSrcRTL( DataType, src_data[i]  )
                     for i in range( num_inports  ) ]
    s.sink_out     = [ TestSinkCL( DataType, sink_out[i] )
                     for i in range( num_outports ) ]

    s.dut = CrossbarUnit( DataType, PredicateType, CtrlType, num_inports,
                          num_outports, num_inports-1 )

    for i in range( num_inports ):
      connect( s.src_data[i].send, s.dut.recv_data[i] )
      connect( s.dut.send_data[i],  s.sink_out[i].recv )
    connect( s.src_opt.send,     s.dut.recv_opt )

  def done( s ):
    done = True
    for i in range( s.num_inports  ):
      if not s.src_data[i].done():
        done = False
        break
    for i in range( s.num_outports ):
      if not s.sink_out[i].done():
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

def test_crossbar():
  FU = CrossbarRTL
  num_fu_in     = 3
  num_inports   = 3
  num_outports  = 3
  DataType      = mk_data( 16, 1 )
  PredicateType = mk_predicate( 1, 1 )
  CtrlType      = mk_ctrl( num_fu_in, num_inports, num_outports )
  FuInType      = mk_bits( clog2( num_inports + 1 ) )
  pickRegister  = [ FuInType( x+1 ) for x in range( num_inports ) ]
  RouteType     = mk_bits( clog2( num_inports + 1 ) )
  src_opt       = [ CtrlType( OPT_ADD, b1(0), pickRegister, [RouteType(2), RouteType(3), RouteType(1)]) ]
  src_data      = [ [DataType(3, 1)], [DataType(2, 1)], [DataType(9, 1)] ]
  sink_out      = [ [DataType(2, 1)], [DataType(9, 1, 1)], [DataType(3, 1)] ]
  th = TestHarness( FU, DataType, PredicateType, CtrlType, num_inports, num_outports,
                    src_data, src_opt, sink_out )
  run_sim( th )

def test_multi():
  FU = CrossbarRTL
  num_fu_in     = 3
  num_inports   = 3
  num_outports  = 3
  DataType      = mk_data( 16, 1 )
  PredicateType = mk_predicate( 1, 1 )
  CtrlType      = mk_ctrl( num_fu_in, num_inports, num_outports )
  FuInType      = mk_bits( clog2( num_inports + 1 ) )
  pickRegister  = [ FuInType( x+1 ) for x in range( num_inports ) ]
  RouteType     = mk_bits( clog2( num_inports + 1 ) )
  src_opt       = [ CtrlType( OPT_ADD, b1(0), pickRegister, [RouteType(2), RouteType(1), RouteType(1)]) ]
  src_data      = [ [DataType(3, 1)], [DataType(2, 1)], [DataType(9, 1)] ]
  sink_out      = [ [DataType(2, 1)], [DataType(3, 1)], [DataType(3, 1)] ]
  th = TestHarness( FU, DataType, PredicateType, CtrlType, num_inports, num_outports,
                    src_data, src_opt, sink_out )
  run_sim( th )

def test_multi2():
  FU = CrossbarRTL
  num_fu_in     = 3
  num_inports   = 3
  num_outports  = 3
  DataType      = mk_data( 16, 1 )
  PredicateType = mk_predicate( 1, 1 )
  CtrlType      = mk_ctrl( num_fu_in, num_inports, num_outports )
  FuInType      = mk_bits( clog2( num_inports + 1 ) )
  pickRegister  = [ FuInType( 0 ) for x in range( num_inports ) ]
  RouteType     = mk_bits( clog2( num_inports + 1 ) )
  # RouteType(0) indicates no data movement. Reg ID starts from 1, which will get "minus 1"
  # the logic.
  src_opt       = [ CtrlType( OPT_ADD, b1(0), pickRegister, [RouteType(2), RouteType(1), RouteType(0)]),
                    CtrlType( OPT_ADD, b1(0), pickRegister, [RouteType(0), RouteType(3), RouteType(2)]) ]
  src_data      = [ [DataType(3, 1)], [DataType(2, 1), DataType(20, 1)], [DataType(9, 1)] ]
  sink_out      = [ [DataType(2, 1)], [DataType(3, 1), DataType(9, 1, 1)], [DataType(20, 1)] ]
  th = TestHarness( FU, DataType, PredicateType, CtrlType, num_inports, num_outports,
                    src_data, src_opt, sink_out )
  run_sim( th )

def test_predicate():
  FU = CrossbarRTL
  num_fu_in     = 3
  num_inports   = 3
  num_outports  = 3
  DataType      = mk_data( 16, 1 )
  PredicateType = mk_predicate( 1, 1 )
  CtrlType      = mk_ctrl( num_fu_in, num_inports, num_outports )
  FuInType      = mk_bits( clog2( num_inports + 1 ) )
  pickRegister  = [ FuInType( 0 ) for x in range( num_inports ) ]
  RouteType     = mk_bits( clog2( num_inports + 1 ) )
  src_opt       = [ CtrlType( OPT_ADD, b1(0), pickRegister, [RouteType(2), RouteType(1), RouteType(0)], [b1(0), b1(0), b1(1)]),
                   CtrlType( OPT_ADD, b1(0), pickRegister, [RouteType(0), RouteType(3), RouteType(2)], [b1(0), b1(0), b1(0)]),
                   CtrlType( OPT_ADD, b1(1), pickRegister, [RouteType(0), RouteType(0), RouteType(0)], [b1(1), b1(1), b1(0)]) ]
  src_data      = [ [DataType(1, 1), DataType(2, 1)], [DataType(3, 1), DataType(4, 1), DataType(5, 0)], [DataType(6, 1), DataType(7, 0)] ]
  sink_out      = [ [DataType(3, 1)], [DataType(1, 1), DataType(6, 1, 1)], [DataType(4, 1)] ]
  th = TestHarness( FU, DataType, PredicateType, CtrlType, num_inports, num_outports,
                    src_data, src_opt, sink_out )
  run_sim( th )

