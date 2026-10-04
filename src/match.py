import asyncio
import os
import re
import stat as _stat
from typing import List
from subprocess import run
import pwd
import grp

from dap_log import log


class MatchRule:
    def __init__(self, fmt, user, group, perm, regex_p_file, regex_p_path, file_group_name) -> None:
        self.fmt, self.user, self.group, self.perm, self.regex_p_file, self.regex_p_dir = \
            fmt, user, group, perm, regex_p_file, regex_p_path
        self.name = file_group_name
        return


def _perm_str_to_list(perm: str) -> List[int]:
    # Keep only the last 9 permission characters.
    if len(perm) > 9:
        perm = perm[-9:]
    result = [0, 0, 0, 0]
    for i in range(3):
        cur_block = perm[i * 3:i * 3 + 3]
        if cur_block[0] == 'r':
            result[i + 1] += 4
        if cur_block[1] == 'w':
            result[i + 1] += 2
        if cur_block[2] == 'x':
            result[i + 1] += 1
        elif cur_block[2] in ('s', 'S', 't', 'T'):
            # Special permission bits: s/S = setuid/setgid, t/T = sticky.
            if i == 0 and cur_block[2] in ('s', 'S'):
                result[0] += 4
            elif i == 1 and cur_block[2] in ('s', 'S'):
                result[0] += 2
            elif i == 2 and cur_block[2] in ('t', 'T'):
                result[0] += 1
    return result


def _check_perm(file_perm: str, tgt_perm: List[int]) -> bool:
    file_perm_list = _perm_str_to_list(file_perm)
    if len(file_perm_list) < len(tgt_perm) and int(''.join(map(str, tgt_perm)))!=0:
        return False
    # Do not mutate the caller's list; build an aligned copy instead.
    tgt = list(tgt_perm)
    if len(file_perm_list) > len(tgt):
        tgt = [0] * (len(file_perm_list) - len(tgt)) + tgt
    for (f, t) in zip(file_perm_list, tgt):
        if f & t != t:
            return False
    return True


def _perm_to_rwx(mode: int) -> str:
    # Convert st_mode into a 9-char permission string like 'rwxr-xr-x',
    # compatible with special bits (s/S/t/T).
    perm = _stat.S_IMODE(mode)
    chars = []
    for i in range(3):
        bits = (perm >> (6 - i * 3)) & 0o7
        chars.append('r' if bits & 0o4 else '-')
        chars.append('w' if bits & 0o2 else '-')
        if bits & 0o1:
            chars.append('x')
        else:
            chars.append('-')
    s = ''.join(chars)
    # Overlay special bits: setuid / setgid / sticky.
    if perm & 0o4000:
        s = s[:2] + ('s' if s[2] == 'x' else 'S') + s[3:]
    if perm & 0o2000:
        s = s[:5] + ('s' if s[5] == 'x' else 'S') + s[6:]
    if perm & 0o1000:
        s = s[:8] + ('t' if s[8] == 'x' else 'T') + s[9:]
    return s


async def check_fmt(file_path: str, tgt_fmt: str) -> bool:
    ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    return ext == tgt_fmt.lower()


async def match(dir_path: str, rule:MatchRule) -> list:
    # print(f"[DEBUG] enter match, dir_path={dir_path}")   # ← 加这行
    file_list = []
    dir_list = []

    # Use os.scandir instead of parsing 'ls -la' output.
    with os.scandir(dir_path) as entries:
        for entry in entries:
            try:
                st = entry.stat(follow_symlinks=False)
            except OSError:
                continue
            # Build fields equivalent to the original layout:
            # 0=perm(str), 2=user, 3=group, -1=filename.
            perm_rwx = _perm_to_rwx(st.st_mode)

            try:
                user_name = pwd.getpwuid(st.st_uid).pw_name
            except KeyError:
                user_name = str(st.st_uid)

            try:
                group_name = grp.getgrgid(st.st_gid).gr_name
            except KeyError:
                group_name = str(st.st_gid)

            file_list.append([perm_rwx, st.st_nlink, user_name, group_name,
                            st.st_size, '-', '-', '-', '-', entry.name])

            if entry.is_dir(follow_symlinks=False):
                dir_list.append(file_list[-1])
                file_list.pop()
        # print(f"[DEBUG] after scandir, file_list={len(file_list)}, dir_list={len(dir_list)}")  # ← 加这行

    # Filter by user / group.
    usr_grp = [rule.user, rule.group]
    if usr_grp != [None, None] and usr_grp != ['', '']:
        file_list = [f for f in file_list if f[2:4] == usr_grp]

    # Filter by perm / file regex / path regex.
    # Use synchronous checks instead of threads sharing the same list.
    perm = list(map(int, list(str(rule.perm))))
    filtered = []
    for file in file_list:
        if (not _check_perm(''.join(file[0]), perm)) \
                or re.search(rule.regex_p_file, file[-1]) is None \
                or re.search(rule.regex_p_dir, dir_path) is None:
            continue
        filtered.append(file)
    file_list = filtered
    # print(f"[DEBUG] after user/perm/regex filter, file_list={len(file_list)}")   # ← 加这行

    # Format check: keep asyncio as before, but process in order to avoid index mismatch.
    async_tasks = [asyncio.create_task(check_fmt(os.path.join(dir_path, file[-1]), rule.fmt))
                   for file in file_list]
    fmt_results = await asyncio.gather(*async_tasks)
    file_list = [file for file, ok in zip(file_list, fmt_results) if ok]

    for file in file_list:
        log('MATCH', f'Mapped file {file[-1]} to {rule.name}.')

    file_list = [os.path.join(dir_path, file[-1]) for file in file_list]
    # Recurse into subdirectories and collect results in order.
    for dp in dir_list:
        file_list += await match(os.path.join(dir_path, dp[-1]), rule)
    
    return file_list


if __name__ == '__main__':
    dir_path = '/home/ubuntu'
    rule = MatchRule(
        fmt='pdf',
        user='ubuntu', group='ubuntu',
        perm=644,
        regex_p_file='.*', regex_p_path='.*',
        file_group_name='test'
    )
    asyncio.run(match(dir_path, rule))

__all__ = [MatchRule, match]