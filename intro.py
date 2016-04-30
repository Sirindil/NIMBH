# -*- coding: utf-8 -*-
"""
Created on Tue Apr 26 22:00:03 2016

@author: Sirindil
"""
import os
import sys
import time
import shlex
import random
import string
import struct
import time
import platform
import subprocess
import ctypes
from ctypes import windll, byref, wintypes, Structure, c_ulong
from ctypes.wintypes import SMALL_RECT
from colorama import init, Fore, Back, Style, Cursor
import win32com.client
import win32api, win32con
import ctypes
from ctypes import wintypes
from colorama import init
import re
from functools import partial
import winsound
#import pywinauto

init(strip=not sys.stdout.isatty()) # strip colors if stdout is redirected
user32 = ctypes.WinDLL('user32', use_last_error=True)

class POINT(Structure):
    _fields_ = [("x", c_ulong), ("y", c_ulong)]


def queryMousePosition():
    pt = POINT()
    windll.user32.GetCursorPos(byref(pt))
    return { "x": pt.x, "y": pt.y}


def click(x,y):
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,x,y,0,0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)


CSI = '\033['
OSC = '\033]'
BEL = '\007'


def clear_line(mode=2):
    return CSI + str(mode) + 'K'


INPUT_MOUSE    = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_UNICODE     = 0x0004
KEYEVENTF_SCANCODE    = 0x0008

MAPVK_VK_TO_VSC = 0

# msdn.microsoft.com/en-us/library/dd375731
VK_TAB  = 0x09
VK_MENU = 0x12
VK_RETURN = 0x0D
VK_CONTROL = 0x11
VK_D = 0x44
# C struct definitions

wintypes.ULONG_PTR = wintypes.WPARAM

class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx",          wintypes.LONG),
                ("dy",          wintypes.LONG),
                ("mouseData",   wintypes.DWORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk",         wintypes.WORD),
                ("wScan",       wintypes.WORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

    def __init__(self, *args, **kwds):
        super(KEYBDINPUT, self).__init__(*args, **kwds)
        # some programs use the scan code even if KEYEVENTF_SCANCODE
        # isn't set in dwFflags, so attempt to map the correct code.
        if not self.dwFlags & KEYEVENTF_UNICODE:
            self.wScan = user32.MapVirtualKeyExW(self.wVk,
                                                 MAPVK_VK_TO_VSC, 0)

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg",    wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD))

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT))
    _anonymous_ = ("_input",)
    _fields_ = (("type",   wintypes.DWORD),
                ("_input", _INPUT))

LPINPUT = ctypes.POINTER(INPUT)

def _check_count(result, func, args):
    if result == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    return args

user32.SendInput.errcheck = _check_count
user32.SendInput.argtypes = (wintypes.UINT, # nInputs
                             LPINPUT,       # pInputs
                             ctypes.c_int)  # cbSize

# Functions

def PressKey(hexKeyCode):
    x = INPUT(type=INPUT_KEYBOARD,
              ki=KEYBDINPUT(wVk=hexKeyCode))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

def ReleaseKey(hexKeyCode):
    x = INPUT(type=INPUT_KEYBOARD,
              ki=KEYBDINPUT(wVk=hexKeyCode,
                            dwFlags=KEYEVENTF_KEYUP))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

def AltEnter():
    """Press Alt+Tab and hold Alt key for 2 seconds
    in order to see the overlay.
    """
    PressKey(VK_MENU)   # Alt
    PressKey(VK_RETURN)    # Enter
    ReleaseKey(VK_RETURN)  # Enter~
    time.sleep(0.5)
    ReleaseKey(VK_MENU) # Alt~

def CtlD():
    PressKey(VK_CONTROL)   # Alt
    PressKey(VK_D)    # Enter
    ReleaseKey(VK_D)  # Enter~
    time.sleep(0.5)
    ReleaseKey(VK_CONTROL) # Alt~

user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

