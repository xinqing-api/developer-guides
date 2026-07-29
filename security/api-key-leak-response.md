# API Key 泄露应急清单：前 60 分钟应该做什么

API Key 出现在 Git 历史、日志、截图或客户端代码中时，应把它视为已经泄露。删除最新版本中的那一行代码，不能使旧 Key 重新可信。

## 0—15 分钟：止损

- [ ] 记录发现时间、密钥用途、仓库与暴露位置。
- [ ] 撤销旧 Key，或按服务连续性要求完成紧急轮换。
- [ ] 更新生产、测试、CI/CD、定时任务和第三方自动化中的合法配置。
- [ ] 验证新 Key 可用、旧 Key 已不可用。
- [ ] 临时收紧预算、速率、权限和来源限制。

## 15—60 分钟：确认影响

- [ ] 检查泄露窗口内的用量、费用、来源、接口和错误率。
- [ ] 查找非工作时间调用、陌生来源、异常模型或配额突增。
- [ ] 保存告警、审计记录和关键时间线。
- [ ] 无法判断影响范围时，联系对应服务商支持。

## 当天：清理暴露面

- [ ] 清理 Git 历史中的 Secret，并评估历史重写的协作影响。
- [ ] 检查分支、标签、Pull Request、Fork 和本地克隆。
- [ ] 检查 Issue、评论、CI 日志、制品、容器镜像、截图和录屏。
- [ ] 通知协作者清理仍包含 Secret 的副本。

## 防止再次发生

- [ ] 密钥只由后端持有，不嵌入浏览器或移动客户端。
- [ ] 本地使用未提交的环境文件；生产使用 Secret Manager。
- [ ] 一人一 Key、一环境一 Key，并采用最小权限。
- [ ] 配置 `.gitignore`、pre-commit 检查与仓库 Secret Scanning。
- [ ] 对异常用量、费用和密钥检测配置可执行告警。
- [ ] 明确撤销、部署、审计、清理和复盘的责任人。

## `.gitignore` 最小示例

```gitignore
.env
.env.*
!.env.example
```

## 安全的配置示例

```js
const apiKey = process.env.API_KEY;

if (!apiKey) {
  throw new Error("API_KEY is not configured");
}
```

`.env.example` 只能包含变量名和虚拟值：

```dotenv
API_KEY=replace-with-your-own-key
```

## 核心原则

> Revoke first, investigate second, clean history third.

轮换解决“泄露者还能不能使用”，清理历史解决“后来的人还能不能看见”。两者都重要，但顺序不能反。

## 参考资料

- [GitHub：从仓库移除敏感数据](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [GitHub：Secret scanning](https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning)
- [OWASP：Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [OpenAI：API Key 安全最佳实践](https://help.openai.com/en/articles/5112595-best-practices-for-api)
