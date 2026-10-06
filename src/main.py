from io import TextIOWrapper
import os
import sys
import argparse
import time
from typing import List

from analyzer import json_analyzer
from dap_log import log
from match import MatchRule, FileInfo
from scan import scan

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog='dap',
        description='Digital Asset Pipeline - Scan target directories and build a manifest.'
    )
    parser.add_argument(
        '--config', '-c',
        required=True,
        help='Path to the `config.json` file.'
    )
    parser.add_argument(
        '--output', '-o',
        default='./manifest',
        help='Output manifest directory path (default: ./manifest).'
    )
    return parser.parse_args(argv)

def match_launcher(rules:List[MatchRule], file_list:TextIOWrapper, output_dir:str, eof_tag:str='__EOF__', max_fork_attempt:int=3)->None:
    eof_tag = eof_tag.strip()
    
    for rule in rules:
        pid = os.fork()
        if pid<0:
            log('MATCH', 'Error: os.fork() failed', type='warn')
            for t in range(max_fork_attempt-1):
                time.sleep(0.1)
                pid = os.fork()
                if pid >= 0:
                    break
                else:
                    log('MATCH', 'Error: os.fork() failed', type='warn' if t != max_fork_attempt-2 else 'error')
                

        if pid==0:  # subprocess, start matching
            while True:
                line = file_list.readline()
                if not line:
                    time.sleep(0.02)
                    continue
                if line.strip() == eof_tag:
                    break
                else:
                    try:
                        file = FileInfo(*line.rsplit(maxsplit=3))
                    except:
                        log('MATCH', 'Invalid line of FileInfo, skipping', type='warn')
                        continue
                    rule.match([file])
            rule.write(output_dir=output_dir)
            break
        else:
            continue

def main(args):
    if os.name != 'posix':
        log('LAUNCH', 'DAP only supports POSIX operating systems! ', type='error')
    if os.geteuid()!=0:
        log('LAUNCH', 'Running as non-root user. Access to certain files or directories may be denied.', type='warn')

    config_path:str = args.config
    output_path:str = args.output

    target_dirs, rules = json_analyzer(config_path)

    r, w = os.pipe
    pid = os.fork()
    if pid<0:
        log('LAUNCH', 'Error: os.fork() failed', type='error')
    if pid==0:
        os.close(r)
        writable = os.fdopen(w)
        for dir in target_dirs:
            scan(dir, writable=writable)
        writable.write('__EOF__')
    else:
        os.close(w)
        readable = os.fdopen(r)
        match_launcher(rules, readable, output_path, eof_tag='__EOF__')

    log('END', 'Operations completed successfully')

if __name__ == '__main__':
    args = parse_args()
    main(args)