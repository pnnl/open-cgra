"""
=========================================================================
CGRAFL.py
=========================================================================
CGRAFL -- running DFG nodes one by one.

Author : Cheng Tan
  Date : Feb 13, 2020

"""

from pymtl3         import *
from ..lib.opt_type import *
from ..lib.messages import *

#------------------------------------------------------------------------
# Assuming that the elements in FuDFG are already ordered well.
#------------------------------------------------------------------------
def CGRAFL( FuDFG, DataType, CtrlType, src_const ):#, data_spm ):

  live_out_val  = DataType( 0, 0 )
  live_out_ctrl = DataType( 0, 0 )

  data_spm = FuDFG.data_spm
  print("data SPM: ", data_spm)

  while live_out_ctrl.predicate == Bits1( 0 ):
    for node in FuDFG.nodes:
      current_input = []
      current_input_predicate = 0
#      print("id: ", node.id, " node.num_const: ", node.num_const, "; node.num_input: ", node.num_input)
      # Assume const goes in first, then the output from predecessor.
      if node.num_const != 0:
        for i in range( node.num_const ):
          current_input.append( src_const[node.const_index[i]] );
      if node.num_input != 0:
        for value in node.input_value:
          current_input.append(value);
 
      result  = [ DataType( 0, 1 ) for _ in node.num_output ]
      if node.opt_predicate == 1:
        current_input_predicate = node.input_predicate
        #current_input_predicate = node.input_predicate
      print( "id: ", node.id, ", current_input: ", current_input, ", current_input_predicate: ", current_input_predicate )
      if node.opt == OPT_ADD:
        result[0].payload = current_input[0].payload + current_input[1].payload
      elif node.opt == OPT_SUB:
        result[0].payload = current_input[0].payload - current_input[1].payload
      elif node.opt == OPT_MUL:
        result[0].payload = current_input[0].payload * current_input[1].payload
      elif node.opt == OPT_PHI:
        if current_input[1].predicate == Bits1( 1 ):
          result[0].payload = current_input[1].payload
        else:
          result[0].payload = current_input[0].payload
      elif node.opt == OPT_LD:
        result[0].payload = data_spm[current_input[0].payload]
      elif node.opt == OPT_EQ:
#        if current_input[0].payload == current_input[1].payload:
        # FIXME: need to specify the constant input for each node
        if current_input[0].payload == current_input[1].payload:
          result[0] = DataType( 1, 1)
        else:
          result[0] = DataType( 0, 1)
      elif node.opt == OPT_BRH:
        # Br node does not output any meaningful value but a predication
        result[0].payload  = 0
        # Cmp result goes into [0]
        if current_input[0].payload == 0:
          result[0].predicate = Bits1( 1 )
          for j in range( node.num_output[0] ):
            FuDFG.get_node(node.output_node[0][j]).updatePredicate( 1 )
          for j in range( node.num_output[1] ):
            FuDFG.get_node(node.output_node[1][j]).updatePredicate( 0 )
        else:
          result[0].predicate  = Bits1( 0 )
          for j in range( node.num_output[0] ):
            FuDFG.get_node(node.output_node[0][j]).updatePredicate( 0 )
          for j in range( node.num_output[1] ):
            FuDFG.get_node(node.output_node[1][j]).updatePredicate( 1 )

        # if len(node.num_output) > 1:
        #   result[1] = DataType( 0, 0 )
        #   result[1].payload = 0
        #   if current_input[0].payload == 0:
        #     result[1].predicate = Bits1( 0 )
        #   else:
        #     result[1].predicate = Bits1( 1 )

      # Currently, treat BRH node as the exit node that could contain live_out_ctrl
      if node.live_out_ctrl != 0:
        if node.opt_predicate == 1:
          for i in range(len( node.num_output )):
            result[i].predicate = result[i].predicate and current_input_predicate
        # case of 'FALSE' ([0]->'FALSE' path; [1]->'TRUE' path)
        if result[0].predicate == 1:
          live_out_ctrl.predicate = Bits1( 0 )
        # Terminate the execution when BRANCH leads to a 'TRUE'
        else:
          live_out_ctrl.predicate = Bits1( 1 )
        if node.opt_predicate == 1:
          live_out_ctrl.predicate = live_out_ctrl.predicate and current_input_predicate
  
      # We allow single live out value in the DFG.
      if node.live_out_val != 0:
        live_out_val.payload   = result[0].payload
        live_out_val.predicate = result[0].predicate

      if node.opt_predicate == 1:
        for i in range(len( node.num_output )):
          result[i].predicate = result[i].predicate and current_input_predicate

      # BRH only updates predicate rather than values.
      if node.opt != OPT_BRH:
        for i in range( len( node.num_output ) ):
  #        print( "see node.num_output[i]: ", node.num_output[i] )
          for j in range( node.num_output[i] ):
            node.updateOutput( i, j, result[i] )
            FuDFG.get_node(node.output_node[i][j]).updateInput( result[i] )

      print( "id: ", node.id, " current output: ", result )
      if live_out_ctrl.predicate == Bits1( 1 ):
        break
  

    print( "[ current iteration live_out_val: ", live_out_val, " ]" )
    print( "--------------------------------------" )
  
  print( "final live_out: ", live_out_val )
  return live_out_val.payload, data_spm

