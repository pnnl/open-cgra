"""
==========================================================================
ConstQueueRTL.py
==========================================================================
Constant queue used for simulation.

Author : Cheng Tan
  Date : Jan 20, 2020

"""

from pymtl3             import *
from pymtl3.stdlib.ifcs import SendIfcRTL, RecvIfcRTL
from ...lib.opt_type    import *
from pymtl3.stdlib.rtl  import RegisterFile

class ConstQueueRTL( Component ):

  def construct( s, DataType, const_list=None ):

    # Constant
    num_const = len( const_list )
    AddrType = mk_bits( clog2( num_const+1 ) )
    TimeType = mk_bits( clog2( num_const+1 ) )

    # Interface

    s.send_const = SendIfcRTL( DataType )

    # Component

    s.const_queue = [ DataType( 0 ) for _ in range( num_const ) ]
    for i in range( len( const_list ) ):
      s.const_queue[ i ] = const_list[i]
    s.cur  = Wire( AddrType )

    @s.update
    def load():
      s.send_const.msg = s.const_queue[ s.cur ]

    @s.update
    def update_en():
      s.send_const.en = s.send_const.rdy

    @s.update_ff
    def update_raddr():
      if s.send_const.rdy:
        if s.cur + AddrType( 1 )  >= AddrType( num_const ):
          s.cur <<= AddrType( 0 )
        else:
          s.cur <<= s.cur + AddrType( 1 )

  def line_trace( s ):
    out_str  = "||".join([ str(data) for data in s.const_queue ])
    return f'[{out_str}] : {s.send_const.msg}({s.send_const.en})'

