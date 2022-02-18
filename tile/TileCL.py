"""
=========================================================================
TileCL.py
=========================================================================

Author : Cheng Tan
  Date : Dec 28, 2019
"""

from pymtl3                      import *
from pymtl3.stdlib.ifcs          import SendIfcRTL, RecvIfcRTL
from ..noc.CrossbarRTL           import CrossbarRTL
from ..noc.ChannelRTL            import ChannelRTL
from ..rf.RegisterRTL            import RegisterRTL
from ..mem.ctrl.CtrlMemCL        import CtrlMemCL
from ..fu.flexible.FlexibleFuRTL import FlexibleFuRTL
from ..mem.const.ConstQueueRTL   import ConstQueueRTL
from ..fu.single.MemUnitRTL      import MemUnitRTL

class TileCL( Component ):

  def construct( s, Fu, FuList, DataType, PredicateType, CtrlType,
                 ctrl_mem_size, data_mem_size, num_ctrl,
                 const_list, opt_list, id=0 ):

    # Constant
    num_xbar_inports  = 6
    num_xbar_outports = 8
    num_fu_inports    = 4
    num_fu_outports   = 2
    num_mesh_ports    = 4
    bypass_point      = 4
    CtrlAddrType      = mk_bits( clog2( ctrl_mem_size ) )
    DataAddrType      = mk_bits( clog2( data_mem_size ) )

    # Interfaces
    s.recv_data    = [ RecvIfcRTL( DataType ) for _ in range ( num_mesh_ports ) ]
    s.send_data    = [ SendIfcRTL( DataType ) for _ in range ( num_mesh_ports ) ]

    # Data
    s.to_mem_raddr   = SendIfcRTL( DataAddrType )
    s.from_mem_rdata = RecvIfcRTL( DataType )
    s.to_mem_waddr   = SendIfcRTL( DataAddrType )
    s.to_mem_wdata   = SendIfcRTL( DataType )

    # Components
    s.element     = FlexibleFuRTL( DataType, PredicateType, CtrlType, num_fu_inports,
                                   num_fu_outports, data_mem_size, FuList )
    s.const_queue = ConstQueueRTL( DataType, const_list )
    s.crossbar    = CrossbarRTL( DataType, PredicateType, CtrlType, num_xbar_inports,
                                 num_xbar_outports, bypass_point, id )
    s.ctrl_mem    = CtrlMemCL( CtrlType, ctrl_mem_size, num_ctrl, opt_list, id )
    s.channel     = [ ChannelRTL ( DataType ) for _ in range( num_xbar_outports ) ]

    # Additional one register for partial predication
    s.reg_predicate = RegisterRTL( PredicateType )

    # Connections

    # Data
    s.element.recv_const //=  s.const_queue.send_const

    for i in range( len( FuList ) ):
      if FuList[i] == MemUnitRTL:
        s.to_mem_raddr   //= s.element.to_mem_raddr[i]
        s.from_mem_rdata //= s.element.from_mem_rdata[i]
        s.to_mem_waddr   //= s.element.to_mem_waddr[i]
        s.to_mem_wdata   //= s.element.to_mem_wdata[i]
      else:
        s.element.to_mem_raddr[i].rdy   //= 0
        s.element.from_mem_rdata[i].en  //= 0
        s.element.from_mem_rdata[i].msg //= DataType( 0, 0 )
        s.element.to_mem_waddr[i].rdy   //= 0
        s.element.to_mem_wdata[i].rdy   //= 0

    for i in range( num_mesh_ports ):
      s.recv_data[i] //= s.crossbar.recv_data[i]

    for i in range( num_xbar_outports ):
      s.crossbar.send_data[i] //= s.channel[i].recv

    # One partial predication register for flow control.
    s.crossbar.send_predicate //= s.reg_predicate.recv
    s.reg_predicate.send //= s.element.recv_predicate

    for i in range( num_mesh_ports ):
      s.channel[i].send //= s.send_data[i]

    for i in range( num_fu_inports ):
      s.channel[num_mesh_ports+i].send  //= s.element.recv_in[i]
      s.channel[num_mesh_ports+i].count //= s.element.recv_in_count[i]

    for i in range( num_fu_outports ):
      s.element.send_out[i] //= s.crossbar.recv_data[num_mesh_ports+i]

    @s.update
    def update_opt():
      s.element.recv_opt.msg   = s.ctrl_mem.send_ctrl.msg
      s.crossbar.recv_opt.msg  = s.ctrl_mem.send_ctrl.msg
      s.element.recv_opt.en    = s.ctrl_mem.send_ctrl.en
      s.crossbar.recv_opt.en   = s.ctrl_mem.send_ctrl.en
      s.ctrl_mem.send_ctrl.rdy = s.element.recv_opt.rdy or s.crossbar.recv_opt.rdy

  # Line trace
  def line_trace( s ):
    recv_str    = "|".join([ str(x.msg) for x in s.recv_data ])
    channel_recv_str = "|".join([ str(x.recv.msg) for x in s.channel ])
    channel_send_str = "|".join([ str(x.send.msg) for x in s.channel ])
    channel_str = "|".join([ str(x.line_trace()) for x in s.channel ])
    out_str  = "|".join([ "("+str(x.msg.payload)+","+str(x.msg.predicate)+")" for x in s.send_data ])
    return f"\n{recv_str} => [crossbar: {s.crossbar.line_trace()}] (element: {s.element.line_trace()}) => {channel_str} => {out_str} |||"

