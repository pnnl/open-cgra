"""
==========================================================================
DataMemRTL_test.py
==========================================================================
Test cases for DataMemRTL.

Author : Cheng Tan
  Date : Nov 26, 2022

"""

from pymtl3                       import *
from pymtl3.stdlib.test           import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL

from ....lib.opt_type             import *
from ....lib.messages             import *
from ..DataMemRTL                 import DataMemRTL

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, DataType, AddrType, data_mem_size, read_addr,
                 read_data, write_addr, write_data, preloadData ):

    s.read_addr   = TestSrcRTL( AddrType, read_addr  )
    s.read_data   = TestSinkCL( DataType, read_data  )

    s.write_addr  = TestSrcRTL( AddrType, write_addr )
    s.write_data  = TestSrcRTL( DataType, write_data )


    s.dataMem = DataMemRTL( DataType, data_mem_size,
                           preload_data = preloadData )

    s.dataMem.recv_raddr[0] //= s.read_addr.send
    s.dataMem.send_rdata[0] //= s.read_data.recv
    s.dataMem.recv_waddr[0] //= s.write_addr.send
    s.dataMem.recv_wdata[0] //= s.write_data.send

  def done( s ):
    return s.read_addr.done() and s.read_data.done()

  def line_trace( s ):
    return s.dataMem.line_trace()

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
  data_mem_size = 20
  AddrType      = mk_bits( clog2( data_mem_size) )
  preloadData   = [ DataType(i, 1) for i in range( data_mem_size ) ]

  read_addr     = [ AddrType(2), AddrType(3), AddrType(0), AddrType(12) ]
  read_data     = [ DataType(2, 1), DataType(3, 1), DataType(0, 1), DataType(13, 1) ]
  # read_data     = [ DataType(0, 0), DataType(0, 0), DataType(0, 0), DataType(13, 1) ]
  write_addr    = [ AddrType(12), AddrType(13) ]
  write_data    = [ DataType(13, 1), DataType(14, 1) ]

  th = TestHarness( DataType, AddrType, data_mem_size, read_addr,
                    read_data, write_addr, write_data, preloadData )
  run_sim( th )

