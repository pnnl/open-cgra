"""
==========================================================================
MemUnitRTL.py
==========================================================================
Scratchpad memory access unit for (the left most) CGRA tiles.

Author : Cheng Tan
  Date : November 29, 2019

"""

from pymtl3              import *
from pymtl3.stdlib.ifcs  import SendIfcRTL, RecvIfcRTL
from ...lib.opt_type     import *
from ..basic.Fu          import Fu

class MemUnitRTL( Component ):

  def construct( s, DataType, PredicateType, CtrlType,
                 num_inports, num_outports, data_mem_size ):

    # Constant
    AddrType      = mk_bits( clog2( data_mem_size ) )
    num_entries   = 2
    CountType     = mk_bits( clog2( num_entries + 1 ) )
    FuInType      = mk_bits( clog2( num_inports + 1 ) )

    # Interface
    s.recv_in        = [ RecvIfcRTL( DataType ) for _ in range( num_inports ) ]
    s.recv_in_count  = [ InPort( CountType ) for _ in range( num_inports ) ]
    s.recv_predicate = RecvIfcRTL( PredicateType )
    s.recv_const     = RecvIfcRTL( DataType )
    s.recv_opt       = RecvIfcRTL( CtrlType )
    s.send_out       = [ SendIfcRTL( DataType ) for _ in range( num_outports ) ]

    # Interface to the data sram, need to interface them with
    # the data memory module in top level
    s.to_mem_raddr   = SendIfcRTL( AddrType )
    s.from_mem_rdata = RecvIfcRTL( DataType )
    s.to_mem_waddr   = SendIfcRTL( AddrType )
    s.to_mem_wdata   = SendIfcRTL( DataType )

    @s.update
    def comb_logic():

      # For pick input register
      in0 = FuInType( 0 )
      in1 = FuInType( 0 )
      for i in range( num_inports ):
        s.recv_in[i].rdy = b1( 0 )
      if s.recv_opt.en:
        if s.recv_opt.msg.fu_in[0] != FuInType( 0 ):
          in0 = s.recv_opt.msg.fu_in[0] - FuInType( 1 )
          s.recv_in[in0].rdy = b1( 1 )
        if s.recv_opt.msg.fu_in[1] != FuInType( 0 ):
          in1 = s.recv_opt.msg.fu_in[1] - FuInType( 1 )
          s.recv_in[in1].rdy = b1( 1 )
        if s.recv_opt.msg.predicate == b1( 1 ):
          s.recv_predicate.rdy = b1( 1 )

      for j in range( num_outports ):
        s.recv_const.rdy = s.send_out[j].rdy or s.recv_const.rdy

      for j in range( num_outports ):
        s.recv_opt.rdy = s.send_out[j].rdy or s.recv_opt.rdy

      for j in range( num_outports ):
        for i in range( num_inports ):
          s.send_out[j].en = s.recv_in[i].en or s.send_out[j].en
        s.send_out[j].en = s.send_out[j].en and s.recv_opt.en

      s.send_out[0].msg = s.from_mem_rdata.msg
      s.to_mem_waddr.en = b1( 0 )
      s.to_mem_wdata.en = b1( 0 )
      if s.recv_opt.msg.ctrl == OPT_LD:
        s.recv_in[in0].rdy     = s.to_mem_raddr.rdy
        s.recv_in[in1].rdy     = s.from_mem_rdata.rdy
        s.to_mem_raddr.msg   = AddrType( s.recv_in[in0].msg.payload )
        s.to_mem_raddr.en    = s.recv_in[in0].en
        s.from_mem_rdata.rdy = s.send_out[0].rdy
        s.send_out[0].msg    = s.from_mem_rdata.msg
        s.send_out[0].en     = s.recv_opt.en
        s.send_out[0].msg.predicate = s.recv_in[in0].msg.predicate

      elif s.recv_opt.msg.ctrl == OPT_LD_CONST:
        for i in range( num_inports):
          s.recv_in[i].rdy = b1( 0 )
        s.recv_const.rdy     = s.to_mem_raddr.rdy
        s.to_mem_raddr.msg   = AddrType( s.recv_const.msg.payload )
        s.to_mem_raddr.en    = s.recv_const.en
        s.from_mem_rdata.rdy = s.send_out[0].rdy
        s.send_out[0].msg    = s.from_mem_rdata.msg
        s.send_out[0].en     = s.recv_opt.en
        # Const's predicate will always be true.
        s.send_out[0].msg.predicate = b1( 1 )

      elif s.recv_opt.msg.ctrl == OPT_STR:
        s.send_out[0].en   = s.from_mem_rdata.en and s.recv_in[in0].en and s.recv_in[in1].en
        s.recv_in[in0].rdy   = s.to_mem_waddr.rdy
        s.recv_in[in1].rdy   = s.to_mem_wdata.rdy
        s.to_mem_waddr.msg = AddrType( s.recv_in[0].msg.payload )
        s.to_mem_waddr.en  = s.recv_in[in0].en
        s.to_mem_wdata.msg = s.recv_in[in1].msg
        s.to_mem_wdata.en  = s.recv_in[in1].en
        s.send_out[0].en   = b1( 0 )
        s.send_out[0].msg  = s.from_mem_rdata.msg
        s.send_out[0].msg.predicate = s.recv_in[in0].msg.predicate and\
                                      s.recv_in[in1].msg.predicate
        if s.recv_opt.en and ( s.recv_in_count[in0] == CountType( 0 ) or\
                               s.recv_in_count[in1] == CountType( 0 ) ):
          s.recv_in[in0].rdy = b1( 0 )
          s.recv_in[in1].rdy = b1( 0 )
          s.send_out[0].msg.predicate = b1( 0 )

      else:
        for j in range( num_outports ):
          s.send_out[j].en = b1( 0 )

      if s.recv_opt.msg.predicate == b1( 1 ):
        s.send_out[0].msg.predicate = s.send_out[0].msg.predicate and\
                                      s.recv_predicate.msg.predicate

  def line_trace( s ):
    opt_str = " #"
    if s.recv_opt.en:
      opt_str = OPT_SYMBOL_DICT[s.recv_opt.msg.ctrl]
    out_str = ",".join([str(x.msg) for x in s.send_out])
    recv_str = ",".join([str(x.msg) for x in s.recv_in])
    return f'[recv: {recv_str}] {opt_str}(P{s.recv_opt.msg.predicate}) (const: {s.recv_const.msg}) ] = [out: {out_str}] (s.recv_opt.rdy: {s.recv_opt.rdy}, {OPT_SYMBOL_DICT[s.recv_opt.msg.ctrl]}, send[0].en: {s.send_out[0].en}) '
