"""
==========================================================================
CompRTL.py
==========================================================================
Functional unit for performing comparison.

Author : Cheng Tan
  Date : December 2, 2019

"""

from pymtl3             import *
from pymtl3.stdlib.ifcs import SendIfcRTL, RecvIfcRTL
from ...lib.opt_type    import *
from ..basic.Fu         import Fu

class CompRTL( Fu ):

  def construct( s, DataType, PredicateType, CtrlType,
                 num_inports, num_outports, data_mem_size ):

    super( CompRTL, s ).construct( DataType, PredicateType, CtrlType,
                                   num_inports, num_outports,
                                   data_mem_size )

    s.const_one  = DataType(1, 0)
    FuInType     = mk_bits( clog2( num_inports + 1 ) )
    num_entries  = 2
    CountType    = mk_bits( clog2( num_entries + 1 ) )

    # data:      s.recv_in[0]
    # reference: s.recv_in[1] (or recv_const)

    @s.update
    def read_reg():

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

      predicate = s.recv_in[in0].msg.predicate & s.recv_in[in1].msg.predicate
      s.send_out[0].msg = s.const_one

      for j in range( num_outports ):
        s.send_out[j].en = s.recv_opt.en

      if s.recv_opt.msg.ctrl == OPT_EQ:
        if s.recv_in[in0].msg.payload == s.recv_in[in1].msg.payload:
          s.send_out[0].msg = s.const_one
          s.send_out[0].msg.predicate = predicate
        else:
          s.send_out[0].msg = s.const_zero
          s.send_out[0].msg.predicate = predicate
        if s.recv_opt.en and ( s.recv_in_count[in0] == CountType( 0 ) or\
                               s.recv_in_count[in1] == CountType( 0 ) ):
          s.recv_in[in0].rdy = b1( 0 )
          s.recv_in[in1].rdy = b1( 0 )
          s.send_out[0].msg.predicate = b1( 0 )

      elif s.recv_opt.msg.ctrl == OPT_EQ_CONST:
        if s.recv_in[in0].msg.payload == s.recv_const.msg.payload:
          s.send_out[0].msg = s.const_one
          s.send_out[0].msg.predicate = b1( 1 )
        else:
          s.send_out[0].msg = s.const_zero
          s.send_out[0].msg.predicate = b1( 1 )

      elif s.recv_opt.msg.ctrl == OPT_LE:
        if s.recv_in[in0].msg.payload < s.recv_in[in1].msg.payload:
          s.send_out[0].msg = s.const_one
          s.send_out[0].msg.predicate = predicate
        else:
          s.send_out[0].msg = s.const_zero
          s.send_out[0].msg.predicate = predicate
        if s.recv_opt.en and ( s.recv_in_count[in0] == CountType( 0 ) or\
                               s.recv_in_count[in1] == CountType( 0 ) ):
          s.recv_in[in0].rdy = b1( 0 )
          s.recv_in[in1].rdy = b1( 0 )

      else:
        for j in range( num_outports ):
          s.send_out[j].en = b1( 0 )

      if s.recv_opt.msg.predicate == b1( 1 ):
        s.send_out[0].msg.predicate = s.send_out[0].msg.predicate and\
                                      s.recv_predicate.msg.predicate
