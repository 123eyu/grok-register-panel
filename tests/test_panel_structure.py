# -*- coding: utf-8 -*-
from pathlib import Path
import re, sys
ROOT = Path(__file__).resolve().parents[1]

def test_workers_dom_ids_unique():
    mon = (ROOT / 'webui/monitor.py').read_text(encoding='utf-8')
    assert 'id="workers-input"' in mon
    assert 'id="workers-stats"' in mon
    assert not re.search(r'id="workers"', mon)

def test_no_cors_wildcard():
    mon = (ROOT / 'webui/monitor.py').read_text(encoding='utf-8')
    assert 'Access-Control-Allow-Origin", "*"' not in mon

def test_no_bind_all_fallback():
    mon = (ROOT / 'webui/monitor.py').read_text(encoding='utf-8')
    assert 'host = "0.0.0.0"' not in mon

def test_license_upstream():
    assert 'AaronL725' in (ROOT / 'LICENSE').read_text(encoding='utf-8')
    assert 'AaronL725' in (ROOT / 'NOTICE').read_text(encoding='utf-8')

def test_redact_proxy_shipped():
    sys.path.insert(0, str(ROOT))
    from webui.security_utils import redact_proxy
    secret = 'super-secret-pass-ZZ'
    out = redact_proxy(f'http://u:{secret}@10.0.0.1:8080')
    assert secret not in out

if __name__ == '__main__':
    test_workers_dom_ids_unique()
    test_no_cors_wildcard()
    test_no_bind_all_fallback()
    test_license_upstream()
    test_redact_proxy_shipped()
    print('OK structure')
