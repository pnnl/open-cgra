#=========================================================================
# ChannelRTL.py
#=========================================================================
# RTL channel module for connecting basic components to form accelerator.
# This simple channel has latency insensitive send/recv interfaces.
#
# Author : Cheng Tan
#   Date : Feb 22, 2020

from pymtl3                   import *
from pymtl3.stdlib.ifcs       import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.rtl.queues import NormalQueueRTL, PipeQueueRTL


class ChannelRTL( Component ):
  def construct(s, DataType, latency = 1 ):

    # Constant
    s.latency     = latency
    s.num_entries = 2
    s.data = DataType(0, 0)
    s.count = OutPort( mk_bits( clog2( s.num_entries+1 ) ) )

    # Interface
    s.recv  = RecvIfcRTL( DataType )
    s.send  = SendIfcRTL( DataType )


    # Component
    s.queues = [ NormalQueueRTL( DataType, s.num_entries )
                 for _ in range( s.latency ) ]

    s.count //= s.queues[s.latency - 1].count

    @s.update
    def process():
      if s.recv.msg.bypass == b1( 0 ):
        s.recv.rdy = s.queues[0].enq.rdy
        s.queues[0].enq.msg = s.recv.msg
        s.queues[0].enq.en  = s.recv.en and s.queues[0].enq.rdy
        for i in range(s.latency - 1):
          s.queues[i+1].enq.msg = s.queues[i].deq.ret
          s.queues[i+1].enq.en  = s.queues[i].deq.rdy and s.queues[i+1].enq.rdy
          s.queues[i].deq.en    = s.queues[i+1].enq.en
  
        s.send.msg  = s.queues[s.latency-1].deq.ret
        s.send.en   = s.send.rdy and s.queues[s.latency-1].deq.rdy
        s.queues[s.latency-1].deq.en   = s.send.en
      else:
        s.send.msg = s.data
        s.send.msg.payload = s.recv.msg.payload
        s.send.msg.predicate = s.recv.msg.predicate
        s.send.msg.bypass = b1( 0 )
        s.send.en = s.send.rdy and s.recv.en
        s.recv.rdy = s.send.rdy

  def line_trace( s ):
    trace = '>'
    for i in range( s.latency ):
      trace += s.queues[i].line_trace() + '>'
    return f"in:{s.recv.msg}({trace})out:{s.send.msg}.count:{s.count} ## "

