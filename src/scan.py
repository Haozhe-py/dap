import grp
from io import TextIOWrapper
import os
import pwd

from dap_log import log

def scan(dir_path:str, writable:TextIOWrapper)->None:
    log('SCAN', f'Scanning {dir_path}')
    
    dir_list = []
    file_count = 0

    with os.scandir(dir_path) as entries:
        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                dir_list.append(os.path.join(dir_path, entry.name))
                continue

            try:
                st = entry.stat(follow_symlinks=False)
            except OSError:
                continue

            perm = f'{st.st_mode & 0o7777:04o}'

            try:
                user_name = pwd.getpwuid(st.st_uid).pw_name
            except KeyError:
                user_name = str(st.st_uid)

            try:
                group_name = grp.getgrgid(st.st_gid).gr_name
            except KeyError:
                group_name = str(st.st_gid)

            writable.write(f'{os.path.join(dir_path, entry.name)} {perm} {user_name} {group_name}\n')
            file_count += 1

    log('SCAN', f'Got {file_count} files and {len(dir_list)} directories in {dir_path}')

    for dir in dir_list:
        scan(dir, writable)
