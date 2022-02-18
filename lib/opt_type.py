#=========================================================================
# opt_type.py
#=========================================================================
# Operation types for all functional units.
#
# Author : Cheng Tan
#   Date : Nov 27, 2019

#-------------------------------------------------------------------------
# Constants
#-------------------------------------------------------------------------

from pymtl3 import *

OPT_START         = Bits6( 0  )
OPT_NAH           = Bits6( 1  )
OPT_PAS           = Bits6( 31 )
OPT_ADD           = Bits6( 2  )
OPT_ADD_CONST     = Bits6( 25 )
OPT_INC           = Bits6( 3  )
OPT_SUB           = Bits6( 4  )
OPT_LLS           = Bits6( 5  )
OPT_LRS           = Bits6( 6  )
OPT_MUL           = Bits6( 7  )
OPT_DIV           = Bits6( 26 )
OPT_OR            = Bits6( 8  )
OPT_XOR           = Bits6( 9  )
OPT_AND           = Bits6( 10 )
OPT_NOT           = Bits6( 11 )
OPT_LD            = Bits6( 12 )
OPT_STR           = Bits6( 13 )
OPT_EQ            = Bits6( 14 )
OPT_EQ_CONST      = Bits6( 33 )
OPT_LE            = Bits6( 15 )
OPT_RET           = Bits6( 35 )
OPT_BRH           = Bits6( 16 )
OPT_BRH_START     = Bits6( 34 )
OPT_PHI           = Bits6( 17 )
OPT_PHI_CONST     = Bits6( 32 )
OPT_SEL           = Bits6( 27 )
OPT_LD_CONST      = Bits6( 28 )
OPT_MUL_ADD       = Bits6( 18 )
OPT_MUL_CONST     = Bits6( 29 )
OPT_MUL_CONST_ADD = Bits6( 30 )
OPT_MUL_SUB       = Bits6( 19 )
OPT_MUL_LLS       = Bits6( 20 )
OPT_MUL_LRS       = Bits6( 21 )
OPT_MUL_ADD_LLS   = Bits6( 22 )
OPT_MUL_SUB_LLS   = Bits6( 23 )
OPT_MUL_SUB_LRS   = Bits6( 24 )

OPT_SYMBOL_DICT = {
  OPT_START         : "(start)",
  OPT_NAH           : "( )",
  OPT_PAS           : "(->)",
  OPT_ADD           : "(+)",
  OPT_ADD_CONST     : "(+')",
  OPT_INC           : "(++)",
  OPT_SUB           : "(-)",
  OPT_LLS           : "(<<)",
  OPT_LRS           : "(>>)",
  OPT_MUL           : "(x)",
  OPT_DIV           : "(/)",
  OPT_OR            : "(|)",
  OPT_XOR           : "(^)",
  OPT_AND           : "(&)",
  OPT_NOT           : "(~)",
  OPT_LD            : "(ld)",
  OPT_STR           : "(st)",
  OPT_EQ            : "(?=)",
  OPT_EQ_CONST      : "(?=')",
  OPT_LE            : "(?<)",
  OPT_BRH           : "(br)",
  OPT_RET           : "(ret)",
  OPT_BRH_START     : "(br*)",
  OPT_PHI           : "(ph)",
  OPT_PHI_CONST     : "(ph')",
  OPT_SEL           : "(sel)",
  OPT_LD_CONST      : "(ldcst)",
  OPT_MUL_ADD       : "(x +)",
  OPT_MUL_CONST_ADD : "(x' +)",
  OPT_MUL_CONST     : "(x')",
  OPT_MUL_SUB       : "(x -)",
  OPT_MUL_LLS       : "(x <<)",
  OPT_MUL_LRS       : "(x >>)",
  OPT_MUL_ADD_LLS   : "(x + <<)",
  OPT_MUL_SUB_LLS   : "(x + <<)",
  OPT_MUL_SUB_LRS   : "(x - >>)"

}
