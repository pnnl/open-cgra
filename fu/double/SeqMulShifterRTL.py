"""
==========================================================================
SeqMulShifterRTL.py
==========================================================================
Mul followed by Shifter in sequential for CGRA tile.

Author : Cheng Tan
  Date : November 28, 2019

"""

from pymtl3              import *
from pymtl3.stdlib.ifcs  import SendIfcRTL, RecvIfcRTL
from ...lib.opt_type     import *
from ..basic.TwoSeqCombo import TwoSeqCombo
from ..single.MulRTL     import MulRTL
from ..single.ShifterRTL import ShifterRTL

class SeqMulShifterRTL( TwoSeqCombo ):

  def construct( s, DataType, PredicateType, CtrlType,
                 num_inports, num_outports, data_mem_size ):

    super( SeqMulShifterRTL, s ).construct( DataType, PredicateType,
                                            CtrlType, MulRTL, ShifterRTL,
                                            num_inports, num_outports,
                                            data_mem_size )

    @s.update
    def update_opt():

      s.Fu0.recv_opt.msg.fu_in[0] = Bits2(1)
      s.Fu0.recv_opt.msg.fu_in[1] = Bits2(2)
      s.Fu1.recv_opt.msg.fu_in[0] = Bits2(1)
      s.Fu1.recv_opt.msg.fu_in[1] = Bits2(2)

      if s.recv_opt.msg.ctrl == OPT_MUL_LLS:
        s.Fu0.recv_opt.msg.ctrl = OPT_MUL
        s.Fu1.recv_opt.msg.ctrl = OPT_LLS
      elif s.recv_opt.msg.ctrl == OPT_MUL_LRS:
        s.Fu0.recv_opt.msg.ctrl = OPT_MUL
        s.Fu1.recv_opt.msg.ctrl = OPT_LRS

      # TODO: need to handle the other cases

