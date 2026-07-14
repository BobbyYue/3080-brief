# 3080 Brief

**30-second judgment, 80% in one picture**

[![CI](https://github.com/BobbyYue/3080-brief/actions/workflows/ci.yml/badge.svg)](https://github.com/BobbyYue/3080-brief/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

把源文档重建为“30 秒形成判断、一张图理解主线”的可追溯决策简报。

[English](README.md)

`3080-brief` 不修改源文档，而是新建一份读者视角简报。产出围绕四个读者价值单元组织：

1. 一句话：首句只承载一个核心判断，其下可用 1–3 行补充证据、下一步或适用边界；
2. 一条清晰的故事线：帮你理清原文逻辑；
3. 一张图：覆盖至少 80% 的价值加权、非附录主张；
4. 一个表：回答读者阅读时最想追问的关键问题。

## 为什么使用

- 读者视角：围绕读者需要理解、信任、判断和行动的信息重建叙事。
- 提炼核心价值：从背景噪音和实现细节中提取关键结论、证据、风险与下一步。
- 理清故事线：把零散、专业或技术化的原文逻辑组织成一条连贯、扫读即可理解的论证主线。
- 快速形成理解：用 30 秒判断、一张主线图和关键问题表，帮助读者迅速抓住重点。
- 可靠交付：来源可追溯、源文不改、格式跟随，并通过确定性校验与审阅门禁保证质量。

## 安装

`3080-brief` 遵循开放的 [Agent Skills](https://agentskills.io/) 文件夹格式，可用于任何支持该格式的 Agent。不同 Agent 的安装命令、Skill 目录和重新加载方式并不相同；具体产品说明可查看官方 [Client Showcase](https://agentskills.io/clients)。

### 方式一：直接让 Agent 安装

如果你的 Agent 支持从 GitHub 安装 Skill，可以向它发送：

```text
请安装 https://github.com/BobbyYue/3080-brief 中的 Agent Skill，
使用完整子目录 skills/3080-brief，并注册到你的正式 Skill 目录。
随后运行飞书依赖检查，向我一次性展示全部缺失依赖及安装影响，并只询问一次是否全部安装。
如果我同意，请安装清单中的所有项目，不要逐项重复申请；其中 beautiful-feishu-whiteboard
必须作为独立 Skill 注册。如果我拒绝，保留 3080-brief，但保持飞书输出为阻断状态。
```

### 方式二：手动安装完整目录

```bash
git clone --depth 1 https://github.com/BobbyYue/3080-brief.git
cp -R ./3080-brief/skills/3080-brief "<YOUR_AGENT_SKILLS_DIR>/3080-brief"
```

Windows PowerShell：

```powershell
git clone --depth 1 https://github.com/BobbyYue/3080-brief.git
Copy-Item -Recurse ./3080-brief/skills/3080-brief "<YOUR_AGENT_SKILLS_DIR>/3080-brief"
```

将 `<YOUR_AGENT_SKILLS_DIR>` 替换成该 Agent 文档规定的用户级或项目级 Skill 目录。必须复制完整的 `skills/3080-brief`，不能只复制 `SKILL.md`，因为运行还需要 `scripts/`、`references/`、`config/` 和 `evals/`。如果产品文档要求，安装后重新加载或重启 Agent。

### 方式三：在 Web 或桌面客户端上传

下载[最新 Release](https://github.com/BobbyYue/3080-brief/releases/latest)并解压，通过客户端的 Skill 导入入口上传 `skills/3080-brief`。除非客户端明确支持仓库子路径，否则不要直接上传整个仓库根目录。

无论使用哪种安装方式，Agent 都应在宣告飞书能力可用前运行依赖检查，并通过一次捆绑审批处理全部缺失依赖。

### 验证安装

确认安装后的 Skill 根目录包含 `SKILL.md`，然后发送：

```text
请使用 $3080-brief，把这份文档新建为读者视角决策简报。
```

如果某个 Agent 尚未原生支持 Agent Skills，可以把完整 Skill 目录作为项目上下文提供给它，并要求其遵循 `SKILL.md`。核心指令仍可使用，但自动发现、按需加载资源、执行脚本和依赖审批能力取决于宿主 Agent。

## 触发样例

显式调用：

```text
请使用 $3080-brief，把这份文档新建为读者视角决策简报。
保持源文档不变，输出格式跟随输入格式。
```

自然语言调用：

```text
请基于这份方案新建一份读者视角总结：30 秒看懂结论，
一张图覆盖核心信息，再用一个表回答读者最关心的问题。
```

仅要求原地修改源文档、普通摘要、或只做画板美化时不应触发。

## 依赖

核心离线校验只依赖 Python 3.9+，不需要第三方 Python 包。

飞书输出额外要求：

- Node.js 20+；
- `@larksuite/cli` / `lark-cli` 1.0.60+；
- 隔离工具缓存中的 `@larksuite/whiteboard-cli` 必须为 0.2.11；
- [`beautiful-feishu-whiteboard`](https://github.com/zarazhangrui/beautiful-feishu-whiteboard) 1.1.1+；
- 飞书账号认证与必要的文档权限。

缺少这些依赖只会阻断飞书路径。skill 会展示准确来源、版本、已知的联网/文件影响，以及审批命令或宿主原生注册请求，并向用户申请明确许可，不会静默安装。

安装阶段的依赖检查会生成一个审批包，覆盖清单中的全部飞书缺失依赖。用户明确同意一次，即授权执行所有已展示的 CLI 命令，并把 [`beautiful-feishu-whiteboard`](https://github.com/zarazhangrui/beautiful-feishu-whiteboard) 作为独立 Skill 注册；不能再逐项重复申请。用户拒绝时，保留核心 Skill，并保持飞书输出阻断。

`3080-brief` 不根据脚本执行目录猜测 Skill 注册目录，因为托管 Agent 可能从一次性临时仓库运行安装脚本。如果宿主没有提供已验证的注册目录，应使用当前 Agent 自带的安装器或导入入口。文件复制成功只会标记为“等待运行时复检”，不会标记为 `PASS`；重新加载 Agent 并在正式运行环境复检通过后才能继续。如果宿主明确提供持久注册目录，可设置 `BRIEF3080_SKILL_INSTALL_ROOT`。

如果缺少 Node.js 且没有已知的平台安装命令，或需要进行飞书登录、权限授权，仍须单独确认；一次捆绑审批不能覆盖未展示的系统命令或账号授权影响。

## 开发验证

运行完整离线测试：

```bash
bash skills/3080-brief/scripts/self_test.sh
```

单独检查能力唯一归属与运行上下文预算：

```bash
python3 skills/3080-brief/scripts/check_context_budget.py skills/3080-brief --json
```

只检查飞书依赖状态，不执行安装：

```bash
python3 skills/3080-brief/scripts/check_dependencies.py --mode feishu --json
```

## 隐私与边界

- 不要在 Issue、示例或截图中提交文档 token、租户标识、凭据或真实内部指标。
- 依赖安装许可不等于飞书认证许可。
- 只有真正运行了独立审阅和盲读复述时，才会对外声明其完成。
- 本项目不包含 with-skill / without-skill 基准宣传。

贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)，安全问题请按 [SECURITY.md](SECURITY.md) 私下报告。

## 许可证

[MIT](LICENSE)
