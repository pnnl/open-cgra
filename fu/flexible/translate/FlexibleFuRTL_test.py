"""
==========================================================================
FlexibleFuRTL_test.py
==========================================================================
Test cases for flexible functional unit.

Author : Cheng Tan
  Date : Dec 14, 2019

"""

from pymtl3                         import *
from pymtl3.stdlib.test.test_srcs   import TestSrcRTL
from pymtl3.stdlib.test.test_sinks  import TestSinkRTL

from ..FlexibleFuRTL                import FlexibleFuRTL
from ....lib.opt_type               import *
from ....lib.messages               import *

from ...single.AdderRTL             import AdderRTL
from ...single.MulRTL               import MulRTL
from ...single.ShifterRTL           import ShifterRTL
from ...single.SelRTL               import SelRTL
from ...single.LogicRTL             import LogicRTL
from ...single.PhiRTL               import PhiRTL
from ...single.MemUnitRTL           import MemUnitRTL
from ...single.CompRTL              import CompRTL
from ...single.BranchRTL            import BranchRTL

from pymtl3.passes.backends.verilog import TranslationImportPass

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, FunctionUnit, FuList, DataType, PredicateType, CtrlType,
                 data_mem_size, num_inports, num_outports,
                 src0_msgs, src1_msgs, src_predicate, ctrl_msgs,
                 sink0_msgs, sink1_msgs ):

    s.src_in0       = TestSrcRTL( DataType,      src0_msgs     )
    s.src_in1       = TestSrcRTL( DataType,      src1_msgs     )
    s.src_predicate = TestSrcRTL( PredicateType, src_predicate )
    s.src_const     = TestSrcRTL( DataType,      src1_msgs     )
    s.src_opt       = TestSrcRTL( CtrlType,      ctrl_msgs     )
    s.sink_out0     = TestSinkRTL( DataType,     sink0_msgs    )

    s.dut = FunctionUnit( DataType, PredicateType, CtrlType,
                          num_inports, num_outports, data_mem_size,
                          FuList )

    for i in range( num_inports ):
      s.dut.recv_in_count[i] //= 1

    connect( s.src_const.send,     s.dut.recv_const     )
    connect( s.src_in0.send,       s.dut.recv_in[0]     )
    connect( s.src_in1.send,       s.dut.recv_in[1]     )
    connect( s.src_predicate.send, s.dut.recv_predicate )
    connect( s.src_opt.send,       s.dut.recv_opt       )
    connect( s.dut.send_out[0],    s.sink_out0.recv     )

    AddrType = mk_bits( clog2( data_mem_size ) )
    s.to_mem_raddr   = [ TestSinkRTL( AddrType, [] ) for _ in FuList ]
    s.from_mem_rdata = [ TestSrcRTL( DataType, [] )  for _ in FuList ]
    s.to_mem_waddr   = [ TestSinkRTL( AddrType, [] ) for _ in FuList ]
    s.to_mem_wdata   = [ TestSinkRTL( DataType, [] ) for _ in FuList ]

    for i in range( len( FuList ) ):
      s.to_mem_raddr[i].recv   //= s.dut.to_mem_raddr[i]
      s.from_mem_rdata[i].send //= s.dut.from_mem_rdata[i]
      s.to_mem_waddr[i].recv   //= s.dut.to_mem_waddr[i]
      s.to_mem_wdata[i].recv   //= s.dut.to_mem_wdata[i]

  def done( s ):
    return s.src_in0.done()   and s.src_in1.done()   and\
           s.src_opt.done()   and s.sink_out0.done()

  def line_trace( s ):
    return s.dut.line_trace()

def run_sim( test_harness, max_cycles=100 ):
  test_harness.elaborate()
  test_harness.dut.verilog_translate_import = True
  test_harness.dut.config_verilog_import = VerilatorImportConfigs(vl_Wno_list = ['UNSIGNED', 'UNOPTFLAT', 'WIDTH', 'WIDTHCONCAT', 'ALWCOMBORDER'])
  test_harness = TranslationImportPass()(test_harness)
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

import platform
import pytest

@pytest.mark.skipif('Linux' not in platform.platform(),
                    reason="requires linux (gcc)")
def test_flexible_mul():
  FU            = FlexibleFuRTL
  FuList        = [AdderRTL, MulRTL, LogicRTL, ShifterRTL, PhiRTL, CompRTL, BranchRTL, MemUnitRTL, SelRTL]
  DataType      = mk_data( 32, 1 )
  PredicateType = mk_predicate( 1, 1 )
  data_mem_size = 8
  num_inports   = 4
  num_outports  = 2
  CtrlType      = mk_ctrl(num_inports)
  FuInType      = mk_bits( clog2( num_inports + 1 ) )
  pickRegister  = [ FuInType( x+1 ) for x in range( num_inports ) ]
  src_in0       = [ DataType(1, 1), DataType(2, 1), DataType(9, 1) ]
  src_in1       = [ DataType(2, 1), DataType(3, 1), DataType(2, 1) ]
  src_predicate = [ PredicateType(1, 1), PredicateType(1, 0), PredicateType(1, 1) ]
  sink_out      = [ DataType(2, 1), DataType(6, 1), DataType(18, 1) ]
  src_opt       = [ CtrlType( OPT_MUL, b1( 0 ), pickRegister ),
                    CtrlType( OPT_MUL, b1( 0 ), pickRegister ),
                    CtrlType( OPT_MUL, b1( 0 ), pickRegister ) ]
  th = TestHarness( FU, FuList, DataType, PredicateType, CtrlType,
                    data_mem_size, num_inports, num_outports,
                    src_in0, src_in1, src_predicate, src_opt,
                    sink_out, sink_out )
  run_sim( th )
