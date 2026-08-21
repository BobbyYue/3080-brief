# 3080 Brief

**30-second judgment, 80% in one picture**

[![CI](https://github.com/BobbyYue/3080-brief/actions/workflows/ci.yml/badge.svg)](https://github.com/BobbyYue/3080-brief/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent_Skill-open_format-0B7A55.svg)](https://agentskills.io/)

[English](README.md) · [快速开始](#快速开始) · [完整案例](docs/examples/claude-code-session-value.md) · [最新版本](https://github.com/BobbyYue/3080-brief/releases/latest)

一个开源 **AI Agent Skill**：把源文档重建为读者视角的决策简报，包括 30 秒判断、一张可追溯的主线图、一个关键问题表和一条清晰故事线。它不修改源文档；宿主支持时，可新建飞书/Lark、Markdown、Word/docx 或自包含 HTML 格式的简报。

<p align="center"><strong>① 左侧是原文章 → ② 右侧是 3080 Brief 产出</strong></p>

[![Claude 原文章与 3080 Brief 产出的对照](docs/assets/claude-code-comparison.png)](docs/examples/claude-code-session-value.md)

> **真实产出案例：** [Anthropic 的 5 分钟文章](https://claude.com/blog/maximizing-the-value-of-your-claude-code-sessions)把 token 定价、提示缓存、上下文增长、会话长度和子代理分散在多个章节中。3080 Brief 在保留原文作为事实来源的前提下，把它整理成一个操作判断、一套五步流程和一份明确的排查优先级。由于源文章为英文，案例按源语言输出。 [查看完整案例 →](docs/examples/claude-code-session-value.md)

## 你会得到什么

| 读者的问题 | 3080 Brief 的产出 |
| --- | --- |
| 最重要的判断是什么？ | **一句话**：一个核心判断，加 1–3 行证据、行动或边界 |
| 信息之间是什么关系？ | **一张图**：覆盖至少 80% 的价值加权、非附录主张 |
| 读完最可能追问什么？ | **一个表**：回答关键问题 |
| 原文逻辑到底是什么？ | **一条线**：按读者视角重新组织原文故事线 |

源文档保持不变，Skill 会另外创建一份新简报。

## 快速开始

### 1. 安装完整 Skill 目录

把下面这段话发给任何支持 Agent Skills 的 Agent：

```text
请安装 https://github.com/BobbyYue/3080-brief 中的 Agent Skill，
使用完整子目录 skills/3080-brief，并注册到你的正式 Skill 目录。
随后检查我目标输出所需的依赖；如有缺失，请一次性展示完整清单和影响，并只询问一次是否安装。
```

也可以手动安装：

```bash
git clone --depth 1 https://github.com/BobbyYue/3080-brief.git
cp -R ./3080-brief/skills/3080-brief "<YOUR_AGENT_SKILLS_DIR>/3080-brief"
```

必须复制完整目录，不能只复制 `SKILL.md`。如果 Agent 文档有要求，安装后重新加载或重启。

### 2. 提供源文档和明确要求

```text
请使用 $3080-brief，把这份文档新建为读者视角决策简报。
保持源文档不变，输出格式跟随输入格式。
最终返回生成结果链接或文件，并说明验收状态。
```

也可以自然语言触发：

```text
请基于这份方案新建一份简报：30 秒看懂结论，
一张图覆盖核心逻辑，再用一个表回答读者最关心的问题。
```

## 为什么使用

- **读者视角：** 围绕读者需要理解、信任、判断和行动的信息重建内容。
- **提炼核心价值：** 从背景噪音中抽出关键结论、证据、风险和下一步。
- **理清故事线：** 把零散或技术化的原文组织成一条连贯论证。
- **表达具体：** 需要说明价值的标题、章节名和开场结论直接写清对象和原文支持的结果，不用方法名或空泛价值词代替。
- **用图表达关系：** 飞书和 HTML 共用一套明确构图、可见证据数值、主题和语义色。HTML 额外内置离线图表/图解素材库和可审计的原生 SVG 回退，避免一张图退化为“方框加文字”。
- **可靠交付：** 保持源文不变、重要主张可追溯、格式跟随，并验收最终产物。

## 安装方式

<details>
<summary><strong>让 Agent 安装并检查依赖</strong></summary>

如果 Agent 支持从 GitHub 安装 Skill，可以发送完整指令：

```text
请安装 https://github.com/BobbyYue/3080-brief 中的 Agent Skill，
使用完整子目录 skills/3080-brief，并注册到你的正式 Skill 目录。
随后检查我目标输出所需的依赖，向我一次性展示全部缺失项、来源、版本和安装影响，
并只询问一次是否全部安装或启用。如果我同意，请处理清单中的所有项目，不要逐项重复申请。
飞书输出还需要把 beautiful-feishu-whiteboard 作为独立 Skill 注册，并启用宿主可实际执行的
lark-doc 和 lark-whiteboard 工作流。仅加载 Skill 说明不代表能力可用。
如果我拒绝，保留 3080-brief，但保持对应输出路径为阻断状态。
```

</details>

<details>
<summary><strong>Windows PowerShell</strong></summary>

```powershell
git clone --depth 1 https://github.com/BobbyYue/3080-brief.git
Copy-Item -Recurse ./3080-brief/skills/3080-brief "<YOUR_AGENT_SKILLS_DIR>/3080-brief"
```

</details>

<details>
<summary><strong>Web 或桌面客户端导入</strong></summary>

下载[最新版本](https://github.com/BobbyYue/3080-brief/releases/latest)并解压，通过客户端的 Skill 导入入口上传 `skills/3080-brief`。除非客户端明确支持仓库子路径，否则不要上传仓库根目录。

</details>

`3080-brief` 遵循开放的 [Agent Skills](https://agentskills.io/) 文件夹格式。不同宿主的安装命令、注册目录、重新加载方式、程序执行和文档能力不同；可参考官方 [Client Showcase](https://agentskills.io/clients)。

## 兼容性与执行保障

| 宿主状态 | 能说明什么 |
| --- | --- |
| 可安装 | Agent 能发现完整 Skill 目录，尚不能说明产出质量。 |
| 核心流程已验证 | Agent 能运行基于原文证据的流程，以及 Markdown/docx、自包含 HTML 的离线检查。 |
| 飞书流程已验证 | 当前运行真实完成文档读写、原生可编辑白板插入与查询、线上预览和最终验收。 |

生产流程为：冻结非附录来源证据 → 预检 → 渲染完整初稿 → 独立执行一张图盲读 → HTML 额外执行几何检查与整页视觉复述 → Primary Blind Reader 复述，按条件升级 Technical/Decision Reader → 三位 Reviewer 独立审稿并全部通过 → 重新读取源文档和产物 → 验收。确认收到或执行计划不算最终交付。

已经审阅过的候选版本发生变化后，Skill 会分别计算来源、正文、核心视觉、桌面布局和移动端布局的哈希，只重跑真正受影响的检查和审阅，保留未受影响的 PASS 结果，并在分层回执验证通过后立即停止。来源或正文变化仍会重启完整审阅；只修复移动端布局不会。

Standard 和 Strict 的首个候选版本必须完成视觉复述、Blind Reader Replay 和三方独立审稿；后续修改执行经过验证的分层复核计划。只有用户明确要求 Fast 时，才允许以披露限制的自检代替独立盲读/审稿，并跳过全文 Blind Reader Replay。

<details>
<summary><strong>飞书/Lark 依赖与安装行为</strong></summary>

核心离线校验只需要 Python 3.9+，不依赖第三方 Python 包。自包含 HTML 只使用 Skill 内置字体和渲染素材，不加载外部脚本、字体或样式。飞书/Lark 输出额外需要：

- 可实际执行的 `lark-doc` 读写和 `lark-whiteboard` 查询/更新工作流；
- Node.js 20+；
- `@larksuite/cli` / `lark-cli` 1.0.60+；
- 隔离工具缓存中的 `@larksuite/whiteboard-cli` 0.2.11；
- [`beautiful-feishu-whiteboard`](https://github.com/zarazhangrui/beautiful-feishu-whiteboard) 1.1.1+；
- 飞书/Lark 登录和必要的文档权限。

缺失飞书依赖只阻断该输出路径。Skill 会先展示来源、版本、已知影响和拟执行动作，再申请用户许可；不会静默安装软件或授予账号权限。

</details>

## 开发验证

运行完整离线测试：

```bash
bash skills/3080-brief/scripts/self_test.sh
```

单独检查运行上下文和飞书依赖：

```bash
python3 skills/3080-brief/scripts/check_context_budget.py skills/3080-brief --json
python3 skills/3080-brief/scripts/check_dependencies.py --mode feishu --json
```

仓库结构：

```text
skills/3080-brief/   可安装的 Agent Skill
docs/examples/       带源链接的真实案例
docs/assets/         README 和社交预览图
.github/workflows/   离线 CI
```

## 隐私与边界

- 不要在 Issue 或案例中公开文档 token、租户标识、凭据或内部指标。
- 只有真正运行了独立审阅或盲读复述时，才会对外声明其完成。
- 带来源的案例只代表其标注获取日期时可验证的产品行为与证据。
- 本项目不使用 with-skill/without-skill 基准宣传。

贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)，安全问题见 [SECURITY.md](SECURITY.md)，许可证为 [MIT](LICENSE)。
