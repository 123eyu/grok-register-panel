# Grok Register + Live Panel

批量注册 Grok 账号（Camoufox）+ Web 监控面板（启停 / 并发 / 黑名单 / 统计）。

> 仅供自动化流程研究、自有环境验证与个人学习。请遵守目标网站服务条款与当地法律。

## 包含什么

| 组件 | 入口 | 说明 |
|------|------|------|
| 注册机 GUI/CLI | `python grok_register_ttk.py` / CLI 模式 | 邮箱 OTP、资料、Turnstile、SSO→CPA |
| 编排器 | `python run_until_100.py` | 多轮 batch，风控满 N 暂停 + ASN 扩黑 |
| 单批 headless | `python run_batch_headless.py <count> <workers>` | Xvfb 无头批量 |
| **Web 面板** | `python webui/monitor.py` | 启动/停止、并发、再跑 N、黑名单、统计 |

## 快速开始

```bash
git clone <your-repo-url> grok-register
cd grok-register
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
camoufox fetch
cp config.example.json config.json
# 编辑 config.json：邮箱 API、proxy、cpa_auth_dir 等
```

### 1) 跑注册（CLI 并发示例）

```bash
# Linux 无头
xvfb-run -a python -u run_batch_headless.py 20 3

# 或编排到目标 CPA 数量（配合 monitor 的 add_count / workers）
python -u run_until_100.py
```

### 2) 开 Web 面板

```bash
export MONITOR_HOST=0.0.0.0   # 默认 127.0.0.1
export MONITOR_PORT=8787
export CPA_AUTH_DIR=./cpa_auth
python webui/monitor.py
# 浏览器打开 http://127.0.0.1:8787/
```

面板功能：

- **启动 / 停止** 编排或单批
- **并发 workers**、**batch 数量**、**再跑 N 个**
- **黑名单列表**、刷新；扩黑错误统计
- 成功/失败 KPI、Worker 分布、日志尾部

## 配置要点

见 `config.example.json`：

- `email_provider` + 对应 API Key（cloudflare / duckmail / yyds / …）
- `proxy`：HTTP 代理，出口建议住宅 IP
- `cpa_auth_dir` / `grok2api_auth_dir`：本地入库目录
- `register_workers`：并发浏览器数

环境变量：

| 变量 | 默认 | 说明 |
|------|------|------|
| `CPA_AUTH_DIR` | `./cpa_auth` | CPA auth 目录（编排统计 CPA 数） |
| `MONITOR_HOST` | `127.0.0.1` | 面板绑定地址 |
| `MONITOR_PORT` | `8787` | 面板端口 |

## 目录结构

```text
.
├── grok_register_ttk.py      # GUI + CLI 主程序
├── register_flow.py          # 注册页流程 / Turnstile
├── browser_session.py        # 浏览器会话 + 出口 ASN 黑名单
├── sso_to_auth_json.py       # SSO → OAuth / CPA
├── run_batch_headless.py     # 无头批量
├── run_until_100.py          # 编排器
├── webui/
│   ├── monitor.py            # Live 面板
│   └── blacklist_ops.py      # 黑名单读写/重置（可选）
├── email_providers/
├── config.example.json
└── requirements.txt
```

## 安全与发布注意

- **不要提交** `config.json`、`accounts/`、`cpa_auth/`、`proxies.txt`、真实 stickies
- 开源前自查密钥：`grep -R api_key --include='*.json' .`
- 黑名单 ASN 为出口质量过滤，非攻击能力

## License

MIT