def terminalSize():  # Windows only
    try:
        from ctypes import windll, create_string_buffer
        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (bufx, bufy, curx, cury, wattr,
             left, top, right, bottom,
             maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            sizex = right - left + 1
            sizey = bottom - top + 1
            return sizex, sizey
    except:
        pass


def get_terminal_size():
    """ getTerminalSize()
     - get width and height of console
     - works on linux,os x,windows,cygwin(windows)
     originally retrieved from:
     http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    """
    current_os = platform.system()
    tuple_xy = None
    if current_os == 'Windows':
        tuple_xy = _get_terminal_size_windows()
        if tuple_xy is None:
            tuple_xy = _get_terminal_size_tput()
            # needed for window's python in cygwin's xterm!
    if tuple_xy is None:
        print("default")
        tuple_xy = (80, 25)      # default value
    return tuple_xy


def _get_terminal_size_windows():
    try:
        from ctypes import windll, create_string_buffer
        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (bufx, bufy, curx, cury, wattr,
             left, top, right, bottom,
             maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            sizex = right - left + 1
            sizey = bottom - top + 1
            return sizex, sizey
    except:
        pass
 

def _get_terminal_size_tput():
    # get terminal width
    # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    try:
        cols = int(subprocess.check_call(shlex.split('tput cols')))
        rows = int(subprocess.check_call(shlex.split('tput lines')))
        return (cols, rows)
    except:
        pass


def clear():
    sys.stderr.write("\x1b[2J\x1b[H")

mypicture = """\
888888OZZO888888888888MMMMMMMMNNMMMMMMMMMMMMMMMMMMMMMMNNMND8OOZZ$$ZOOOOOOOZZZZZZ
8888888OZO88888888888NMMMMMNNNMMMMMMMMMMMMMMMMMMMMMMMMMMMMNDOOOO$ZZZZZZZZZZZZZ$Z
8888888OOO8888888888NMMMMMMN8888888NNNNMMMMMMMMMMMMMMMMMMMMMN8OO$ZZOOOOOOOOOOOZZ
8888888OZ88888888888MMMMMND8ZZ$7777$O88888DNMMMMMMMMMMMMMMMMMN8OZZZZZZZZZZZZ$Z$$
8888888OOO888888888DMMMNDOZ$7777I???????I77$$DNMMMMMMMMMMMMMMMDOZ$ZOOOOOOOOZZZZZ
8888888OOO888888888NMMNOZ$7II??++++=+++++++?I7ZDNNMMMMMMMMMMMMM8ZZZZOZZZZZZZZ$Z$
88888888O88888OOOOOMMNOZ$7III??++==========++?I$8DDNNMMMMMMMMMMNZZZZOZZZOOZZOZZZ
888888888888888888DNNOZ$$77I??+++============++?IODDNNMMMMMMMMMN8ZZOZOOZZZZZZZZ$
888888888888888888DN8Z$$7I????++=============++??I7$ODMMMMMMMMMMDOZZZZZZZZZZZZZZ
88888888888888NMNDND8NNO$I++====~~~===++++++++???I77Z8NNMMMMMMMMD8OZZZZZZZZZZZZ$
8888888888888MMMMMNNMNNNND87=~~~~~~~~~===++???I???I7ZODNMMMMMMMMNOOOOOOOZZZZZZZ$
DD8888888888DMMMMMNZI?+?$8D8+~~~:::::~~=+????IIIII77$ODNNMMMMMMMM88OOOOOOOOOZZZZ
DD8888888888DDNMMN8I?++==+?+?=~::::+$ODDDDDD88O$77777ODNNMMMMMMMN8888888OOOOOOOO
DDD888888888888NNNO77$7I++=?++=~::~+7$$$ZZOODNNDOZ$$7ZDNNMMMMMMMDDD88888888OOOOO
DDDD88D8DD8DDD8888$ON8O$$II++??=:~~~=+=~==~~~?78D8Z$$$ODNMMMMMMMD88888888888OOOO
NDDDD8DDDDD88D888$78O+~D8D7II7I???=~=+?+===~~~+IODO$77$8DNMMMMMN8888888888888OOO
MNDD8DDDD888DD888$$Z7$7Z$Z7777I7$7+=II7II7II+==?I8O$$$$ONNNNMMMD88888888888888OO
MNNNDDDDDDDDDDD8O7III?+??I7Z7II7$$7?$=::8DNOZ7I?I$$7$$Z8NNNMMMNDD888888888888888
MMNNNDDDDDDDDDD8Z7IIII?II7$ZII$$$$$I++IIOD8ODO7III777$ODNNNNMMNDDDD8888888888888
MMMNNDDDDDDDDDD8$I??????I7?=+?$Z$$7?+++===?I7II???I77$ONMNMNNND888D8888888888888
MMNNNDDDDDDDDDD87I?++++???=::~?ZO$I====++==+?????II77Z8NMMNNMDDDDD88888888888888
MMMNNDNNDDDDDND87?+===~=+I+~===?OZ+====~==+++???II777Z8NMD$$77OD88D8888888888888
MMMNNNNNNNNNNNND7==~:~~+?II=IZD=I$~~~~~~==~===+?I7$$$Z8D8$7I77?8D888D88888888888
MMMMNNNNNNNNNNND7+=~~=+?7I=++++I7I~~~~~~~~~~==+?I7$$ZO8DOO?+I7?8DDDDD88888888888
MMMMMNNNNNNNNNND7+==+?II?~:::=?I?+=~::::~~===++?I7$ZZO8Z$$=:7?8DD8DDDDDDDDDDDDD8
MMMMMMMMNNNNNNND$?++=?I+=~~~:~+?++=~:,,::~==++??I7ZZO8$$$7=:7ZDDD8DD8D8888888888
MMMMMMMMMMNNNNNN7I+=+7$7II??=~~~~===~:,::~=+++?I7$OO8O7I?$I78DDD88DDDD8888888888
MMMMMMMMMMNNNNNN77?=+I$$7$OZ77I+~:~=~::::~==++?I7$O887?+IZ$8DDDDDDDDDDD888888888
MMMMMMMMMMNNNNNNO7I++++??IIIII$Z$?=~~:::~~==+??I7ZODDNO$8DDDDDDDDDDDDD8DD8D88888
MMMMMMMMMMMNMMMMM7I?++====~~:::~~~~~~~~~=====+?I$O8DDNNNNDDDDDDDDDDDDDDDDDD8D888
MMMMMMMMMMMMMMMMM$7I?======~::::~~~~~~~~===+++?7$888DNNNNNDDDDDDDDDDDDDDDDDDDD88
MMMMMMMMMMMMMMMMMNZ$7?++++++=~::~~~~~=~====++?IZOOO8NNNNNNNNNDDDDDDDDDDDDDDDDDD8
MMMMMMMMMMMMMMMMMMZ$I?=~~=====~~~==========+?7$88OODNNNNNNNNNNDDDDDDDDDDDDDDDDD8
MMMMMMMMMMMMMMMMMN7$I+~:::::~=~====+====++?I7$8OOO8NNNNNNNNNNNNDDDDDDDDDDDDDDDD8
MMMMMMMMMMMMMMMMND$?$?==::::::~=++??+???I7$ZOO$$Z8DNNNNNNNNNNNNDDDDDDDDDDDDDDDDD
MMMMMMMMMMMMMMMMMO$??77??+===~++?I77777$$ZZ7777$ZDNNNNNNNNNNNNNNDDDDDDDDDDDDDDDD
MMMMMMNNNMMMMMMMN$$++77?+?I77$$$$$777II?????II7Z8MMMMNNNNNNNNNNNDDDDNDDDDDDDDDDD
MMMMMMNNMMMMMMMMNOZ+=+7======+??????++====+??I$8DMMMMNNNNNNNNNNNDNNNNNDDDDDDDDDD
MMMMMMNNMMMMMMMMMM8+==??=~~~=~~~===~~~~~~==+I7Z8NMMMMMNNNNNNNNNNNNNNNNNNDDDDDDDD
NNMMMMMMMMMMNNNNNMM$=~=??===~====~:::~~~=++?I$ONMMMMMMMMNNNNNNNNNNNNNNNNNDDNDDDD
MMMMNMMMMMMNNNNNNMMMM8$??I7$ZO8888OOZ7III?II$DNNNMMMMMMMMNNNNNNNNNNNNNNNNNDNNDDD
MMMNMMMMMMMMMNNNNNMMMMNNNNNNNNNNNNNNNNNNNNNMMNNMMMMMMMMMMMMNNNNNNNNNNNNNNDDNNDDD
"""

castle = """\
~~~~~~~~~~~~~~~~~~~~~~~~~~~~O?~~+$+?~~~~~~~~~~=?O$~Z7~ZI++~~~~8$Z=$O~$+I?=~~~~~=~==N$$=~IO=$7I=================~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~::8=8$ZI?+I$=?~~~~~~~~~ONN87II7$7?=$+8788?III7ZI+$I~~~~~~~~~~NON+8D8D7$?ZI?~==~~~===~~~~~~~~~~~~:I
~~~~~~~~~~~~~:~:::::::::N8Z$7?+?++I~+~:::::::O8DOMNNMMM=~ZO88D8IMMM7NN?7+~~~~~~~~~~NODDDDD??II+~~~~~~~~~~~~~~~~~~~~~~~:N
~~~~~~~~~~~~::::::::::::D8887I?+I+==$::::::::8NNO$7=O?D7DOMNMDN?8N7ION=NN?~~~~~~~~~NODDOOD$$7?++~~~~~~~~~~~~~~~~~~~~~~ND
:~~~~~~~~~::::::::::::::888$$I??++~:O:~?I=::::DDN=II777~$O8DDND?ZI+~877$$~~~~~~~~$~MD88DOD$Z?+?=~~~~~~~~~~~~~~~~~~~~:MDN
~~~~~~~:::::::::::::::::88O$I???+=++Z$77~~::::DDN+:?=I$~$88N8DNIII?+$I7+?:::~~~~~O?MDDDD8ZZ$7?++~~~~~~~~~~~~~~~~~~~~D7OM
~~~~~~~~::::::::::::::::8OO7??+=~===$777?~::::8DD+++I7$=Z88D8DD?7??I777778D8?~:~:8NMDD88O$Z7I?+~~~~~~~~~~~~~~~~~~~:DMMDN
~~~~~~~:::::::::::::::::OOO$+??=~~~~ONOOD8N:8N8DD+II$$7=Z888DDD?7I?II??$7DDZ8DDDDNDNDDD8ZZZI7+=+~~~~~~~~~~~~~~~~~~:D8NMN
~~~~~~~~::::::::::::::::ZOO7I+==+~~~ZO88ZOOD8D8DD+I77M$=OOONODD+7I7IZ?+OIZDDZZ8DD8DNDD88DZ$II===~::~~~~~~~~:~~~~~~~IMMMM
~~~~~~~~~~~~::::::::::::Z8Z7?+=~Z~~=ONOO88O8DND8D?I?IMZ~OOOD8DD?$I7?M??$?$ZZ8ZDD8DDMDDDDOZ$7IN+=~~:~~~~~~~~~~~~~~::DNMMM
~~~~~~~~~~~~~~~~:::::::=O8Z7?==~=~~+OD8D88DDNN8DD???I77=Z$8O8ONM$DI+I?+$IZZO88ZOODDNDDDOOO7I?I+=OO~~::~~~~~~~~~~~~~N7MDM
==~~~~+I=+=~~~~~~~~~~~:?OOZ7?+=~=~:=OD$888ODDD88NI?I?7I+ODDDDNM??NII??I+II7D8Z88DDDNDD8DOZ$7I?+~Z$+:~~:~I=~:~=8=8MMMMMMM
=====8O8O?$$~~$=$+~=:I$NOOZ7?+=8+~~=8D$OOOZO88O8N+?I?I?~OZZD88N$7?O?+?III$ZOD8ZZZ8DNDDD88O$7++==8MND+~ZD8D=:~=$?8MMMMND8
O88DMNMNNNZ887NMMNDZ88MNOZOI?==N=+~=88Z$ZOOODN8DD???I?I~ZZNMMMMO?$??+?+++$$8D8$ZZO8NDD888Z7I?I=~DMNMMMNMNNI~~IMMMMMMMMMM
8ODDMMMMMNMM8NMMMMMN8ODN88O$?+=+~~==OD7O8Z88DDOON?II??I~OONDNDN?MDI+I+++?778DZZO$ODND8D88O$I?+=:DMMMMMMMMMMNNNMMMMMMMMMM
DNDOMMMONNM7OMMMMMMM7777N8OI??+=~:~=OD$Z$7$Z888DD+?7+II~OODNNNNOMD?I?+=?I$ZONOOZ$88NNDD88OI??+=~DMMMMMMMMMMMMMMMMMMMMMMM
DNDNDNM8NMNNMODMNNDNNNNMO887?=7:::=~Z8Z$Z$8O8DODN??+?$$~NDMMMMO8MOI7I7+?7O88OOODOONNDDDD8$7I7==~NMMMMMMMMMMMMMMMMMMMMMMM
8DN88DDDDNDDONNNDNNDD88DDNDZOII??$Z7MMMDNMMMMMNNDI$7ND8ON88DDNNNO8DO8ZZZODMMMMMMNDMMMMMMNDZZ7ZZ77MMMMMMMMMNNMMMMMMMMMMMM
Z$$ZZOMOMDN778MMMMMNZI7ONND8OO7$$ODDMMMMMMDZZOOOOOOOOIDD8III778MNDZOOOOOO$O8DMMMMMMMMMMMNMD8OZZZOMMMMMMMMMMMMMMMMMMMMMMM
+++INMNMMMM++ZMMMMMZI+ONNND88O7$$$ZONMNMNNMMMMMMMN$O88MD$77777$DNDDODDDMDN8ND8NMMMMMMMNMDMDZOZ77ONMMMMMMMMMMOMMMMMMMMMMM
+++?NMONND87+INMMDO+==ONDDDZ7IZ+=++?8N888NNMMMMM?IM8DNOZ7777II7$8DN8ODDDDN8II7DD8DNNNNNDD8O$I??+DMMMMMMMMMM?++NMMMMMMMMM
++++7DNND8+++==?I=====78DD8Z7I??++=+DN888MMMMM=8ZINDNO$IIII??+???ONNDD8ON8D8DN888DDMNNNDDDZZ$7I+DMMNZ8NNNNZ++?MMMMMMMMMM
++++++88O7I?++++++++===?DD8Z77II???IDN8DDMM$=+8MO7NN8$$77I77777I778DDDNO$ND88D8DDDNNNNNDDDOZ$7??DDI+++I8NOI++$I7NMMMMM8D
++++++++++++++++++++++??DDDZ$77D?IIIDNDD8I=:N+8M?DNO8O$77777777$ZZODDN88ZDO88N88DDNMNNNDNDOZ77I?DDI++?+?+????7N$$MMMMMMM
++++++++++++++++++++++++DDDZZ7INII?IDND7?MD=M+DZDNO8OZ77$7$7777777ZZ8OD8ONONDNDD8NNMNNNNNN8OZ$I???????????????7??$NDDMMM
????????++++++++++++++++DDDOZ$7IIIII$7?D7D8?NINNN$OZ7III7I?II$$III777ZO87N8N8DN8NNDOMNNNND8O$$7I?I??I????I????????IMMMMM
??????????????????+?+?+?DND8Z$7I7I?I+MN8$NO7IONNZ$77???????+???I$$I??I$$ODOMZNNDNNNN88NNNDD8OZ7IIIIIIIIIIIIIIIIIIZZMNMMM
????????????????????????NND8Z$7O77I8ONNDON$7N8NOZ$7?????+?I7$7??????IIIZ7D8DMZNNNN88NMND8ND8ZD$IIIIIIIIII7IIIIIIIIIMMMMM
I?IIIII?????????????????DNN8Z$Z=7I7DONNNOI88MO$$$$$II7$I??II?IIIIIII77I7$Z8N8DMDNMNZNDNNMDNOO8$$7777777777777777IIINMNMM
IIIIIIIIIIIIIIIIIIIIIIIINNN$I$?7$77DONNZ8N8ONI888O$77777777777I7777777ZODDZ$DN$MOMNOMMMNNDNNNZZ77777777777777777777ZNNNM
IIIIIIIIIIIIIIIIIIIIIIIID777?D$ZZ$$O8$?ZNZZO$OOOO7I777ZZ8ZZ$$$Z$$$777I7777$O8$$OD8MOMMMMNDODMDNZ$$$$$$$$$$$$$$$7$$$$77DM
7777777777777777777777O$$I?D8DOOOZZOZ77ZN7N788DDZZZZ$$ZZZZOO8Z$$777III77ZZ8NI$$D$ZNOMMMMNDODD8DNMNZ$$$$$$$$$$$$$$$$$ZMNM
77777777777777777777O7$7INNDDD$OOOZ?N$7$N$$7$$$$I??I$$7??II??III??IIII7IIIII$8ZDZZOM8NMMMD8DD8OOMMNM8ZZZZZZZZZZZZZZZ$OMM
7$$$$$77777777777$7ZIZ77NNNDDDZ8O$7DM$$$O$$$$$$7I???IIII?IIIIIII?I7ZO$IIII77$OO7ZZO8NM$MMD8NDD88ZZNMMNMZZZZZZZZZZZZZZZZD
$$$$$$$$$$$$$$$O$O7Z7I$$MMNNDD7O77O8N$$7DOOZZ$Z7IIIII?I?IIIII7II?IIIII7II7I777$ZOOO8MMM8M88DDD8O8ONDDNNMM8OZOOOZOOZOZZDM
$$$$$$$$$$$$$$Z$7$$NDIZZNNNND877O8O8N$$$ZZZZZ$III$$$Z$IIIIIII77I7III7I777$7$$$ZO8OODMMNNMODNDD88DON8DODNNNNMOOOOOOOOOOOD
ZZZZZZZZZZZOZZ$7$ZZDDIZZZZDNDO7OODO8N8$$ZZZZZ7IIIIIIIIIIIII7ZZ$Z$II7I777I77777$$O8D8NM8MMM8NNDND8OMDDOOO8NMNMMDOOOOOOOOO
ZZZZZZZZOZOZ$$$ZZZ8NNIZZZZZO?8DZOOZM$ZOOOZ$$77I77$IIIIIIIIII777I77I7I77IOZZOO$$$ZZM7NND8MDMNO88888MDD8888ODMMDNMD8O88OOO
ZZOOZODOOZZ7ZZZZOODMOIOOOOO7ZDOZOOOMZOOOZZZZ7IIII7IIIIIIII77III777I777777777$$$$$Z$8D888MD8NMDD888MDN88888888MMNNNNZ8888
OOOOZZOZD7OOOOOOOO8NO7OOO7Z8OD8OOO8OZOOZOZZZ$ZZZZ$7I7I7II7I7I77777777777777777$$$ZZO8$8DM888DMMDDDMDDDDDDD88888MMMNNND88
ODZO8ZO7OOOOOOOOOO8D8IOO+D8O8D888Z$$ZOOOOZZ7II77I77I7ZZZOD$777I7777777$I777777777$$$Z8ZDM8DDDDNMNDM8DDDDDDDDDDDDDNMMMMMN
8Z7$$ZOOOOOOOOOOO88D8I$7O8888DDO8ZZZOOOZZ$7777I777II777777777$ZZZZZZ7I7$$7$$7$$$ZO8OD8DIM8DDDDDDMMMDDDDDDDDDDDDDDDDNNMNM
Z7Z?OOOOOOOOO8O8888O8I$Z88888DDOOOOOOOOZZ77777777$777777I777777777777777ZOZZOOZ7$$$$ZZODN8DDDDDDDMMDDDDDDDDDDDDDDDDDDNMM
"""

welcome = """\
 ▄█     █▄     ▄████████  ▄█        ▄████████  ▄██████▄    ▄▄▄▄███▄▄▄▄      ▄████████ 
███     ███   ███    ███ ███       ███    ███ ███    ███ ▄██▀▀▀███▀▀▀██▄   ███    ███ 
███     ███   ███    █▀  ███       ███    █▀  ███    ███ ███   ███   ███   ███    █▀  
███     ███  ▄███▄▄▄     ███       ███        ███    ███ ███   ███   ███  ▄███▄▄▄     
███     ███ ▀▀███▀▀▀     ███       ███        ███    ███ ███   ███   ███ ▀▀███▀▀▀     
███     ███   ███    █▄  ███       ███    █▄  ███    ███ ███   ███   ███   ███    █▄  
███ ▄█▄ ███   ███    ███ ███▌    ▄ ███    ███ ███    ███ ███   ███   ███   ███    ███ 
 ▀███▀███▀    ██████████ █████▄▄██ ████████▀   ▀██████▀   ▀█   ███   █▀    ██████████ 
                         ▀                                                            
"""
Welcome = """\
 ,ggg,      gg      ,gg                                                                   
dP""Y8a     88     ,8P           ,dPYb,                                                   
Yb, `88     88     d8'           IP'`Yb                                                   
 `"  88     88     88            I8  8I                                                   
     88     88     88            I8  8'                                                   
     88     88     88    ,ggg,   I8 dP    ,gggg,    ,ggggg,     ,ggg,,ggg,,ggg,    ,ggg,  
     88     88     88   i8" "8i  I8dP    dP"  "Yb  dP"  "Y8ggg ,8" "8P" "8P" "8,  i8" "8i 
     Y8    ,88,    8P   I8, ,8I  I8P    i8'       i8'    ,8I   I8   8I   8I   8I  I8, ,8I 
      Yb,,d8""8b,,dP    `YbadP' ,d8b,_ ,d8,_    _,d8,   ,d8'  ,dP   8I   8I   Yb, `YbadP' 
       "88"    "88"    888P"Y8888P'"Y88P""Y8888PPP"Y8888P"    8P'   8I   8I   `Y8888P"Y888
"""
to = """\
 ▄▀▀▀█▀▀▄  ▄▀▀▀▀▄  
█    █  ▐ █      █ 
▐   █     █      █ 
   █      ▀▄    ▄▀ 
 ▄▀         ▀▀▀▀   
█                  
▐                  
"""
To = """\
    .             
  .o8             
.o888oo  .ooooo.  
  888   d88' `88b 
  888   888   888 
  888 . 888   888 
  "888" `Y8bod8P'
"""

nimbh = """\
 ███▄    █  ██▓ ███▄ ▄███▓ ▄▄▄▄    ██░ ██ 
 ██ ▀█   █ ▓██▒▓██▒▀█▀ ██▒▓█████▄ ▓██░ ██▒
▓██  ▀█ ██▒▒██▒▓██    ▓██░▒██▒ ▄██▒██▀▀██░
▓██▒  ▐▌██▒░██░▒██    ▒██ ▒██░█▀  ░▓█ ░██ 
▒██░   ▓██░░██░▒██▒   ░██▒░▓█  ▀█▓░▓█▒░██▓
░ ▒░   ▒ ▒ ░▓  ░ ▒░   ░  ░░▒▓███▀▒ ▒ ░░▒░▒
░ ░░   ░ ▒░ ▒ ░░  ░      ░▒░▒   ░  ▒ ░▒░ ░
   ░   ░ ░  ▒ ░░      ░    ░    ░  ░  ░░ ░
         ░  ░         ░    ░       ░  ░  ░
                                ░         
"""
Nimbh = """\
     ...     ...        .                              ..                
  .=*8888n.."%888:     @88>                      . uW8"        .uef^"    
 X    ?8888f '8888     %8P      ..    .     :    `t888       :d88E       
 88x. '8888X  8888>     .     .888: x888  x888.   8888   .   `888E       
'8888k 8888X  '"*8h.  .@88u  ~`8888~'888X`?888f`  9888.z88N   888E .z8k  
 "8888 X888X .xH8    ''888E`   X888  888X '888>   9888  888E  888E~?888L 
   `8" X888!:888X      888E    X888  888X '888>   9888  888E  888E  888E 
  =~`  X888 X888X      888E    X888  888X '888>   9888  888E  888E  888E 
   :h. X8*` !888X      888E    X888  888X '888>   9888  888E  888E  888E 
  X888xX"   '8888..:   888&   "*88%""*88" '888!` .8888  888"  888E  888E 
:~`888f     '*888*"    R888"    `~    "    `"`    `%888*%"   m888N= 888> 
    ""        `"`       ""                           "`       `Y"   888  
                                                                   J88"  
                                                                   @%    
                                                                 :"      
                                                                                                          
"""
fullgreet = """\
 ,ggg,      gg      ,gg                                                                   
dP""Y8a     88     ,8P           ,dPYb,                                                   
Yb, `88     88     d8'           IP'`Yb                                                   
 `"  88     88     88            I8  8I                                                   
     88     88     88            I8  8'                                                   
     88     88     88    ,ggg,   I8 dP    ,gggg,    ,ggggg,     ,ggg,,ggg,,ggg,    ,ggg,  
     88     88     88   i8" "8i  I8dP    dP"  "Yb  dP"  "Y8ggg ,8" "8P" "8P" "8,  i8" "8i 
     Y8    ,88,    8P   I8, ,8I  I8P    i8'       i8'    ,8I   I8   8I   8I   8I  I8, ,8I 
      Yb,,d8""8b,,dP    `YbadP' ,d8b,_ ,d8,_    _,d8,   ,d8'  ,dP   8I   8I   Yb, `YbadP' 
       "88"    "88"    888P"Y8888P'"Y88P""Y8888PPP"Y8888P"    8P'   8I   8I   `Y8888P"Y888

    .            
  .o8            
.o888oo  .ooooo. 
  888   d88' `88b
  888   888   888
  888 . 888   888
  "888" `Y8bod8P'
     ...     ...        .                              ..               
  .=*8888n.."%888:     @88>                      . uW8"        .uef^"   
 X    ?8888f '8888     %8P      ..    .     :    `t888       :d88E      
 88x. '8888X  8888>     .     .888: x888  x888.   8888   .   `888E      
'8888k 8888X  '"*8h.  .@88u  ~`8888~'888X`?888f`  9888.z88N   888E .z8k 
 "8888 X888X .xH8    ''888E`   X888  888X '888>   9888  888E  888E~?888L
   `8" X888!:888X      888E    X888  888X '888>   9888  888E  888E  888E
  =~`  X888 X888X      888E    X888  888X '888>   9888  888E  888E  888E
   :h. X8*` !888X      888E    X888  888X '888>   9888  888E  888E  888E
  X888xX"   '8888..:   888&   "*88%""*88" '888!` .8888  888"  888E  888E
:~`888f     '*888*"    R888"    `~    "    `"`    `%888*%"   m888N= 888>
    ""        `"`       ""                           "`       `Y"   888 
                                                                   J88" 
                                                                   @%   
                                                                 :"     
"""
greet = """\
\    / _ | _ _  _ _  _ 
 \/\/ (/_|(_(_)| | |(/_
                       
_|_ _                  
 | (_)                 
                       
|\ |. _ _ |_ |_        
| \||| | ||_)| |   
"""

dead = """\
 __   __  _____  _     _      _______  ______ _______      ______  _______ _______ ______ 
   \\_/   |     | |     |      |_____| |_____/ |______      |     \\ |______ |_____| |     \\
    |    |_____| |_____|      |     | |    \\_ |______      |_____/ |______ |     | |_____/
"""


cinfo = """\
NIMBH
Copyright (c) 2016 James Burns. All rights reserved.
NIMBH is held under the Attribution-NonCommercial-ShareAlike (CC BY-NC-SA) License.
Version 0.1 Alpha
"""
info = """\
Remember: You may press Control+D or ALT+F4 at any time to exit.
ALT+ENTER toggles fullscreen, although doing this may distort formatting.
Formatting is designed best around a 1920x1080 fullscreen monitor.
Press ALT+TAB to switch in and out of the game.
"""
def maxSize(x):
    if x < 10:
        return 9
    if x < 100:
        return 99
    if x < 1000:
        return 999
    if x < 10000:
        return 9999
    else:
        return 99

def randomDigits(y):
       return ''.join(str(random.randint(0,9)) for x in range(y))


def randomChars(y):
       return ''.join(random.choice(string.ascii_letters) for x in range(y))

def isInt(c):
    try:
        int(c)
        return True
    except:
        return False


LF_FACESIZE = 32
STD_OUTPUT_HANDLE = -11

def nprint(s, x=0, c=" "):
    for line in s.splitlines():
        print(line.center(x, c), end="\r")

def replaceNumbers(s):
    return re.sub('\d', lambda m: str(random.randint(0,9)), s)

class COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

class CONSOLE_FONT_INFOEX(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_ulong),
                ("nFont", ctypes.c_ulong),
                ("dwFontSize", COORD),
                ("FontFamily", ctypes.c_uint),
                ("FontWeight", ctypes.c_uint),
                ("FaceName", ctypes.c_wchar * LF_FACESIZE)]


def printXY(x, y, text):
     sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (x, y, text))
     time.sleep(1)
     sys.stdout.flush()


