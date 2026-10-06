import sys
import time
from typing import Literal

mapping = {
    'normal':'INFO',
    'warn':'WARNING',
    'error':'ERROR'
}

def _log(process:str, info:str, type:Literal['normal', 'warn', 'error'] = 'normal'):
    cur_time = time.localtime()
    log_info = f'[{cur_time.tm_year}-{cur_time.tm_mon}-{cur_time.tm_mday} {cur_time.tm_hour}:{cur_time.tm_min}:{cur_time.tm_sec}]'+\
                f'[DAP {mapping[type]}][{process}] {info}'
    if type=='normal':
        print(log_info)
    elif type=='warn':
        print(f'\033[33m{log_info}\033[0m', file=sys.stderr)
    elif type=='error':
        print(f'\033[31m{log_info}\033[0m', file=sys.stderr)
        raise RuntimeError(info)

def _err_only(process:str, info:str, type:Literal['normal', 'warn', 'error'] = 'normal'):
    cur_time = time.localtime()
    log_info = f'[{cur_time.tm_year}-{cur_time.tm_mon}-{cur_time.tm_mday} {cur_time.tm_hour}:{cur_time.tm_min}:{cur_time.tm_sec}]'+\
                f'[DAP {mapping[type]}][{process}] {info}'
    if type=='error' or type=='warn':
        print(f'\033[31m{log_info}\033[0m', file=sys.stderr)
        raise RuntimeError(info)

DEBUG = False
log = _log if not DEBUG else _err_only