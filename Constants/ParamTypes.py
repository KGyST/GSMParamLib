# FIXME to handle unknown parameter types as string representations

PAR_UNKNOWN     = 0
PAR_LENGTH      = 1
PAR_ANGLE       = 2
PAR_REAL        = 3
PAR_INT         = 4
PAR_BOOL        = 5
PAR_STRING      = 6
PAR_MATERIAL    = 7
PAR_LINETYPE    = 8
PAR_FILL        = 9
PAR_PEN         = 10
PAR_SEPARATOR   = 11
PAR_TITLE       = 12
PAR_LIGHTSW     = 13
PAR_COLORRGB    = 14
PAR_INTENSITY   = 15
PAR_BMAT        = 16
PAR_PROF        = 17
PAR_DICT        = 18
PAR_COMMENT     = 19

PARFLG_CHILD    = 1
PARFLG_BOLDNAME = 2
PARFLG_UNIQUE   = 3
PARFLG_HIDDEN   = 4

__all__ = [
    'PAR_LENGTH',
    'PAR_ANGLE',
    'PAR_REAL',
    'PAR_INT',
    'PAR_BOOL',
    'PAR_STRING',
    'PAR_MATERIAL',
    'PAR_LINETYPE',
    'PAR_FILL',
    'PAR_PEN',
    'PAR_SEPARATOR',
    'PAR_TITLE',
    'PAR_LIGHTSW',
    'PAR_COLORRGB',
    'PAR_INTENSITY',
    'PAR_BMAT',
    'PAR_PROF',
    'PAR_DICT',
    'PAR_COMMENT',

    'PARFLG_CHILD',
    'PARFLG_BOLDNAME',
    'PARFLG_UNIQUE',
    'PARFLG_HIDDEN'
]