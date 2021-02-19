import time
import sys
import os
import import threading
import platform
from keymap import *
from common import Output, thread_refresh


MAX_KEYLOGGER_BUF = 1024

if platform.system() == 'Windos':
    import pywin32
