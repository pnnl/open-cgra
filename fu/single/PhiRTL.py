"""
==========================================================================
PhiRTL.py
==========================================================================
Functional unit Phi for CGRA tile.

Author : Cheng Tan
  Date : November 30, 2019

"""

from pymtl3             import *
from pymtl3.stdlib.ifcs import SendIfcRTL, RecvIfcRTL
from ...lib.opt_type    import *
from ..basic.Fu         import Fu
import copy

class PhiRTL( Fu ):

  def construct( s, DataType, PredicateType, CtrlType,
                 num_inports, num_outports, data_mem_size ):

    super( PhiRTL, s ).construct( DataType, PredicateType, CtrlType,
                                  num_inports, num_outports, data_mem_size )

    FuInType    = mk_bits( clog2( num_inports + 1 ) )
    num_entries = 2
    CountType   = mk_bits( clog2( num_entries + 1 ) )

    @s.update
    def comb_logic():

      # For pick input register
      in0 = FuInType( 0 )
      in1 = FuInType( 0 )
      for i in range( num_inports ):
        s.recv_in[i].rdy = b1( 0 )

      s.recv_predicate.rdy = b1( 0 )

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
        s.send_out[j].en = s.recv_opt.en

      if s.recv_opt.msg.ctrl == OPT_PHI:
        if s.recv_in[in0].msg.predicate == Bits1( 1 ):
          s.send_out[0].msg.payload   = s.recv_in[in0].msg.payload
          s.send_out[0].msg.predicate = Bits1( 1 )
        elif s.recv_in[in1].msg.predicate == Bits1( 1 ):
          s.send_out[0].msg.payload   = s.recv_in[in1].msg.payload
          s.send_out[0].msg.predicate = Bits1( 1 )
        else: # No predecessor is active.
          s.send_out[0].msg.payload   = s.recv_in[in0].msg.payload
          s.send_out[0].msg.predicate = Bits1( 0 )
        if s.recv_opt.en and ( s.recv_in_count[in0] == CountType( 0 ) or\
                               s.recv_in_count[in1] == CountType( 0 ) ):
          s.recv_in[in0].rdy   = b1( 0 )
          s.recv_in[in1].rdy   = b1( 0 )
          s.recv_predicate.rdy = b1( 0 )
          s.send_out[0].msg.predicate = b1( 0 )

        if s.recv_opt.msg.predicate     == b1( 1 ) and\
           s.recv_predicate.msg.payload == b1( 0 ):
          s.recv_predicate.rdy = b1( 0 )
          s.recv_in[in0].rdy   = b1( 0 )
          s.recv_in[in1].rdy   = b1( 0 )

      elif s.recv_opt.msg.ctrl == OPT_PHI_CONST:

        s.send_out[0].msg.predicate = Bits1( 1 )
        if s.recv_in[in0].msg.predicate == Bits1( 1 ):
          s.send_out[0].msg.payload   = s.recv_in[in0].msg.payload
        else:
          s.send_out[0].msg.payload   = s.recv_const.msg.payload

        # Predication signal not arrive yet.
        if s.recv_opt.msg.predicate     == b1( 1 ) and\
           s.recv_predicate.msg.payload == b1( 0 ):
          #s.recv_predicate.rdy = b1( 0 )
          s.recv_in[in0].rdy   = b1( 0 )

      else:
        for j in range( num_outports ):
          s.send_out[j].en = b1( 0 )

      if s.recv_opt.msg.predicate == b1( 1 ):

        s.send_out[0].msg.predicate = s.send_out[0].msg.predicate and\
                                      s.recv_predicate.msg.predicate
        # The PHI_CONST operation executed an the first time does not need predication signal.
        if s.recv_opt.msg.ctrl == OPT_PHI_CONST:
          if s.recv_predicate.msg.payload == b1( 0 ):
            s.send_out[0].msg.predicate = b1( 1 )
#                                        ( s.recv_predicate.msg.payload == b1( 0 ) )

  def line_trace( s ):
    opt_str = " #"
    if s.recv_opt.en:
      opt_str = OPT_SYMBOL_DICT[s.recv_opt.msg.ctrl]
    out_str = ",".join([str(x.msg) for x in s.send_out])
    recv_str = ",".join([str(x.msg) for x in s.recv_in])
    return f'[recv: {recv_str}] {opt_str}(P{s.recv_opt.msg.predicate}) (const_reg: {s.recv_const.msg}, predicate_reg: {s.recv_predicate.msg}) ] = [out: {out_str}] (s.recv_opt.rdy: {s.recv_opt.rdy}, {OPT_SYMBOL_DICT[s.recv_opt.msg.ctrl]}, send[0].en: {s.send_out[0].en}) '