def beep(sound):
    winsound.PlaySound('%s.wav' % sound, winsound.SND_FILENAME)


def blood(decay=15, dur=100, fast=True):
    sizex, sizey = get_terminal_size()
    #os.system("mode con: cols="+str(sizex)+ "lines="+str(sizey))
    positions = []
    text = "0"*sizex
    for i in range(sizex//2* + decay*2):
        positions.append(random.randint(0, sizex))
        if len(positions) >= sizex:
            break
    if 0 in positions:
        positions = [x for x in positions if x != 0]
#        positions.append(int(random.gauss(sizex//2, sizex//4)))
    for i in range(dur):
        if all(x == text[0] for x in text) and text[0] != "0":
            for i in range(sizey):
                start_time = time.time()
                print("")
                if time.time() - start_time < 0.008:
                    time.sleep(0.008 - (time.time() - start_time))
            break  # break function once it everything looks done
        #positions.append(random.randint(0, sizex))
        lenp = len(positions)
        #text = str(randomDigits(x))
        for index, j in enumerate(positions):
            if all(x == text[0] for x in text) and text[0] != "0":
                break
            found = False
            count = 0
            while found == False and fast == True and count < decay:
                count += 1
                if all(x == text[0] for x in text):
                    found = True
                    break
                pos = random.randint(0,sizex-1)
    #            print("pos:", pos)
                if text[pos].isdigit() == True:
    #                print("True!")
                    text = text[:pos] + ' ' + text[pos + 1:]
                    found == True
                    break  # Not sure why this look won't end without breaking
    #            else:
    #                print("False :(")
    #        print("break")
            #positions.append(random.randint(0, sizex))
            text = replaceNumbers(text)
            shift = random.randint(0,1)
            text = text[:j] + ' ' + text[j + 1:]
            if shift == 0 and j == 0:
                positions[index] += 1
            elif shift == 1 and j == lenp - 1:
                positions[index] -= 1
            else:
                if shift == 0:
                    positions[index] -= 1
                else:
                    positions[index] += 1
            print(Fore.RED, Style.DIM, text, end="\r")



def youdied(decay=15, dur=100, fast=True):
    sizex, sizey = get_terminal_size()
    #os.system("mode con: cols="+str(sizex)+ "lines="+str(sizey))
    positions = []
    text = "0"*sizex
    for i in range(sizex//2* + decay*2):
        positions.append(random.randint(0, sizex))
        if len(positions) >= sizex:
            break
    if 0 in positions:
        positions = [x for x in positions if x != 0]
#        positions.append(int(random.gauss(sizex//2, sizex//4)))
    for i in range(dur):
        if all(x == text[0] for x in text) and text[0] != "0":
            for i in range(sizey):
                start_time = time.time()
                print("")
                if time.time() - start_time < 0.01:
                    time.sleep(0.01 - (time.time() - start_time))
            break  # break function once it everything looks done
        #positions.append(random.randint(0, sizex))
        lenp = len(positions)
        #text = str(randomDigits(x))
        for index, j in enumerate(positions):
            if all(x == text[0] for x in text) and text[0] != "0":
                break
            found = False
            count = 0
            while found == False and fast == True and count < decay:
                count += 1
                if all(x == text[0] for x in text):
                    found = True
                    break
                pos = random.randint(0,sizex-1)
    #            print("pos:", pos)
                if text[pos].isdigit() == True:
    #                print("True!")
                    text = text[:pos] + ' ' + text[pos + 1:]
                    found == True
                    break  # Not sure why this look won't end without breaking
    #            else:
    #                print("False :(")
    #        print("break")
            #positions.append(random.randint(0, sizex))
            text = replaceNumbers(text)
            shift = random.randint(0,1)
            text = text[:j] + ' ' + text[j + 1:]
            if shift == 0 and j == 0:
                positions[index] += 1
            elif shift == 1 and j == lenp - 1:
                positions[index] -= 1
            else:
                if shift == 0:
                    positions[index] -= 1
                else:
                    positions[index] += 1
            print(Fore.RED, Style.DIM, text, end="\r")
    print(Style.BRIGHT)
    nprint(dead, sizex)
    for i in range(sizey//2-2):
        print("")
        time.sleep(0.03)
    print(Fore.WHITE, Style.DIM)
#    time.sleep(1.5)
    sys.stdout.write("\r")
    ret = input("Enter 'q' to quit, or anything else to return to the main menu.".center(sizex) + Fore.RED + Style.BRIGHT)
    return ret

def rain(dur=10**5):  # pretend you're upside down ;)
    sizex, sizey = get_terminal_size()
    os.system("mode con: cols="+str(sizex)+ "lines="+str(sizey))
    positions = []
    #bolt = x//2 + random.randint(-x//3, x//3)
    #boltf = bolt
    time1 = 250
    time2 = 491
    time3 = 599
    time4 = 759
    time5 = 956
    nextbolt = time5 + random.randint(5,sizex)
    bl1 = random.gauss(sizey//2, sizey//4)
    bl2 = random.gauss(sizey//2, sizey//4)
    bl3 = random.gauss(sizey//2, sizey//4)
    bl4 = random.gauss(sizey//2, sizey//4)
    bl5 = random.gauss(sizey//2, sizey//4)
    bln = random.gauss(sizey//2, sizey//4)
    fade = 0
    def lightning(bolt, text):
        boltf = bolt
        boltf += random.randint(-1,1)
        if boltf == bolt:
            text = text[:boltf] + '|' + text[boltf + 1:]
        elif boltf > bolt:
            text = text[:boltf] + '\\' + text[boltf + 1:]
        else:
            text = text[:boltf] + '/' + text[boltf + 1:]
        #p = str(Fore.BLUE, text[:bolt], Fore.YELLOW, text[bolt], Fore.BLUE, text[boltf + 1:])
        p = Fore.BLUE + text[:boltf] + Fore.YELLOW + Style.BRIGHT + text[boltf] + Fore.BLUE + Style.NORMAL + text[boltf + 1:]
        print(p, end="\r")
        return boltf
    for i in range(sizex*3):
        positions.append(random.randint(0, sizex))
    for i in range(dur):
        text = "o"*sizex
        #positions.append(random.randint(0, sizex))
        lenp = len(positions)
        #text = str(randomDigits(x))
        for index, j in enumerate(positions):
            shift = random.randint(0,1)
            text = text[:j] + ' ' + text[j + 1:]
            if shift == 0 and j == 0:
                positions[index] += 1
            elif shift == 1 and j == lenp - 1:
                positions[index] -= 1
            else:
                if shift == 0:
                    positions[index] -= 1
                else:
                    positions[index] += 1
        if i >= time1 and i < time1 + bl1:
            if i == time1:
                bolt1 = sizex//2 + random.randint(-sizex//3, sizex//3)
            bolt1 = lightning(bolt1, text)
        elif i >= time2 and i < time2 + bl2:
            if i == time2:
                bolt2 = sizex//2 + random.randint(-sizex//3, sizex//3)
            bolt2 = lightning(bolt2, text)
        elif i >= time3 and i < time3 + bl3:
            if i == time3:
                bolt3 = sizex//2 + random.randint(-sizex//3, sizex//3)
            bolt3 = lightning(bolt3, text)
        elif i >= time4 and i < time4 + bl4:
            if i == time4:
                bolt4 = sizex//2 + random.randint(-sizex//3, sizex//3)
            bolt4 = lightning(bolt4, text)
        elif i >= time5 and i < time5 + bl5:
            if i == time5:
                bolt5 = sizex//2 + random.randint(-sizex//3, sizex//3)
            bolt5 = lightning(bolt5, text)
        elif i >= nextbolt and i < nextbolt + bln:
            if i == nextbolt:
                boltn = sizex//2 + random.randint(-sizex//3, sizex//3)
            boltn = lightning(boltn, text)
        if i == nextbolt + (sizey)//2:
            nextbolt += sizey + fade + random.randint(1,sizex)
            bln = random.gauss(sizey//2, sizey//4)
            fade += 5
        else:
            print(Fore.BLUE, end="\r")
            print(text, end="\r")


def tendrils():
    sizex, sizey = get_terminal_size()
    os.system("mode con: cols="+str(sizex)+ "lines="+str(sizey))
    positions = []
    for i in range(sizey * 2):
        start_time = time.time()
        positions.append(random.randint(0, sizex))
        positions.append(random.randint(0, sizex))
        lenp = len(positions)
        text = " " * sizex
        for index, j in enumerate(positions):
            shift = random.randint(0,1)
            text = text[:j] + str(random.randint(0,9)) + text[j + 1:]
            if shift == 0 and j == 0:
                positions[index] += 1
            elif shift == 1 and j == lenp - 1:
                positions[index] -= 1
            else:
                if shift == 0:
                    positions[index] -= 1
                else:
                    positions[index] += 1
                
        print(text, end="\r")
        if time.time() - start_time < 0.01:
            time.sleep(0.01 - (time.time() - start_time))


def bloodText1(x, y):
    positions = []
    for i in range(int(x//2)):
        positions.append(random.randint(0, x))
    lenp = len(positions)
    for i in range(y):
        text = str(randomDigits(x))
        for index, j in enumerate(positions):
            shift = random.randint(0,1)
            text = text[:j] + ' ' + text[j + 1:]
            if shift == 0 and j == 0:
                positions[index] += 1
            elif shift == 1 and j == lenp - 1:
                positions[index] -= 1
            else:
                if shift == 0:
                    positions[index] -= 1
                else:
                    positions[index] += 1
                
        print(text, end="\r")


def intro():
    ctypes.windll.kernel32.SetConsoleTitleA("NIMBH")
    font = CONSOLE_FONT_INFOEX()
    font.cbSize = ctypes.sizeof(CONSOLE_FONT_INFOEX)
    font.nFont = 12
    font.dwFontSize.X = 12
    font.dwFontSize.Y = 12
    font.FontFamily = 54
    font.FontWeight = 400
    font.FaceName = "Lucida Console"

    handle1 = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    ctypes.windll.kernel32.SetCurrentConsoleFontEx(
        handle1, ctypes.c_long(False), ctypes.pointer(font))
    AltEnter()
    sizex, sizey = get_terminal_size()
    #mode con: cols=sizex lines=sizey
    #system("mode CON: COLS=",str(sizey))
    #bufsize = wintypes._COORD(sizex, sizey) # rows, columns
    #STDERR = -12
    #h = windll.kernel32.GetStdHandle(STDERR)
    #windll.kernel32.SetConsoleScreenBufferSize(h, bufsize)
    #subprocess.Popen(["mode", "con:", "cols=",str(sizex), "lines=",str(sizey)])
    #sys.stdout.write("\x1b[8;{rows};{cols}t".format(rows=32, cols=100))
    os.system("mode con: cols="+str(sizex)+ "lines="+str(sizey))
    #print("Terminal size:", get_terminal_size())
    #pause = input("Press enter to begin.\n")
    #clear()
    count = 0
    fullgreetsize = len(re.findall("\n", fullgreet))
    for i in range((sizey- 1)):
        print("| {0:<{1}} |".format("", sizex-4), end = "\r")
    for line in fullgreet.splitlines():
        count += 1
        print("| {0:<{1}} |".format(line.center(sizex-4), sizex-4), end = "\r")
        time.sleep(0.015)
    for i in range((sizey-fullgreetsize)//2):
        count += 1
        print("| {0:<{1}} |".format("", sizex-4), end = "\r")
        time.sleep(0.03)
    #tendrils()
    #clear()
    print(Fore.RED, Style.DIM, end="\r"),
    time.sleep(3)
    print("".center(sizex, "_"), end="\r")
    blood(40)
    clear()
    toPrint = replaceNumbers(fullgreet)
    print(Style.RESET_ALL),
    #print(Style.DIM),
    print(Style.DIM),
    for i in cinfo.splitlines():
        print(i.rjust(sizex))
    print(Fore.RED),
    print(Style.BRIGHT),
    #print(Back.WHITE)
    for i in range((sizey - 63)//2-3):
        print("")
    for i in toPrint.splitlines():
        print(i.center(sizex), end = "\r")
        sys.stdout.write('\r')
        sys.stdout.flush()
    for i in range((sizey - 63)//2-1):
        print("")
    print(Fore.BLUE)
    pause = input("Press enter to continue.\n")
    clear()
    for i in range((sizey)//2-6):
            print("")
    print(Fore.CYAN)
    print(Style.DIM),
    nprint(info, sizex)
    for i in range((sizey)//2-6):
        print("")
    pause = input(Fore.RED + "Press enter to begin.\n")


if __name__ == "__main__":
    intro()
    clear()
    youdied()
