# 3080 Brief｜Audience Heading Failure Fixture

## TLDR

> 分层判断改变了结果解释。  
> 下一步根据来源中的验证条件决定是否扩大范围。

![Synthetic visual](synthetic-board.svg)

| 问题 | 结论 | 为什么 |
| --- | --- | --- |
| 本质变化是什么？ | 从汇总判断转为分层判断。 | 不同分层的结果方向不同。 |
| 证据说明什么？ | 当前结果支持继续验证。 | 来源覆盖了当前样本和周期。 |
| 下一步做什么？ | 按验证条件继续检查。 | 当前证据存在适用边界。 |

> 来源：[Synthetic Source](https://example.invalid/source)

## 给 Leader 的决策建议

该标题必须被配置和 preflight 拦截。
