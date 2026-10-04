import json
from typing import List

import match
from dap_log import log


def json2rule(json_path:str)->List[match.MatchRule]:
    results = []
    try:
        with open(json_path, 'r') as f:
            rules = json.load(f)
        log('ANALYZE', 'Reading configuration file')
        assert isinstance(rules, list), 'Invalid configuration file. (wrong type)'
        for r in rules:
            assert isinstance(rules, dict), 'Invalid rule in configuration file. (wrong type)'
            try:
                cur_rule = match.MatchRule(**r)
                results.append(cur_rule)
                log('ANALYZE', f'Added rule {cur_rule.name} successfully')
            except:
                raise RuntimeError('Unexpected arguments in rule(s).')

        return rules
    except Exception as e:
        log('ANALYZE', f'Cannot analyze configration file: {e}', type='error')