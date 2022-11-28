"""
==========================================================================
CGRACL_fir_demo_test.py
==========================================================================
Test cases for CGRAs with CL data/config memory.

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
from ...fu.single.MulRTL          import MulRTL
from ...fu.single.LogicRTL        import LogicRTL
from ...fu.single.CompRTL         import CompRTL
from ...fu.single.BranchRTL       import BranchRTL
from ...fu.single.PhiRTL          import PhiRTL
from ...fu.single.ShifterRTL      import ShifterRTL
from ...fu.single.MemUnitRTL      import MemUnitRTL
from ..CGRARTL                    import CGRARTL

from ..CGRAFL                     import CGRAFL
from ...lib.dfg_helper            import *

import os

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, DUT, FunctionUnit, FuList, DataType, PredicateType,
                 CtrlType, width, height, ctrl_mem_size, data_mem_size,
                 src_opt, ctrl_waddr, preload_data, preload_const ):

    s.num_tiles  = width * height
    AddrType     = mk_bits( clog2( ctrl_mem_size ) )

    s.src_opt    = [ TestSrcRTL( CtrlType, src_opt[i] )
                     for i in range( s.num_tiles ) ]
    s.ctrl_waddr = [ TestSrcRTL( AddrType, ctrl_waddr[i] )
                     for i in range( s.num_tiles ) ]

    s.dut        = DUT( DataType, PredicateType, CtrlType, width, height,
                        ctrl_mem_size, data_mem_size, 100, FunctionUnit, FuList,
                        preload_data, preload_const )
    s.DataType   = DataType

    for i in range( s.num_tiles ):
      connect( s.src_opt[i].send,     s.dut.recv_wopt[i]  )
      connect( s.ctrl_waddr[i].send,  s.dut.recv_waddr[i] )

  def line_trace( s ):
    return s.dut.line_trace()

  def output_target_value( s ):
    res = s.DataType(0, 1)
    res.payload = s.dut.tile[9].element.send_out[0].msg.payload
    return res.payload


def run_sim( test_harness, max_cycles=18 ):
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
    print( "{}:{}".format( ncycles, test_harness.line_trace() ))

  target_value = test_harness.output_target_value()

  test_harness.tick()
  test_harness.tick()
  test_harness.tick()

  print( '=' * 70 )
  print( "----------------- RTL test ------------------" )
  print("CGRA RTL model final result:", target_value)
  print("=================================================================")
  print("···························· split ······························")
  print("=================================================================")
  return target_value

def run_CGRAFL():
  target_json = "dfg_fir.json"
  script_dir  = os.path.dirname(__file__)
  file_path   = os.path.join( script_dir, target_json )
  DataType    = mk_data( 16, 1 )
  CtrlType    = mk_ctrl()
  const_data  = [ DataType( 0, 1  ),
                  DataType( 1, 1  ),
                  DataType( 2, 1  ),
                  DataType( 3, 1  ),
                  DataType( 4, 1  ),
                  DataType( 5, 1 ) ]
  data_spm    = [ 5 for _ in range(100) ]
  fu_dfg      = DFG( file_path, const_data, data_spm )

  print( "----------------- FL test ------------------" )
  # FL golden reference
  return CGRAFL( fu_dfg, DataType, CtrlType, const_data )#, data_spm )

def test_CGRA_4x4_fir():
  target_json = "config_fir.json"
  script_dir  = os.path.dirname(__file__)
  file_path   = os.path.join( script_dir, target_json )

  II                = 4
  num_tile_inports  = 4
  num_tile_outports = 4
  num_xbar_inports  = 6
  num_xbar_outports = 8
  ctrl_mem_size     = 8
  width             = 4
  height            = 4
  num_tiles         = width * height
  RouteType         = mk_bits( clog2( num_xbar_inports + 1 ) )
  AddrType          = mk_bits( clog2( ctrl_mem_size ) )
  num_tiles         = width * height
  ctrl_mem_size     = II
  data_mem_size     = 100
  num_fu_in         = 4
  DUT               = CGRARTL
  FunctionUnit      = FlexibleFuRTL
  targetFuList      = [ AdderRTL, PhiRTL, MemUnitRTL, CompRTL, MulRTL, BranchRTL ]
  DataType          = mk_data( 16, 1 )
  PredicateType     = mk_predicate( 1, 1 )
  CtrlType          = mk_ctrl( num_fu_in, num_xbar_inports, num_xbar_outports )
  FuInType          = mk_bits( clog2( num_fu_in + 1 ) )
  pickRegister      = [ FuInType( 0 ) for x in range( num_fu_in ) ]

  cgra_ctrl         = CGRACtrl( file_path, CtrlType, RouteType, width, height,
                                num_fu_in, num_xbar_inports, num_xbar_outports,
                                II )
  src_opt           = cgra_ctrl.get_ctrl()

  ctrl_waddr = [ [ AddrType( i ) for i in range( II ) ] for _ in range( num_tiles ) ]

  preload_data      = [ DataType( 5, 1 ) ] * data_mem_size
  preload_const     = []
  for _ in range( num_tiles ):
    preload_const.append([])
  preload_const[0].append( DataType( 0, 1) )
  preload_const[1].append( DataType( 0, 1) )
  preload_const[2].append( DataType( 0, 1) )
  preload_const[3].append( DataType( 0, 1) )
  preload_const[4].append( DataType( 0, 1) )
  preload_const[5].append( DataType( 10, 1) )
  preload_const[6].append( DataType( 0, 1) )
  preload_const[6].append( DataType( 1, 1) )
  preload_const[7].append( DataType( 0, 1) )
  preload_const[8].append( DataType( 0, 1) )
  preload_const[9].append( DataType( 0, 1) )
  preload_const[10].append( DataType( 0, 1) )
  preload_const[10].append( DataType( 3, 1) )
  preload_const[11].append( DataType( 0, 1) )
  preload_const[12].append( DataType( 0, 1) )
  preload_const[13].append( DataType( 0, 1) )
  preload_const[14].append( DataType( 0, 1) )
  preload_const[15].append( DataType( 0, 1) )
#  print(preload_const)

  th = TestHarness( DUT, FunctionUnit, targetFuList, DataType, PredicateType,
                    CtrlType, width, height, ctrl_mem_size, data_mem_size,
                    src_opt, ctrl_waddr, preload_data, preload_const )

  for i in range( num_tiles ):
    th.set_param("top.dut.tile["+str(i)+"].construct", FuList=targetFuList)

  target = run_sim( th )

  reference = run_CGRAFL()[0]

  assert(target == reference)

#def test_CGRA():
#
#  # Attribute of CGRA
#  width     = 4
#  height    = 4
#  DUT       = CGRA
#  FuList    = [ ALU ]
#  DataType  = mk_data( 16 )
#  CtrlType  = mk_ctrl()
#  cgra_ctrl = CGRACtrl( "control_signal.json", CtrlType )
#
#  # FL golden reference
#  fu_dfg    = DFG( "dfg.json" )
#  data_mem  = acc_fl( fu_dfg, DataType, CtrlType )
#
#  th = TestHarness( DUT, FuList, cgra_ctrl, DataType, CtrlType,
#                    width, height, data_mem ) 
#  run_sim( th )

