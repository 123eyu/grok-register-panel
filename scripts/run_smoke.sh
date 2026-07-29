#!/usr/bin/env bash
# 本地单号冒烟：环境检查 → 输入 start 后注册 1 个
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate

echo "=== 1) 代理探测 ==="
PROXY=$(python3 -c "import json; print(json.load(open('config.json')).get('proxy',''))")
echo "config.proxy=$PROXY"
if [[ -n "$PROXY" ]]; then
  ip=$(curl -s -m 8 -x "$PROXY" https://api.ipify.org || true)
  code=$(curl -s -m 12 -x "$PROXY" "https://accounts.x.ai/sign-up" -o /tmp/grok_smoke_xai.html -w "%{http_code}" \
    -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36" || true)
  body=$(head -c 80 /tmp/grok_smoke_xai.html 2>/dev/null | tr '\n' ' ' || true)
  echo "exit_ip=$ip  xai_http=$code  body=${body:0:80}"
  if [[ "$code" == "403" ]] && grep -qi "abusive\|just a moment\|cloudflare\|blocked" /tmp/grok_smoke_xai.html 2>/dev/null; then
    echo "[!] accounts.x.ai 仍被拦截。请先换干净代理出口，再改 config.json 的 proxy 后重试。"
    echo "    当前 Camoufox 有头模式也过不了 hard-block（已验证）。"
    exit 2
  fi
fi

echo "=== 2) 邮箱建号探测 ==="
python3 - <<'PY'
import json
from grok_register_ttk import load_config, config, http_post
load_config()
from email_providers.cloudflare import create_temp_address
addr, jwt = create_temp_address(
    http_post,
    config["cloudflare_api_base"],
    accounts_path=config["cloudflare_path_accounts"],
    domain="example.com",
    api_key=config["cloudflare_api_key"],
    auth_mode=config["cloudflare_auth_mode"],
    name="smokeprecheck",
)
print(f"email_ok {addr} jwt_len={len(jwt)}")
PY

echo "=== 3) 启动 CLI（register_count=1）==="
echo "start" | python grok_register_ttk.py start
echo "=== 4) 结果 ==="
ls -la accounts/ cpa_auth/ grok2api_auth/ 2>/dev/null || true
echo "--- accounts ---"
tail -n 3 accounts/*.txt 2>/dev/null || true
echo "--- cpa_auth ---"
ls cpa_auth/ 2>/dev/null || true
