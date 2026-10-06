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

MAX_BATCH_SIZE = 10000

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

def match_launcher(rules: List[MatchRule], file_list: TextIOWrapper,
                   output_dir: str, eof_tag: str = '__EOF__',
                   max_fork_attempt: int = 3) -> None:
    log('LAUNCH', 'Starting to match files')
    eof_tag = eof_tag.strip()
    os.makedirs(output_dir, exist_ok=True)

    round_idx = 0
    reached_eof = False
    while True:
        # --- Step 1: parent reads whatever is currently available ---
        batch = []
        bsz = 0
        while True:
            line = file_list.readline()
            if not line:
                # Pipe is empty for now. If we already have lines, break
                # out of this inner loop to process this partial batch.
                # Otherwise keep waiting for the writer.
                if batch:
                    break
                time.sleep(0.02)
                continue
            if line.strip() == eof_tag:
                reached_eof = True
                break
            batch.append(line)
            bsz += 1
            if bsz >= MAX_BATCH_SIZE:
                break

        # --- Step 2: fork one child per rule, each handles this batch ---
        pids = []
        for rule in rules:
            pid = os.fork()
            if pid < 0:
                log('MATCH', 'Error: os.fork() failed', type='warn')
                for t in range(max_fork_attempt - 1):
                    time.sleep(0.1)
                    pid = os.fork()
                    if pid >= 0:
                        break
                    else:
                        log('MATCH', 'Error: os.fork() failed',
                            type='warn' if t != max_fork_attempt - 2 else 'error')

            if pid == 0:
                # Child: process this batch, append to a per-rule batch file.
                files = []
                for line in batch:
                    try:
                        file = FileInfo(*line.rsplit(maxsplit=3))
                        files.append(file)
                    except Exception:
                        log('MATCH', 'Invalid line of FileInfo, skipping', type='warn')
                        continue
                rule.match(files)
                rule.write(output_dir=output_dir)
                os._exit(0)
            else:
                pids.append(pid)

        # --- Step 3: parent waits for this round ---
        for pid in pids:
            try:
                log('WAIT', f'Waiting PID {pid}')
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass

        round_idx += 1
        log('MATCH', f'Round {round_idx} done, batch size={len(batch)}')

        if reached_eof:
            break

def main(args):
    if os.name != 'posix':
        log('LAUNCH', 'DAP only supports POSIX operating systems! ', type='error')
    if os.geteuid()!=0:
        log('LAUNCH', 'Running as non-root user. Access to certain files or directories may be denied.', type='warn')

    config_path:str = args.config
    output_path:str = args.output

    target_dirs, rules = json_analyzer(config_path)

    r, w = os.pipe()
    pid = os.fork()
    if pid<0:
        log('LAUNCH', 'Error: os.fork() failed', type='error')
    if pid==0:
        os.close(r)
        writable = os.fdopen(w, 'w', encoding='utf-8')
        file_count = 0
        for dir in target_dirs:
            file_count += scan(dir, writable=writable)
        writable.write('__EOF__')
        writable.flush()
        writable.close()
        log('SCAN', f'Scan completed, got {file_count} files')
        os._exit(0)
    else:
        os.close(w)
        readable = os.fdopen(r, 'r', encoding='utf-8')
        match_launcher(rules, readable, output_path, eof_tag='__EOF__')
        while True:
            try:
                pid, status = os.wait()
                log('WAIT', f"Subprocess {pid} done, status={status}")
            except ChildProcessError:
                break

    log('END', 'Operations completed successfully')

if __name__ == '__main__':
    args = parse_args()
    main(args)