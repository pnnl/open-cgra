#=========================================================================
# RegisterRTL.py
#=========================================================================
# RTL register module specifically for predication.
#
# Author : Cheng Tan
#   Date : Aug 22, 2021

from pymtl3                   import *
from pymtl3.stdlib.ifcs       import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.rtl.queues import NormalQueueRTL, PipeQueueRTL


class RegisterRTL( Component ):
  def construct(s, DataType, latency = 1 ):

    # Constant
    s.latency     = latency
    s.num_entries = 2
    s.data = DataType( 0 )

    # Interface
    s.recv  = RecvIfcRTL( DataType )
    s.send  = SendIfcRTL( DataType )

    # Component
    s.queues = [ NormalQueueRTL( DataType, s.num_entries )
                 for _ in range( s.latency ) ]

    @s.update
    def process():
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

  def line_trace( s ):
    trace = '>'
    for i in range( s.latency ):
      trace += s.queues[i].line_trace() + '>'
    return f"{s.recv.msg}({trace}){s.send.msg} ## "

