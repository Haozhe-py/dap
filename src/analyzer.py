import json
from typing import List, Tuple

from dap_log import log
import match

def json_analyzer(json_path:str)->Tuple[List[str], List[match.MatchRule]]:
    tar_dirs, results = [], []
    try:
        with open(json_path, 'r') as f:
            config = json.load(f)
        log('ANALYZE', 'Reading configuration file')
        if isinstance(config, list):
            raise TypeError('The format of configration file has changed. The old one is no longer supported. ')
        
        assert isinstance(config, dict), f'Invalid configration file. (wrong type, expected `dict`, got {type(config).__name__})'

        tar_dirs = config.get('target_dirs', None)
        rules = config.get('rules', None)

        assert isinstance(tar_dirs, list) and (isinstance(rules, list) or rules is None), 'Expected key `target_dirs` and `rules` not found or invalid in configuration file.'

        if rules:
            for r in rules:
                assert isinstance(r, dict), f'Invalid rule in configuration file. (wrong type: {type(r).__name__})'
                try:
                    cur_rule = match.MatchRule(**r)
                    results.append(cur_rule)
                    log('ANALYZE', f'Added rule {cur_rule.name} successfully')
                except:
                    raise RuntimeError('Unexpected arguments in rule(s).')
        else:
            results = match.DEFAULT_RULES
            log('ANALYZE', 'Rules undefined in configuration. Using default settings')

        return tar_dirs, results

    except Exception as e:
        log('ANALYZE', f'Cannot analyze configration file: {e}', type='error')