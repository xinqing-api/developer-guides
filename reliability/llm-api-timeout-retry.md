# 大模型 API 超时与重试：一份可直接复用的工程指南

大模型 API 偶尔超时并不稀奇。真正危险的不是一次失败，而是没有边界的重试：请求越积越多，延迟和费用一起失控，最终把短暂故障放大成系统故障。

这篇指南给出一套适合大多数 AI 应用的起点：**明确超时、只重试临时故障、指数退避、加入随机抖动、设置总次数上限。**

## 先判断：哪些错误值得重试？

通常可以重试：

- 网络连接被重置或临时中断；
- 请求超时；
- `408 Request Timeout`；
- `429 Too Many Requests`；
- `500`、`502`、`503`、`504`。

通常不应自动重试：

- `400`：请求格式或参数错误；
- `401`：密钥无效或缺失；
- `403`：没有访问权限；
- `404`：资源或接口地址不存在；
- 内容安全、输入长度等明确的业务拒绝。

一个简单原则：**重试只应该处理“稍后再试可能成功”的故障。**

## 可直接复用的 Node.js 示例

下面的实现只使用 Node.js 内置能力，适用于 Node.js 18 及以上版本。

```js
const RETRYABLE_STATUS = new Set([408, 429, 500, 502, 503, 504]);

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function backoffWithJitter(attempt, baseMs = 500, capMs = 8000) {
  const exponential = Math.min(capMs, baseMs * 2 ** attempt);
  return Math.floor(Math.random() * exponential);
}

async function requestWithRetry(url, options = {}) {
  const {
    maxRetries = 3,
    timeoutMs = 30_000,
    ...fetchOptions
  } = options;

  let lastError;

  for (let attempt = 0; attempt <= maxRetries; attempt += 1) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
      });

      if (response.ok) {
        return response;
      }

      if (!RETRYABLE_STATUS.has(response.status)) {
        throw new Error(`Non-retryable HTTP ${response.status}`);
      }

      lastError = new Error(`Retryable HTTP ${response.status}`);
    } catch (error) {
      lastError = error;

      const isTimeout = error.name === "AbortError";
      const isNetworkError = error instanceof TypeError;

      if (!isTimeout && !isNetworkError) {
        throw error;
      }
    } finally {
      clearTimeout(timeoutId);
    }

    if (attempt === maxRetries) {
      break;
    }

    const delayMs = backoffWithJitter(attempt);
    await sleep(delayMs);
  }

  throw new Error(
    `Request failed after ${maxRetries + 1} attempts`,
    { cause: lastError },
  );
}

async function createCompletion(messages) {
  const response = await requestWithRetry(
    process.env.API_BASE_URL + "/v1/chat/completions",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.API_KEY}`,
      },
      body: JSON.stringify({
        model: process.env.MODEL_NAME,
        messages,
      }),
      timeoutMs: 30_000,
      maxRetries: 3,
    },
  );

  return response.json();
}
```

示例中的地址、密钥和模型都来自环境变量，避免把真实凭证或内部地址写进仓库。

## 为什么要加入随机抖动？

如果一千个客户端在同一时刻收到 `429`，又都在固定的 1 秒后重试，服务端会再次迎来一千个请求。这叫“惊群”。

指数退避让每次等待逐步变长；随机抖动让客户端分散在不同时间重试。两者结合，可以显著降低同步冲击。

本文采用 Full Jitter：

```text
等待时间 = random(0, min(上限, 基础时间 × 2^重试次数))
```

## 别忽略服务端的提示

如果响应包含 `Retry-After`，应优先遵守服务端给出的等待时间，并为本地等待设置合理上限。生产实现还可以记录限流相关响应头，帮助判断是账户配额、并发限制还是短时流量尖峰。

## 流式请求要更谨慎

普通请求在收到响应前失败，通常可以整体重试。流式请求一旦已经输出部分内容，直接重试可能造成：

- 界面出现重复文本；
- 重复执行工具调用；
- 重复写入数据库或触发外部操作；
- 同一次用户请求产生多次费用。

因此，流式处理中应记录“是否已经向下游交付内容”。开始交付后，默认不要自动整体重试；需要恢复时，应设计明确的续传或去重机制。

## 写操作需要幂等性

聊天生成看似是读取，实际应用往往还会创建任务、扣减额度或写入记录。对可能产生副作用的请求：

- 为一次业务操作生成稳定的请求 ID；
- 重试时复用同一个 ID；
- 服务端保存并识别已经处理过的 ID；
- 不要把“客户端没收到响应”误判成“服务端没有执行”。

## 生产环境至少记录这些字段

- 请求 ID 与追踪 ID；
- 尝试次数；
- 每次等待时间；
- HTTP 状态码或网络错误类型；
- 首次请求和最终结束时间；
- 是否发生超时；
- 最终使用的模型；
- Token 用量与估算费用；
- 是否已经向用户输出部分结果。

日志中不要记录完整 API Key，也应谨慎处理用户输入和模型输出中的敏感信息。

## 上线前检查清单

- [ ] 每次请求都有超时；
- [ ] 重试次数有硬上限；
- [ ] 只重试临时故障；
- [ ] 使用指数退避和随机抖动；
- [ ] 支持并优先遵守 `Retry-After`；
- [ ] 流式输出开始后不会盲目整体重试；
- [ ] 有副作用的操作具备幂等或去重能力；
- [ ] 指标能够区分首次成功、重试成功和最终失败；
- [ ] 日志不包含密钥和不必要的敏感内容。

## 推荐的默认起点

没有历史数据时，可以从以下配置开始：

- 单次超时：30 秒；
- 最大重试：3 次；
- 基础退避：500 毫秒；
- 退避上限：8 秒；
- 使用 Full Jitter；
- 超过总延迟预算后立即失败。

这些不是永远正确的固定值。上线后应根据模型延迟、用户场景、限流策略和错误分布持续调整。

## 最后一句

> 好的重试不是“直到成功”，而是“在明确的时间和成本预算内，提高临时故障的恢复概率”。


