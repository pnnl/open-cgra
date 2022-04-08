"""
==========================================================================
RetRTL.py
==========================================================================
Functional unit Ret as a CGRA tile.

Author : Cheng Tan
  Date : September 21, 2021

"""

from pymtl3             import *
from pymtl3.stdlib.ifcs import SendIfcRTL, RecvIfcRTL
from ...lib.opt_type    import *
from ..basic.Fu         import Fu

class RetRTL( Fu ):

  def construct( s, DataType, PredicateType, CtrlType,
                 num_inports, num_outports, data_mem_size ):

    super( RetRTL, s ).construct( DataType, PredicateType, CtrlType,
                                     num_inports, num_outports, data_mem_size )

    FuInType    = mk_bits( clog2( num_inports + 1 ) )
    num_entries = 2
    CountType   = mk_bits( clog2( num_entries + 1 ) )

    @s.update
    def comb_logic():

      # For pick input register
      in0 = FuInType( 0 )
      for i in range( num_inports ):
        s.recv_in[i].rdy = b1( 0 )

      s.recv_predicate.rdy = b1( 0 )

      if s.recv_opt.en:
        if s.recv_opt.msg.fu_in[0] != FuInType( 0 ):
          in0 = s.recv_opt.msg.fu_in[0] - FuInType( 1 )
          s.recv_in[in0].rdy = b1( 1 )

        if s.recv_opt.msg.predicate == b1( 1 ):
          s.recv_predicate.rdy = b1( 1 )

      for j in range( num_outports ):
        s.send_out[j].en = s.recv_opt.en
      if s.recv_opt.msg.ctrl == OPT_RET:
        # Branch is only used to set predication rather than delivering value.
        s.send_out[0].msg = DataType(s.recv_in[in0].msg.payload, b1( 0 ), b1( 0 ) )
        if s.recv_in[in0].msg.predicate == b1( 0 ):#s.const_zero.payload:
          s.send_out[0].msg.predicate = Bits1( 0 )
        else:
          s.send_out[0].msg.predicate = Bits1( 1 )

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
    return f'[recv: {recv_str}] {opt_str}(P{s.recv_opt.msg.predicate}) (const_reg: {s.recv_const.msg}, predicate_reg: {s.recv_predicate.msg}) ] = [out: {out_str}] (s.recv_opt.rdy: {s.recv_opt.rdy}, {OPT_SYMBOL_DICT[s.recv_opt.msg.ctrl]}, send[0].en: {s.send_out[0].en}) '
