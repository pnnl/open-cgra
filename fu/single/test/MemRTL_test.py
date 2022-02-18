"""
==========================================================================
Mem_test.py
==========================================================================
Test cases for functional unit.

Author : Cheng Tan
  Date : November 27, 2019

"""

from pymtl3                       import *
from pymtl3.stdlib.test           import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL

from ..MemUnitRTL                 import MemUnitRTL
from ....mem.data.DataMemRTL      import DataMemRTL
from ....mem.data.DataMemCL       import DataMemCL
from ....lib.opt_type             import *
from ....lib.messages             import *

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, FunctionUnit, DataUnit, DataType, PredicateType,
                 ConfigType, num_inports, num_outports, data_mem_size,
                 src0_msgs, src1_msgs, src_predicate, ctrl_msgs,
                 sink_msgs ):

    s.src_in0       = TestSrcRTL( DataType,      src0_msgs     )
    s.src_in1       = TestSrcRTL( DataType,      src1_msgs     )
    s.src_predicate = TestSrcRTL( PredicateType, src_predicate )
    s.src_opt       = TestSrcRTL( ConfigType,    ctrl_msgs     )
    s.sink_out      = TestSinkCL( DataType,      sink_msgs     )

    s.dut = FunctionUnit( DataType, PredicateType, ConfigType,
                          num_inports, num_outports, data_mem_size )
    s.data_mem = DataUnit( DataType, data_mem_size )

    for i in range( num_inports ):
      s.dut.recv_in_count[i] //= 1

    connect( s.dut.to_mem_raddr,   s.data_mem.recv_raddr[0] )
    connect( s.dut.from_mem_rdata, s.data_mem.send_rdata[0] )
    connect( s.dut.to_mem_waddr,   s.data_mem.recv_waddr[0] )
    connect( s.dut.to_mem_wdata,   s.data_mem.recv_wdata[0] )

    connect( s.src_in0.send,       s.dut.recv_in[0]     )
    connect( s.src_in1.send,       s.dut.recv_in[1]     )
    connect( s.src_predicate.send, s.dut.recv_predicate )
    connect( s.src_opt.send,       s.dut.recv_opt       )
    connect( s.dut.send_out[0],    s.sink_out.recv      )

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

def test_Mem():
  FU            = MemUnitRTL
  DataUnit      = DataMemRTL
  DataType      = mk_data( 16, 1 )
  PredicateType = mk_predicate( 1, 1 )
  ConfigType    = mk_ctrl()
  data_mem_size = 8
  num_inports   = 2
  num_outports  = 1
  FuInType      = mk_bits( clog2( num_inports + 1 ) )
  pickRegister  = [ FuInType( x+1 ) for x in range( num_inports ) ]
  src_in0       = [ DataType(1, 1), DataType(3, 1), DataType(3, 1), DataType(3, 1) ]
  src_in1       = [ DataType(9, 1), DataType(6, 1), DataType(2, 1), DataType(7, 1) ]
  src_predicate = [ PredicateType(1, 0), PredicateType(1,1), PredicateType(1,0), PredicateType(0,0) ]
  sink_out      = [ DataType(0, 0), DataType(6, 1), DataType(6, 1) ]
  src_opt       = [ ConfigType( OPT_LD,  b1( 1 ), pickRegister ),
                    ConfigType( OPT_STR, b1( 0 ), pickRegister ),
                    ConfigType( OPT_LD,  b1( 0 ), pickRegister ),
                    ConfigType( OPT_LD,  b1( 0 ), pickRegister ) ]
  th = TestHarness( FU, DataUnit, DataType, PredicateType, ConfigType,
                    num_inports, num_outports, data_mem_size,
                    src_in0, src_in1, src_predicate, src_opt, sink_out )
  run_sim( th )

def test_PseudoMem():
  FU = MemUnitRTL
  DataUnit      = DataMemCL
  DataType      = mk_data( 16, 1 )
  PredicateType = mk_predicate( 1, 1 )
  ConfigType = mk_ctrl()
  data_mem_size = 8
  num_inports  = 2
  num_outports = 1
  FuInType = mk_bits( clog2( num_inports + 1 ) )
  pickRegister = [ FuInType( x+1 ) for x in range( num_inports ) ]
  src_in0  = [ DataType(1, 1), DataType(0, 1), DataType(0, 1) ]
  src_in1  = [ DataType(9, 1), DataType(6, 1), DataType(7, 1) ]
  src_predicate = [ PredicateType(1, 1), PredicateType(0, 0), PredicateType(1, 0),
                    PredicateType(0, 0), PredicateType(0, 0), PredicateType(0, 0) ]
  sink_out = [ DataType(0, 1), DataType(6, 1), DataType(6, 1), DataType(6, 1) ]
  src_opt  = [ ConfigType( OPT_LD      , b1( 0 ), pickRegister ),
               ConfigType( OPT_STR     , b1( 0 ), pickRegister ),
               ConfigType( OPT_LD_CONST, b1( 0 ), pickRegister ),
               ConfigType( OPT_LD      , b1( 0 ), pickRegister ),
               ConfigType( OPT_LD_CONST, b1( 0 ), pickRegister ) ]
  th = TestHarness( FU, DataUnit, DataType, PredicateType, ConfigType, num_inports,
                    num_outports, data_mem_size, src_in0, src_in1,
                    src_predicate, src_opt, sink_out )
  run_sim( th )

