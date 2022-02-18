"""
=========================================================================
TileRTL.py
=========================================================================

Author : Cheng Tan
  Date : Dec 11, 2019
"""

from pymtl3                      import *
from pymtl3.stdlib.ifcs          import SendIfcRTL, RecvIfcRTL
from ..noc.CrossbarRTL           import CrossbarRTL
from ..noc.ChannelRTL            import ChannelRTL
from ..rf.RegisterRTL            import RegisterRTL
from ..mem.ctrl.CtrlMemRTL       import CtrlMemRTL
from ..fu.flexible.FlexibleFuRTL import FlexibleFuRTL
from ..fu.single.MemUnitRTL      import MemUnitRTL
from ..fu.single.AdderRTL        import AdderRTL

class TileRTL( Component ):

  def construct( s, DataType, PredicateType, CtrlType,
                 ctrl_mem_size, data_mem_size, num_ctrl,
                 num_fu_inports, num_fu_outports,
                 num_connect_inports, num_connect_outports,
                 Fu=FlexibleFuRTL, FuList=[MemUnitRTL,AdderRTL] ):

    # Constant
    num_xbar_inports  = num_fu_outports + num_connect_inports
    num_xbar_outports = num_fu_inports + num_connect_outports

    CtrlAddrType = mk_bits( clog2( ctrl_mem_size ) )
    DataAddrType = mk_bits( clog2( data_mem_size ) )

    # Interfaces
    s.recv_data = [ RecvIfcRTL( DataType ) for _ in range ( num_connect_inports ) ]
    s.send_data = [ SendIfcRTL( DataType ) for _ in range ( num_connect_outports ) ]

    # Ctrl
    s.recv_waddr = RecvIfcRTL( CtrlAddrType )
    s.recv_wopt  = RecvIfcRTL( CtrlType )

    # Data
    s.to_mem_raddr   = SendIfcRTL( DataAddrType )
    s.from_mem_rdata = RecvIfcRTL( DataType )
    s.to_mem_waddr   = SendIfcRTL( DataAddrType )
    s.to_mem_wdata   = SendIfcRTL( DataType )

    # Components
    s.element  = FlexibleFuRTL( DataType, PredicateType, CtrlType,
                                num_fu_inports, num_fu_outports,
                                data_mem_size, FuList )
    s.crossbar = CrossbarRTL( DataType, PredicateType, CtrlType,
                              num_xbar_inports, num_xbar_outports )
    s.ctrl_mem = CtrlMemRTL( CtrlType, ctrl_mem_size, num_ctrl )
    s.channel  = [ ChannelRTL( DataType ) for _ in range( num_xbar_outports ) ]

    # Additional one register for partial predication
    s.reg_predicate = RegisterRTL( PredicateType )

    # Connections

    # Ctrl
    s.ctrl_mem.recv_waddr //= s.recv_waddr
    s.ctrl_mem.recv_ctrl  //= s.recv_wopt
    # Data
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


    for i in range( num_connect_inports ):
      s.recv_data[i] //= s.crossbar.recv_data[i]

    for i in range( num_xbar_outports ):
      s.crossbar.send_data[i] //= s.channel[i].recv

    # One partial predication register for flow control.
    s.crossbar.send_predicate //= s.reg_predicate.recv
    s.reg_predicate.send //= s.element.recv_predicate

    for i in range( num_connect_outports ):
      s.channel[i].send //= s.send_data[i]

    for i in range( num_fu_inports ):
      s.channel[num_connect_inports+i].send //= s.element.recv_in[i]
      s.channel[num_connect_inports+i].count //= s.element.recv_in_count[i]

    for i in range( num_fu_outports ):
      s.element.send_out[i] //= s.crossbar.recv_data[num_connect_outports+i]

    @s.update
    def update_opt():
      s.element.recv_opt.msg  = s.ctrl_mem.send_ctrl.msg
      s.crossbar.recv_opt.msg = s.ctrl_mem.send_ctrl.msg
      s.element.recv_opt.en  = s.ctrl_mem.send_ctrl.en
      s.crossbar.recv_opt.en = s.ctrl_mem.send_ctrl.en
      s.ctrl_mem.send_ctrl.rdy = s.element.recv_opt.rdy and s.crossbar.recv_opt.rdy

  # Line trace
  def line_trace( s ):

    recv_str    = "|".join([ str(x.msg) for x in s.recv_data ])
    channel_recv_str = "|".join([ str(x.recv.msg) for x in s.channel ])
    channel_send_str = "|".join([ str(x.send.msg) for x in s.channel ])
    out_str  = "|".join([ "("+str(x.msg.payload)+","+str(x.msg.predicate)+")" for x in s.send_data ])
    return f"{recv_str} => [{s.crossbar.recv_opt.msg}] ({s.element.line_trace()}) => {channel_recv_str} => {channel_send_str} => {out_str}"

