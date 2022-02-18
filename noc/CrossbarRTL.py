"""
=========================================================================
Crossbar.py
=========================================================================

Author : Cheng Tan
  Date : Dec 8, 2019
"""

from pymtl3             import *
from pymtl3.stdlib.ifcs import SendIfcRTL, RecvIfcRTL

from ..lib.opt_type     import *

class CrossbarRTL( Component ):

  def construct( s, DataType, PredicateType, CtrlType,
                 num_inports=5, num_outports=5, bypass_point=4, id=0 ):

    OutType     = mk_bits( clog2( num_inports + 1 ) )
    s.bypass_point = bypass_point

    # Interface

    s.recv_opt       = RecvIfcRTL( CtrlType )
    s.recv_data      = [ RecvIfcRTL( DataType ) for _ in range ( num_inports  ) ]
    s.send_data      = [ SendIfcRTL( DataType ) for _ in range ( num_outports ) ]
    s.send_predicate = SendIfcRTL( PredicateType )

    # TODO: should include position information or not
    # s.pos  = InPort( PositionType )

    # Routing logic
    @s.update
    def update_signal():
      out_rdy = b1( 0 )
      s.send_predicate.en = b1( 0 )
      # predicate_out_rdy = b1( 0 )
      # For predication register update. 'predicate' and 'predicate_in' no need
      # to be active at the same time. Specifically, the 'predicate' is for
      # the operation at the current cycle while the 'predicate_in' accumulates
      # the predicate and pushes into the predicate register that will be used
      # in the future.
      if s.recv_opt.msg.predicate == b1( 1 ):
        # s.send_predicate.msg.payload = b1( 0 )
        # s.send_predicate.msg.predicate = b1( 0 )
        s.send_predicate.msg = PredicateType( b1(0), b1(0) )
      if s.recv_opt.msg.ctrl != OPT_START:
        for i in range( num_inports ):
          # Set predicate once the recv_data is stable (i.e., en == true).
          if s.recv_opt.msg.predicate_in[i] == b1( 1 ) and s.recv_data[i].en == b1( 1 ):
            s.send_predicate.en = b1( 1 )
            s.send_predicate.msg.payload = b1( 1 )
            s.send_predicate.msg.predicate = s.send_predicate.msg.predicate | s.recv_data[i].msg.predicate
            # predicate_out_rdy = b1( 1 )
        for i in range( num_outports ):
          in_dir  = s.recv_opt.msg.outport[i]
          out_rdy = out_rdy | s.send_data[i].rdy
#          s.send_data[i].msg.bypass = b1( 0 ) 
          if in_dir > OutType( 0 ) and s.send_data[i].rdy:
            in_dir = in_dir - OutType( 1 )
            s.recv_data[in_dir].rdy = s.send_data[i].rdy
            s.send_data[i].en       = s.recv_data[in_dir].en
            if s.send_data[i].en and s.recv_data[in_dir].rdy:
              s.send_data[i].msg.payload   = s.recv_data[in_dir].msg.payload
              s.send_data[i].msg.predicate = s.recv_data[in_dir].msg.predicate
#              s.send_data[i].msg = s.recv_data[in_dir].msg
              s.send_data[i].msg.bypass    = s.recv_data[in_dir].msg.bypass
            # The generate one can be send to other tile without buffering,
            # but buffering is still needed when 'other tile' is yourself
            # (i.e., generating output to self input). Here we avoid self 
            # connecting by checking whether the inport belongs to FU and
            # outport be towards to remote tiles to eliminate combinational
            # loop.
            if in_dir >= OutType( s.bypass_point ) and i<s.bypass_point:
              s.send_data[i].msg.bypass = b1( 1 ) 
#              print("in crossbar ", s, " set bypass ... s.recv_opt.msg.outport[", i, "]: ", s.recv_opt.msg.outport[i])
            else:
              s.send_data[i].msg.bypass = b1( 0 ) 
#            print("in crossbar if... s.send_data[", i, "].msg: ", s.send_data[i].msg, "; recv.rdy: ", s.recv_data[in_dir].rdy)
          else:
            s.send_data[i].en  = b1( 0 )
            #s.send_data[i].msg = b1( 0 )
#            print("in crossbar else... s.send_data[", i, "].msg: ", s.send_data[i].msg)

      else:
        for i in range( num_outports ):
#          s.send_data[i].msg.bypass = b1( 0 ) 
          s.send_data[i].en = b1( 0 )
      s.recv_opt.rdy = out_rdy# and predicate_out_rdy

  # Line trace
  def line_trace( s ):
    recv_str = "|".join([ str(x.msg) for x in s.recv_data ])
    out_str  = "|".join([ str(x.msg) for x in s.send_data ])
    pred_str = str( s.send_predicate.msg )
    return f"{recv_str} [{s.recv_opt.msg}] {out_str}-xbar.pred:{pred_str}"

