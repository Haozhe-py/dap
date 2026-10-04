import asyncio
import os
import argparse
import sys
from typing import List
import xml.etree.ElementTree as ET

from analyzer import json2rule
from match import MatchRule, match
from dap_log import log


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog='dap',
        description='Digital Asset Pipeline - scan target directories and build a manifest.',
    )
    parser.add_argument(
        '--config', '-c',
        required=True,
        help='Path to the config.json file (index rules).',
    )
    parser.add_argument(
        '--target-dirs', '-t',
        required=True,
        nargs='+',
        help='One or more directories to scan.',
    )
    parser.add_argument(
        '--output', '-o',
        default='manifest.xml',
        help='Output manifest file path (default: manifest.xml).',
    )
    return parser.parse_args(argv)

def add_group(parent_node, file_list:List[str], rule:MatchRule):
    name=rule.name

    group = ET.SubElement(parent_node, 'group')
    group.set('name', name)

    files = ET.SubElement(group, 'files')
    for file in file_list:
        node = ET.SubElement(files, 'file')
        node.set('path', file)

    rule_node = ET.SubElement(group, 'rule')
    for attr in ('fmt', 'user', 'group', 'perm', 'regex_p_file', 'regex_p_path'):
        node = ET.SubElement(rule_node, attr)
        node.text = rule.__getattribute__(attr)

async def main(args):
    if os.name != 'posix':
        log('LAUNCH', 'DAP only supports POSIX operating systems! ', type='error')
    if os.geteuid()!=0:
        log('LAUNCH', 'Running as non-root user. Access to certain files or directories may be denied.')

    config_path:str  = args.config
    target_dirs:list = args.target_dirs
    output_path:str  = args.output

    rules:list = json2rule(config_path)
    root = ET.Element('manifest', version='1.0')

    async def scan_rule(rule:MatchRule):
        result = []
        for dir in target_dirs:
            result += await match(dir, rule=rule)
        return result
    async_tasks = [asyncio.create_task(scan_rule(rule)) for rule in rules]
    for task in async_tasks:
        add_group(root, await task)

    tree = ET.ElementTree(root)
    ET.indent(tree, space='  ')

    log('WRITE', f'Writing to {output_path}')
    try:
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
    except:
        log('WRITE', f'Failed writing to {output_path}', type='warn')
        raise


if __name__ == '__main__':
    args = parse_args(sys.argv)
    exit(asyncio.run(main(args)))