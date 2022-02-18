"""
==========================================================================
ctrl_helper.py
==========================================================================
Helper classes and functions to wrap configure signal for each tile on 
CGRA.

Author : Cheng Tan
  Date : Feb 22, 2020

"""

from .messages                   import *
from .map_helper                 import *
from ..fu.flexible.FlexibleFuRTL import FlexibleFuRTL

import json

class TileCtrl:

  def __init__( s, FuType, CtrlType, RouteType, x, y, num_fu_in,
                num_inports, num_outports, II ):
    s.FuType = FuType
    s.CtrlType = CtrlType
    s.RouteType = RouteType
    s.x      = x
    s.y      = y
    s.II     = II
#    s.opts   = [ CtrlType( 0, 0 ) ] * II
#    s.routes = [ [ RouteType( 0 ) ] * num_outports ] * II
    FuInType     = mk_bits( clog2( num_fu_in + 1 ) )
    pickRegister = [ FuInType( 0 ) for x in range( num_fu_in ) ]
#    pickRegister[2] = FuInType( 0 )
#    pickRegister[3] = FuInType( 0 )
    s.ctrl   = [ CtrlType( OPT_NAH, b1( 0 ), pickRegister,
                           [ RouteType( 0 ) ] * num_outports,
                           [ b1( 0 ) ] * num_inports ) ] * II

  def update_ctrl( s, cycle, ctrl ):
#    s.opts[cycle]   = opt
#    s.routes[cycle] = route
    s.ctrl[ cycle ] = ctrl

  def get_ctrl( s ):
    return s.ctrl

def get_tile( x, y, tiles ):
  for tile in tiles:
    if tile.x == x and tile.y == y:
      return tile
  return None

class CGRACtrl:

  def __init__( s, json_file_name, CtrlType, RouteType, width, height,
                num_fu_in, num_inports, num_outports, II ):
    s.tiles = []
    # X is the horizontal axis while Y is the vertical axis
    for y in range( height ):
      for x in range( width ):
        s.tiles.append( TileCtrl( FlexibleFuRTL, CtrlType, RouteType,
                                  x, y, num_fu_in, num_inports, num_outports,
                                  II ) )

    FuInType     = mk_bits( clog2( num_fu_in + 1 ) )
    pickRegister = [ FuInType( x+1 ) for x in range( num_fu_in ) ]

    with open( json_file_name ) as json_file:
      ctrls = json.load( json_file )
      for ctrl in ctrls:
        tile  = get_tile( ctrl['x'], ctrl['y'], s.tiles )
        reg = None
        reg = [ FuInType( 0 ) for x in range( num_fu_in ) ]
        if ctrl['opt'] != "OPT_NAH":
          reg[0] = FuInType( 1 )
          reg[1] = FuInType( 2 )
        route = []
#        reg[2] = FuInType( 0 )
#        reg[3] = FuInType( 0 )
        for i in range( num_outports ):
          out = ctrl['out_'+str(i)]
          out = RouteType( int(out) + 1 ) if out != "none" else RouteType( 0 )
          route.append( out )

        for i in range( num_fu_in ):
          if 'fu_in_'+str(i) in ctrl:
            for j in range( num_fu_in ):
              reg[j] = FuInType( 0 )
            break

        for i in range( num_fu_in ):
          if 'fu_in_'+str(i) in ctrl:
            fu_in = ctrl['fu_in_'+str(i)]
            reg[i] = FuInType( fu_in )

        predicate_in = []
        if 'predicate_in' in ctrl:
          for i in range( num_inports ):
            if i in ctrl['predicate_in']:
              predicate_in.append( b1( 1 ) )
            else:
              predicate_in.append( b1( 0 ) )

        tile.update_ctrl( ctrl['cycle']%II, CtrlType( opt_map[ ctrl['opt'] ],
                                                      ctrl['predicate'], reg,
                                                      route, predicate_in ) )
#          print( tile.ctrl )

  def get_ctrl( s ):
    ctrls = []
    for tile in s.tiles:
      ctrls.append( tile.ctrl )
    return ctrls

def wrap_ctrl_signals(CtrlType, raw_ctrls):
  pass

