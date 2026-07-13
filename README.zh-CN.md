# 3080 Brief

**30-second judgment, 80% in one picture**

[![CI](https://github.com/BobbyYue/3080-brief/actions/workflows/ci.yml/badge.svg)](https://github.com/BobbyYue/3080-brief/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

把源文档重建为“30 秒形成判断、一张图理解主线”的可追溯决策简报。

[English](README.md)

`3080-brief` 不修改源文档，而是新建一份读者视角简报。开篇严格包含三个内容单元：

1. 一句话：首句只承载一个核心判断，其下可用 1–3 行补充证据、下一步或适用边界；
2. 一张图：覆盖至少 80% 的价值加权、非附录主张；
3. 一个表：回答读者阅读时最想追问的关键问题。

![3080 Brief 合成演示图](docs/assets/synthetic-brief.svg)

上图只使用合成评测数据，不包含真实业务信息。

## 为什么使用

- 来源可追溯：数字、结论、风险和建议必须能回到原文，否则明确标记为推断或原文未提供。
- 读者视角：围绕读者需要理解、信任、判断和行动的信息重建叙事。
- 格式匹配：飞书输入默认新建飞书文档，Word 输入默认新建 `.docx`，Markdown 输入默认新建 Markdown。
- 图不是装饰：使用价值加权 claim ledger 校验一张图的覆盖率；飞书画板保持可编辑。
- 有发布门禁：包含确定性预检、三个独立审阅角色和盲读者复述。
- 默认加载轻量：正常运行只加载 `SKILL.md`（当前 11.4KB），细则只在进入对应分支时读取。

## 安装

可以直接让 Codex 从本仓库的 `skills/3080-brief` 路径安装该 skill。

也可以使用 Codex 自带安装器：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo BobbyYue/3080-brief \
  --path skills/3080-brief
```

安装后重启 Codex，使新 skill 完成注册。

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

缺少这些依赖只会阻断飞书路径。skill 会展示准确来源、版本、安装目录、联网/文件影响和命令，并向用户申请明确许可，不会静默安装。

## 验证

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
