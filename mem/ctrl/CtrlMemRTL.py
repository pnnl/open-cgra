"""
==========================================================================
CtrlMemRTL.py
==========================================================================
Control memory for CGRA.

Author : Cheng Tan
  Date : Dec 21, 2019

"""

from pymtl3             import *
from pymtl3.stdlib.ifcs import SendIfcRTL, RecvIfcRTL
from ...lib.opt_type    import *
from pymtl3.stdlib.rtl  import RegisterFile

class CtrlMemRTL( Component ):

  def construct( s, CtrlType, ctrl_mem_size, num_ctrl=4 ):

    # Constant
    # assert( ctrl_mem_size <= num_ctrl )
    AddrType = mk_bits( clog2( ctrl_mem_size ) )
    TimeType = mk_bits( clog2( num_ctrl+1 ) )
    last_item = AddrType( ctrl_mem_size - 1 )

    # Interface
    s.send_ctrl  = SendIfcRTL( CtrlType )
    s.recv_waddr = RecvIfcRTL( AddrType )
    s.recv_ctrl  = RecvIfcRTL( CtrlType )

    # Component
    s.reg_file   = RegisterFile( CtrlType, ctrl_mem_size, 1, 1 )
    s.times = Wire( TimeType )

    # Connections
    s.send_ctrl.msg //= s.reg_file.rdata[0]
    s.reg_file.waddr[0] //= s.recv_waddr.msg
    s.reg_file.wdata[0] //= s.recv_ctrl.msg
    s.reg_file.wen[0]   //= s.recv_ctrl.en  and s.recv_waddr.en

    @s.update
    def update_signal():
      if s.times == TimeType( num_ctrl ) or s.reg_file.rdata[0].ctrl == OPT_START:
        s.send_ctrl.en = b1( 0 )
      else:
        s.send_ctrl.en  = s.send_ctrl.rdy # s.recv_raddr[i].rdy
      s.recv_waddr.rdy = b1( 1 )
      s.recv_ctrl.rdy = b1( 1 )

    @s.update_ff
    def update_raddr():
      if s.reg_file.rdata[0].ctrl != OPT_START:
        if s.times < TimeType( num_ctrl ):
          s.times <<= s.times + TimeType( 1 )
        if s.reg_file.raddr[0] < last_item:
          s.reg_file.raddr[0] <<= s.reg_file.raddr[0] + AddrType( 1 )
        else:
          s.reg_file.raddr[0] <<= AddrType( 0 )

  def line_trace( s ):
    out_str  = "||".join([ str(data) for data in s.reg_file.regs ])
    return f'{s.recv_ctrl.msg} : [{out_str}] : {s.send_ctrl.msg}'

