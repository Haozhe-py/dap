import re
import os
from typing import List, Union
from dataclasses import dataclass
import xml.etree.ElementTree as ET

from dap_log import log

def _check_perm(file_perm: str, tgt_perm: List[int]) -> bool:
    file_perm_list = list(map(int, file_perm))
    if len(file_perm_list) < len(tgt_perm) and int(''.join(map(str, tgt_perm)))!=0:
        return False

    tgt = list(tgt_perm)
    if len(file_perm_list) > len(tgt):
        tgt = [0] * (len(file_perm_list) - len(tgt)) + tgt
    for (f, t) in zip(file_perm_list, tgt):
        if f & t != t:
            return False
    return True

@dataclass
class FileInfo:
    file_path:str
    perm:str
    user:str
    group:str

class MatchRule:
    def __init__(
        self, 
        fmt:Union[str, List[str]],
        user:str, 
        group:str, 
        perm:str, 
        regex_p_file:str, 
        regex_p_path:str, 
        file_group_name:str
    ) -> None:
        self.fmt, self.user, self.group, self.perm, self.regex_p_file, self.regex_p_dir = \
            fmt, user.strip(), group.strip(), list(map(int, str(perm))), regex_p_file, regex_p_path
        self.name = file_group_name

        if isinstance(self.fmt, str):
            self.fmt = [self.fmt.lower().strip()]
        elif isinstance(self.fmt, list) or isinstance(self.fmt, tuple):
            self.fmt = [m.lower().strip() for m in self.fmt]

        self.xml = ET.Element('manifest', version='1.0')
        self.xmlgroup = ET.SubElement(self.xml, 'group')
        self.xmlgroup.set('name', self.name)
        self.xmlfiles = ET.SubElement(self.xmlgroup, 'files')

        self.file_count:int = 0

    def match(self, files:List[FileInfo])->None:
        # Filter by user / group
        if not self.user and self.group:
            files = [f for f in files if f.group==self.group]
        elif not self.group and self.user:
            files = [f for f in files if f.user==self.user]
        elif self.group and self.user:
            files = [f for f in files if f.user==self.user and f.group == self.group]

        # Format check
        if self.fmt:
            files = [f for f in files if 
                     os.path.splitext(f.file_path)[1]
                     .lower()
                     .lstrip('.') in \
                     self.fmt
                     ]

        # Filter by perm / file regex / path regex
        files = [f for f in files 
                 if _check_perm(f.perm, self.perm)
                 and re.search(self.regex_p_file, os.path.split(f.file_path)[-1])
                 and re.search(self.regex_p_dir, os.path.split(f.file_path)[0])
                ]

        self.file_count += len(files)
        log(f'Mapped {len(files)} file(s) to {self.name}')
        for file in files:
            et = ET.SubElement(self.xmlfiles, 'file')
            et.text = file.file_path

    def write(self, output_dir:str, encoding:str='utf-8', xml_declaration:bool=True)->None:
        if self.file_count==0:
            return

        tree = ET.ElementTree(self.xml)
        ET.indent(tree, space='    ')

        output_path = os.path.join(output_dir, self.name)
        log('WRITE', f'Writing to {output_path}')
        try:
            tree.write(output_path, encoding=encoding, xml_declaration=xml_declaration)
            log('WRITE', f'File {output_path} generated successfully')
        except:
            log('WRITE', f'Failed writing to {output_path}', type='warn')
            raise

DEFAULT_RULES = [
    MatchRule(
        fmt=fmt, 
        user='', 
        group='', 
        perm='0000', 
        regex_p_file='.*', 
        regex_p_path='.*', 
        file_group_name=name
    ) for (fmt, name) in (
        (('doc', 'docx', 'wps', 'rtf'), '文字文稿'),
        (('ppt', 'pptx'), '演示文稿'),
        (('xls', 'xlsx', 'csv', 'et'), '电子表格'),
        (('py', 'h', 'cpp', 'cs', 'ts', 'js', 'java', 'c', 'go', 'php', 'rb', 'rs', 'swift'), '源代码'),
        (('jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'webp', 'svg'), '图像'),
        (('mp4', 'avi', 'mkv', 'mov', 'flv', 'wmv'), '视频'),
        (('mp3', 'wav', 'flac', 'aac', 'ogg'), '音频'),
        (('zip', 'rar', '7z', 'tar', 'gz'), '压缩包'),
        (('pdf'), 'PDF文档'),
        (('txt', 'md'), '文本文件'),
        (('exe', 'bat', 'sh', 'cmd'), '可执行文件或脚本'),
        (('iso', 'img'), '光盘镜像'),
        (('db', 'sql', 'mdb', 'sqlite'), '数据库文件'),
        (('apk', 'ipa'), '移动应用'),
        (('psd', 'ai', 'indd'), '设计文件'),
        (('epub', 'mobi'), '电子书'),
        (('log'), '日志文件'),
        (('cfg', 'ini', 'conf', 'json', 'xml', 'yaml', 'yml'), '配置文件'),
        (('torrent'), '种子文件'),
        (('vmdk', 'vdi', 'vhd'), '虚拟机磁盘镜像'),
        (('bak', 'old', 'tmp'), '备份或临时文件'),
    )
]

__all__ = [FileInfo, MatchRule, DEFAULT_RULES]