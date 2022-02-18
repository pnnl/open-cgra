"""
==========================================================================
messages.py
==========================================================================
Collection of messages definition.

Convention: The fields/constructor arguments should appear in the order
            of [ payload_nbits, predicate_nbits ]

Author : Cheng Tan
  Date : Dec 3, 2019
"""
from pymtl3 import *

#=========================================================================
# Generic data message
#=========================================================================

def mk_data( payload_nbits=16, predicate_nbits=1, bypass_nbits=1,
             prefix="CGRAData" ):

  PayloadType   = mk_bits( payload_nbits   )
  PredicateType = mk_bits( predicate_nbits )
  BypassType    = mk_bits( bypass_nbits )

  new_name = f"{prefix}_{payload_nbits}_{predicate_nbits}_{bypass_nbits}"

  def str_func( s ):
    return f"{s.payload}.{s.predicate}.{s.bypass}"

  return mk_bitstruct( new_name, {
      'payload'  : PayloadType,
      'predicate': PredicateType,
      'bypass'   : BypassType,
    },
    namespace = { '__str__': str_func }
  )

#=========================================================================
# Predicate signal
#=========================================================================

def mk_predicate( payload_nbits=1, predicate_nbits=1, prefix="CGRAData" ):

  PayloadType   = mk_bits( payload_nbits   )
  PredicateType = mk_bits( predicate_nbits )

  new_name = f"{prefix}_{payload_nbits}_{predicate_nbits}"

  def str_func( s ):
    return f"{s.payload}.{s.predicate}"

  return mk_bitstruct( new_name, {
      'payload'  : PayloadType,
      'predicate': PredicateType,
    },
    namespace = { '__str__': str_func }
  )

#=========================================================================
# Generic config message
#=========================================================================

def mk_ctrl( num_fu_in=2, num_inports=5, num_outports=5, prefix="CGRAConfig" ):

  ctrl_nbits    = 6
  CtrlType      = mk_bits( ctrl_nbits )
  InportsType   = mk_bits( clog2( num_inports  + 1 ) )
  OutportsType  = mk_bits( clog2( num_outports + 1 ) )
  FuInType      = mk_bits( clog2( num_fu_in + 1 ) )
  PredicateType = mk_bits( 1 )

  new_name = f"{prefix}_{ctrl_nbits}_{num_fu_in}_{num_inports}_{num_outports}"

  def str_func( s ):
    out_str = '(in)'

    for i in range( num_fu_in ):
      if i != 0:
        out_str += '-'
      out_str += str(int(s.fu_in[i]))

    out_str += '|(p)'
    out_str += str(int(s.predicate))

    out_str += '|(out)'
    for i in range( num_outports ):
      if i != 0:
        out_str += '-'
      out_str += str(int(s.outport[i]))

    out_str += '|(p_in)'
    for i in range( num_inports ):
      if i != 0:
        out_str += '-'
      out_str += str(int(s.predicate_in[i]))

    return f"(opt){s.ctrl}|{out_str}"

  field_dict = {}
  field_dict[ 'ctrl' ]         = CtrlType
  # The 'predicate' indicates whether the current operation is based on the partial
  # predication or not. Note that 'predicate' is different from the following
  # 'predicate_in', which contributes to the 'predicate' at the next cycle.
  field_dict[ 'predicate' ]    = PredicateType
  # The fu_in indicates the input port (i.e., ordering the oprands).
  field_dict[ 'fu_in' ]        = [ FuInType for _ in range( num_fu_in ) ]
  field_dict[ 'outport' ]      = [ InportsType for _ in range( num_outports ) ]
  # I assume one tile supports single predicate at the entire execution time, as
  # it is hard to distinguish predication for different operations (we automatically
  # update, i.e., 'or', the predicate stored in the predicate register). This should
  # be guaranteed by the compiler.
  field_dict[ 'predicate_in' ] = [ PredicateType for _ in range( num_inports ) ]

  # TODO: to support multiple predicate
  # field_dict[ 'predicate_in0' ] = ...
  # field_dict[ 'predicate_in1' ] = ...

  return mk_bitstruct( new_name, field_dict,
    namespace = { '__str__': str_func }
  )

