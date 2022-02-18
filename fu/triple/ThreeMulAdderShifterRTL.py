"""
==========================================================================
ThreeMulShifterRTL.py
==========================================================================
Mul and Adder in parallel followed by a shifter for CGRA tile.

Author : Cheng Tan
  Date : November 28, 2019

"""

from pymtl3                import *
from pymtl3.stdlib.ifcs    import SendIfcRTL, RecvIfcRTL
from ...lib.opt_type       import *
from ..basic.ThreeCombo    import ThreeCombo
from ..single.MulRTL       import MulRTL
from ..single.AdderRTL     import AdderRTL
from ..single.ShifterRTL   import ShifterRTL

class ThreeMulAdderShifterRTL( ThreeCombo ):

  def construct( s, DataType, PredicateType, CtrlType,
                 num_inports, num_outports, data_mem_size ):

    super( ThreeMulAdderShifterRTL, s ).construct( DataType, PredicateType,
                                                   CtrlType, MulRTL,
                                                   AdderRTL, ShifterRTL,
                                                   num_inports, num_outports,
                                                   data_mem_size )

    @s.update
    def update_opt():

      s.send_out[0].en  = s.recv_in[0].en  and s.recv_in[1].en  and\
                          s.recv_in[2].en  and s.recv_in[3].en  and\
                          s.recv_opt.en
      s.send_out[1].en  = s.recv_in[0].en  and s.recv_in[1].en  and\
                          s.recv_in[2].en  and s.recv_in[3].en  and\
                          s.recv_opt.en

      s.Fu0.recv_opt.msg.fu_in[0] = Bits2(1)
      s.Fu0.recv_opt.msg.fu_in[1] = Bits2(2)
      s.Fu1.recv_opt.msg.fu_in[0] = Bits2(1)
      s.Fu1.recv_opt.msg.fu_in[1] = Bits2(2)
      s.Fu2.recv_opt.msg.fu_in[0] = Bits2(1)
      s.Fu2.recv_opt.msg.fu_in[1] = Bits2(2)

      if s.recv_opt.msg.ctrl == OPT_MUL_ADD_LLS:
        s.Fu0.recv_opt.msg.ctrl = OPT_MUL
        s.Fu1.recv_opt.msg.ctrl = OPT_ADD
        s.Fu2.recv_opt.msg.ctrl = OPT_LLS
      elif s.recv_opt.msg.ctrl == OPT_MUL_SUB_LLS:
        s.Fu0.recv_opt.msg.ctrl = OPT_MUL
        s.Fu1.recv_opt.msg.ctrl = OPT_SUB
        s.Fu2.recv_opt.msg.ctrl = OPT_LLS
      elif s.recv_opt.msg.ctrl == OPT_MUL_SUB_LRS:
        s.Fu0.recv_opt.msg.ctrl = OPT_MUL
        s.Fu1.recv_opt.msg.ctrl = OPT_SUB
        s.Fu2.recv_opt.msg.ctrl = OPT_LRS
      else:
        for j in range( num_outports ):
          s.send_out[j].en = b1( 0 )

      # TODO: need to handle the other cases

