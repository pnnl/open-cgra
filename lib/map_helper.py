"""
==========================================================================
map_helper.py
==========================================================================
Helper map and functions to get corresponding functional unit and ctrl.

Author : Cheng Tan
  Date : Feb 22, 2020

"""

from .opt_type              import *
from ..fu.single.AdderRTL   import AdderRTL
from ..fu.single.ShifterRTL import ShifterRTL
from ..fu.single.LogicRTL   import LogicRTL
from ..fu.single.MulRTL     import MulRTL
from ..fu.single.MemUnitRTL import MemUnitRTL
from ..fu.single.CompRTL    import CompRTL
from ..fu.single.PhiRTL     import PhiRTL
from ..fu.single.RetRTL     import RetRTL
from ..fu.single.BranchRTL  import BranchRTL
from ..fu.single.SelRTL     import SelRTL

# -----------------------------------------------------------------------
# Global dictionary for UnitType and OptType
# -----------------------------------------------------------------------

unit_map = { "Adder"           : AdderRTL,
             "Mul"             : MulRTL,
             "Phi"             : PhiRTL,
             "Comp"            : CompRTL,
             "Branch"          : BranchRTL,
             "Ret"             : RetRTL,
             "Logic"           : LogicRTL,
             "Shifter"         : ShifterRTL,
             "Selecter"        : SelRTL,
             "MemUnit"         : MemUnitRTL }

opt_map  = { "OPT_START"       : OPT_START,
             "OPT_NAH"         : OPT_NAH,
             "OPT_ADD"         : OPT_ADD,
             "OPT_ADD_CONST"   : OPT_ADD_CONST,
             "OPT_INC"         : OPT_INC,
             "OPT_SUB"         : OPT_SUB,
             "OPT_LLS"         : OPT_LLS,
             "OPT_LRS"         : OPT_LRS,
             "OPT_MUL"         : OPT_MUL,
             "OPT_OR"          : OPT_OR,
             "OPT_XOR"         : OPT_XOR,
             "OPT_AND"         : OPT_AND,
             "OPT_NOT"         : OPT_NOT,
             "OPT_LD"          : OPT_LD,
             "OPT_STR"         : OPT_STR,
             "OPT_EQ"          : OPT_EQ,
             "OPT_EQ_CONST"    : OPT_EQ_CONST,
             "OPT_LE"          : OPT_LE,
             "OPT_RET"         : OPT_RET,
             "OPT_BRH"         : OPT_BRH,
             "OPT_BRH_START"   : OPT_BRH_START,
             "OPT_PHI"         : OPT_PHI,
             "OPT_PHI_CONST"   : OPT_PHI_CONST,
             "OPT_MUL_ADD"     : OPT_MUL_ADD,
             "OPT_MUL_SUB"     : OPT_MUL_SUB,
             "OPT_MUL_LLS"     : OPT_MUL_LLS,
             "OPT_MUL_LRS"     : OPT_MUL_LRS,
             "OPT_MUL_ADD_LLS" : OPT_MUL_ADD_LLS,
             "OPT_MUL_SUB_LLS" : OPT_MUL_SUB_LLS,
             "OPT_MUL_SUB_LRS" : OPT_MUL_SUB_LRS }


def getUnitType( fu_name ):
  return unit_map[ fu_name ]

def getOptType( opt_name ):
  return opt_map[ opt_name ]

