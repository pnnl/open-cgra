"""
=========================================================================
CGRARTL.py
=========================================================================

Author : Cheng Tan
  Date : Dec 15, 2019
"""

from pymtl3                      import *
from pymtl3.stdlib.ifcs          import SendIfcRTL, RecvIfcRTL
from ..noc.CrossbarRTL           import CrossbarRTL
from ..noc.ChannelRTL            import ChannelRTL
from ..tile.TileRTL              import TileRTL
from ..lib.opt_type              import *
from ..mem.data.DataMemRTL       import DataMemRTL
from ..fu.single.MemUnitRTL      import MemUnitRTL
from ..fu.single.AdderRTL        import AdderRTL
from ..fu.flexible.FlexibleFuRTL import FlexibleFuRTL

class CGRARTL( Component ):

  def construct( s, DataType, PredicateType, CtrlType, width, height,
                 ctrl_mem_size, data_mem_size, num_ctrl, FunctionUnit,
                 FuList ):

    # Constant
    NORTH = 0
    SOUTH = 1
    WEST  = 2
    EAST  = 3
    ADDITION = 4
    s.num_tiles = width * height
    s.num_mesh_ports = 5
    AddrType = mk_bits( clog2( ctrl_mem_size ) )

    # Interfaces
    s.recv_waddr = [ RecvIfcRTL( AddrType )  for _ in range( s.num_tiles ) ]
    s.recv_wopt  = [ RecvIfcRTL( CtrlType )  for _ in range( s.num_tiles ) ]

    # Components
    s.tile = [ TileRTL( DataType, PredicateType, CtrlType,
                        ctrl_mem_size, data_mem_size,
                        num_ctrl, 4, 2, s.num_mesh_ports,
                        s.num_mesh_ports )
                        for _ in range( s.num_tiles ) ]
    s.data_mem = DataMemRTL( DataType, data_mem_size, height, height )

    # Connections
    for i in range( s.num_tiles):
      s.recv_waddr[i] //= s.tile[i].recv_waddr
      s.recv_wopt[i]  //= s.tile[i].recv_wopt

      if i // width > 0:
        s.tile[i].send_data[SOUTH] //= s.tile[i-width].recv_data[NORTH]

      if i // width < height - 1:
        s.tile[i].send_data[NORTH] //= s.tile[i+width].recv_data[SOUTH]

      if i % width > 0:
        s.tile[i].send_data[WEST] //= s.tile[i-1].recv_data[EAST]

      if i % width < width - 1:
        s.tile[i].send_data[EAST] //= s.tile[i+1].recv_data[WEST]

      if i // width == 0:
        s.tile[i].send_data[SOUTH].rdy //= 0
        s.tile[i].recv_data[SOUTH].en  //= 0
        s.tile[i].recv_data[SOUTH].msg //= DataType( 0, 0 )

      if i // width == height - 1:
        s.tile[i].send_data[NORTH].rdy  //= 0
        s.tile[i].recv_data[NORTH].en   //= 0
        s.tile[i].recv_data[NORTH].msg  //= DataType( 0, 0 )

      if i % width == 0:
        s.tile[i].send_data[WEST].rdy  //= 0
        s.tile[i].recv_data[WEST].en   //= 0
        s.tile[i].recv_data[WEST].msg  //= DataType( 0, 0 )

      if i % width == width - 1:
        s.tile[i].send_data[EAST].rdy  //= 0
        s.tile[i].recv_data[EAST].en   //= 0
        s.tile[i].recv_data[EAST].msg  //= DataType( 0, 0 )

      if i % width == 0:
        s.tile[i].to_mem_raddr   //= s.data_mem.recv_raddr[i//width]
        s.tile[i].from_mem_rdata //= s.data_mem.send_rdata[i//width]
        s.tile[i].to_mem_waddr   //= s.data_mem.recv_waddr[i//width]
        s.tile[i].to_mem_wdata   //= s.data_mem.recv_wdata[i//width]
      else:
        s.tile[i].to_mem_raddr.rdy //= 0
        s.tile[i].from_mem_rdata.en //= 0
        s.tile[i].from_mem_rdata.msg //= DataType(0, 0)
        s.tile[i].to_mem_waddr.rdy //= 0
        s.tile[i].to_mem_wdata.rdy //= 0

    s.tile[0].send_data[ADDITION] //= s.tile[3].recv_data[ADDITION]
    s.tile[3].send_data[ADDITION] //= s.tile[0].recv_data[ADDITION]
    s.tile[1].send_data[ADDITION] //= s.tile[2].recv_data[ADDITION]
    s.tile[2].send_data[ADDITION] //= s.tile[1].recv_data[ADDITION]

  # Line trace
  def line_trace( s ):
    str = "||".join([ x.element.line_trace() for x in s.tile ])
    str += " :: [" + s.data_mem.line_trace() + "]"
    return str

