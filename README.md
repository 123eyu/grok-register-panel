<div align="center">

# Grok Register + Live Panel

Based on [AaronL725/grok-register](https://github.com/AaronL725/grok-register) (MIT).

批量注册 Grok 账号（Camoufox）+ Web 监控面板  
启停 / 并发 / ASN 黑名单 / 1h·3h·12h 成功率

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)
![Stars](https://img.shields.io/github/stars/lij768423-svg/grok-register-panel?style=flat)

**仓库：** https://github.com/lij768423-svg/grok-register-panel

</div>

---

> **声明：** 仅供自动化流程研究、自有环境联调与个人学习。请遵守 xAI / 邮箱 / 代理服务商条款与当地法律，勿用于未授权批量滥用。

## 功能一览

| 能力 | 说明 |
|------|------|
| 注册全链路 | 邮箱 OTP → 资料页 → Turnstile → SSO → Device / OAuth → 写入 CPA / Grok2API |
| 多邮箱后端 | Cloudflare Worker 邮、DuckMail、YYDS、MailNest、CloudMail 等 |
| 反检测浏览器 | [Camoufox](https://camoufox.com/)（Gecko 层指纹） |
| 出口预检 | 启动前解析出口 IP / ASN，命中黑名单直接换口 |
| 风控早停 | `botFlagSource=1` + `policy=deny` 时跳过后续 OAuth，避免无效重试 |
| 编排器 | 多轮 batch、风控满 N 暂停、ASN 自动扩黑 |
| **Live 面板** | 启停、并发、再跑 N、黑名单、时段成功率、日志尾部 |

## 架构示意

```text
┌─────────────────┐     HTTP proxy      ┌──────────────────┐
│  Camoufox 注册机 │ ──────────────────► │ 本地代理 mixed 口 │
│  (多 worker)     │   127.0.0.1:79xx    │ (可选链式 dialer) │
└────────┬────────┘                     └────────┬─────────┘
         │                                        │
         │ SSO / Device Flow                      ▼
         ▼                                 住宅出口 / 其它出口
   cpa_auth/ · grok2api_auth/
         │
         ▼
┌─────────────────┐
│ webui/monitor   │  读 log/register_results.jsonl · CPA 目录
│ :8787 Live 面板 │  启停 run_until_100 / run_batch_headless
└─────────────────┘
```

说明：**注册机本身只配置一层 HTTP 代理 URL**。若需要「先节点再家宽」等链式出口，在代理客户端（如 mihomo `dialer-proxy`）配置，对注册机透明。

## 快速开始

### 环境

- Python 3.10+
- Linux 无头建议带 Xvfb；macOS 可本机 GUI/有头
- 能访问注册页、临时邮箱 API、`auth.x.ai` 的网络

### 安装

```bash
git clone https://github.com/lij768423-svg/grok-register-panel.git
cd grok-register-panel

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
camoufox fetch                     # 必须：下载浏览器引擎（约数百 MB）

cp config.example.json config.json
# 编辑 config.json：邮箱、proxy、cpa_auth_dir 等
```

> `pip install` 只装 Python 依赖；**不执行 `camoufox fetch` 无法启动浏览器**。

### 配置（`config.json`）

| 字段 | 说明 |
|------|------|
| `email_provider` | `cloudflare` / `duckmail` / `yyds` / `mailnest` / … |
| `defaultDomains` | 临时邮域名（如二级 CF 域） |
| `cloudflare_*` / `duckmail_*` 等 | 对应邮箱 API |
| `proxy` | 默认 HTTP 代理，如 `http://127.0.0.1:7890` |
| `proxies.txt` | 可选；多行代理，多 worker 轮换端口 |
| `register_workers` | 并发浏览器数（建议先 2～3） |
| `register_count` | 单次目标数量 |
| `cpa_auto_add` | 是否 SSO→OAuth 并写入 auth |
| `cpa_auth_dir` | 本地 CPA 目录（`xai-*.json`） |
| `grok2api_auth_dir` | Grok2API 风格 auth 目录 |
| `cpa_remote_url` / `cpa_management_key` | 远程 CPA Management API（可选） |

环境变量：

| 变量 | 默认 | 说明 |
|------|------|------|
| `CPA_AUTH_DIR` | `./cpa_auth` | 编排器统计 CPA 数量用 |
| `MONITOR_HOST` | `127.0.0.1` | 面板绑定地址 |
| `MONITOR_PORT` | `8787` | 面板端口 |
| `BATCH_LOG` | 自动发现最新 `log/batch*.log` | 面板跟踪的日志 |

### 跑起来

**A. Web 面板（推荐）**

```bash
export MONITOR_HOST=0.0.0.0    # 仅本机可省略
export MONITOR_PORT=8787
export CPA_AUTH_DIR=./cpa_auth

python webui/monitor.py
# 浏览器打开 http://127.0.0.1:8787/
```

面板上可设：模式（Orch / 单批）、workers、batch 数量、**再跑 N 个**、风控满 N 暂停 → 点启动。

**B. 命令行单批（无头 Linux）**

```bash
xvfb-run -a python -u run_batch_headless.py 20 3
#                        数量↑        并发↑
```

**C. 编排器**

```bash
# 由面板写入 log/monitor_control.json（workers / add_count / risk_pause …）
python -u run_until_100.py
```

**D. GUI**

```bash
python grok_register_ttk.py
```

## Live 面板说明

### 控制

| 控件 | 作用 |
|------|------|
| 模式 Orch | 跑 `run_until_100.py` 多轮直到目标 CPA |
| 模式 单批 | 只跑一轮 `run_batch_headless` |
| workers | 并发浏览器 |
| batch 数量 | 单批账号数上限相关 |
| **再跑 N 个** | 从**当前** CPA 再注册 N 个（目标已满时点启动不会秒退） |
| 风控满 N 暂停 | 本轮注册风控达到 N 后停 batch 并分析 ASN |

### 时段成功率

基于 `log/register_results.jsonl`：

```text
成功率 = ok / (ok + fail + risk) × 100%
窗口：近 1 小时 / 3 小时 / 12 小时
```

### 黑名单

- 下号前解析出口 ASN，命中则换 sticky / 代理口  
- 编排器在风控累计到阈值后，对「几乎只有失败」的 ASN 扩黑  
- 面板可 **刷新列表**；若实现了重置：回到基线熔断（如常见大户 ASN）  

## 工程实践备忘（非教程承诺）

以下为社区常见踩坑方向，**环境差异大，仅供参考**：

1. 邮箱：二级域名临时邮往往比批发一级域 / 大盘 Outlook·Google 更省事  
2. 出口：质量与冷却窗口影响大；同一出口短时间打太满容易抬失败率  
3. 风控字段：服务端 deny 后宜尽早结束 OAuth 路径  
4. 并发建议从 2～3 起跳，过高易空页、Turnstile 卡住、代理打满  
5. 「资料填写失败」有时是资料页人机未过，不一定是姓名密码写不进  
6. 链式代理在客户端配，不在注册机 Python 里写死  

## 目录结构

```text
.
├── grok_register_ttk.py       # GUI + CLI 主程序
├── register_flow.py           # 注册页流程 / Turnstile
├── browser_session.py         # 会话、出口探测、ASN 黑名单
├── sso_to_auth_json.py        # SSO → OAuth / 写 CPA
├── camoufox_adapter.py
├── connectivity.py
├── run_batch_headless.py      # 无头批量
├── run_until_100.py           # 编排器
├── webui/
│   ├── monitor.py             # Live 面板 HTTP 服务
│   └── blacklist_ops.py       # 黑名单读写 / 重置
├── email_providers/
├── scripts/                   # xvfb 辅助脚本
├── config.example.json
├── proxies.example.txt
├── requirements.txt
└── DEPLOYMENT.md
```

## 常见问题

**Q: 点启动立刻结束？**  
A: CPA 已达旧目标。面板填大 **再跑 N 个** 再启动；编排器用 `add_count` 抬目标。

**Q: 全是「无法解析出口 IP」？**  
A: 代理挂了 / 流量耗尽 / dialer 下游失败。先 `curl -x http://127.0.0.1:端口 https://httpbin.org/ip` 探活。

**Q: 邮箱 API 401？**  
A: 与代理无关，检查 `config.json` 里对应 provider 的 key / auth_mode。

**Q: Windows？**  
A: 主要在 macOS 与无界面 Linux 验证；Windows 需自备显示/依赖，欢迎 PR。

**Q: 面板和真实进程不一致？**  
A: 看 `log/orch100-stdout.log` 与最新 `log/batch-*.log`；欢迎提 issue / PR。

## 安全

- **不要提交** `config.json`、`accounts/`、`cpa_auth/`、`proxies.txt`、真实 stickies  
- `.gitignore` 已忽略上述路径  
- 开源前自查：`grep -R api_key --include='*.json' .`

## License

[MIT](LICENSE)

## 致谢

- [Camoufox](https://camoufox.com/)
- [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) 等下游生态
- 社区里分享风控字段与工程经验的各位

---

Star 鼓励一下 → https://github.com/lij768423-svg/grok-register-panel


## Panel security

```bash
export MONITOR_TOKEN='long-random-secret'
export MONITOR_HOST=127.0.0.1   # do not use 0.0.0.0 fallback
python webui/monitor.py
# browser: localStorage.setItem('MONITOR_TOKEN', 'long-random-secret')
```

Write APIs (`/api/start`, `/api/stop`, `/api/control`, …) require
`Authorization: Bearer <MONITOR_TOKEN>`. Raw log tails are off unless
`PANEL_INCLUDE_TAIL=1`.
