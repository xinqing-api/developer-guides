# 01｜从零构造 RAG：整体架构与可运行项目骨架

很多 RAG 教程从“调用模型”开始，结果一换文档、一改模型或数据量增大，项目就难以维护。本期先不接大模型，先把数据流、目录边界和向量数据库运行起来。

完成后，你将拥有：

- 一个可持久化的本地 Qdrant 服务；
- 一个隔离的 Python 环境；
- 一个能验证 Qdrant 连接的脚本；
- 一套后续可以逐步扩展的目录结构。

## 一、先理解完整数据流

RAG 分为两条链路。

### 入库链路

```text
原始文件 -> 解析 -> 清洗 -> Chunk -> Embedding -> 向量数据库
```

它的任务是把“文档”转换成可检索的知识单元。这里最容易被忽略的是稳定 ID、元数据和幂等更新。

### 查询链路

```text
用户问题 -> Query Embedding -> 召回 -> 过滤/重排 -> 上下文 -> LLM -> 答案与引用
```

检索不到正确材料时，换更强的生成模型通常也解决不了问题。因此要分别观测“召回是否正确”和“答案是否正确”。

## 二、准备目录

```text
rag-starter/
├─ compose.yaml
├─ requirements.txt
├─ healthcheck.py
├─ .gitignore
├─ data/               # 原始文档，后续使用
├─ storage/            # Qdrant 数据，不提交 Git
└─ src/
   ├─ ingest/          # 解析、清洗、切分、入库
   ├─ retrieval/       # 检索、过滤、重排
   ├─ generation/      # Prompt 与答案生成
   └─ evaluation/      # 检索和回答评测
```

本期可运行文件已经放在 [`01-starter`](01-starter/) 目录。

## 三、启动 Qdrant

进入示例目录：

```bash
cd rag/01-starter
docker compose up -d
docker compose ps
```

打开两个地址验证服务：

- REST API：<http://localhost:6333>
- Dashboard：<http://localhost:6333/dashboard>

示例只把端口绑定到 `127.0.0.1`，避免开发环境直接暴露到局域网或公网。Qdrant 默认配置没有启用认证，生产环境不能照搬。

## 四、建立 Python 环境

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux：

```bash
source .venv/bin/activate
```

安装依赖：

```bash
python -m pip install -r requirements.txt
```

## 五、运行健康检查

```bash
python healthcheck.py
```

预期输出类似：

```text
Qdrant connected
server version: 1.x.x
collections: 0
```

这一步故意不创建 Collection。健康检查只负责判断依赖服务是否可用，不应该顺便修改数据库状态。

## 六、为什么现在不急着接 Embedding 和 LLM

第一阶段先建立可靠边界：

| 模块 | 输入 | 输出 | 首要验收 |
| --- | --- | --- | --- |
| 文档处理 | 文件 | 标准化文本 | 内容未丢失 |
| Chunk | 标准化文本 | 文本块+元数据 | 可定位回原文 |
| Embedding | 文本块 | 固定维度向量 | 维度一致 |
| 向量库 | 向量+Payload | 可检索记录 | 可重复写入 |
| Retrieval | 问题 | 候选片段 | 正确片段进入 Top-K |
| Generation | 问题+片段 | 答案+引用 | 不超出证据 |

把所有模块一次性写完，出现错误时很难判断是解析、切分、向量还是 Prompt 的问题。

## 七、验收清单

- [ ] `docker compose ps` 显示 Qdrant 正常运行；
- [ ] 浏览器能打开本地 Dashboard；
- [ ] Python 虚拟环境已激活；
- [ ] `python healthcheck.py` 能读取服务版本；
- [ ] `storage/` 已被 Git 忽略；
- [ ] 没有把 6333 端口暴露到公网。

## 常见问题

### 6333 端口被占用

```bash
docker compose down
```

检查本机占用，或修改 `compose.yaml` 左侧的宿主机端口。

### Docker 容器启动后立即退出

```bash
docker compose logs qdrant
```

优先检查 Docker Desktop 是否正常运行，以及数据卷是否有写入权限。

### Python 报连接失败

先用浏览器或 `curl http://localhost:6333` 验证服务，再检查脚本中的 `QDRANT_URL`。不要在服务未启动时反复重装 Python 包。

## 下一期

下一期将深入 Docker 部署 Qdrant：数据持久化、端口含义、容器排错，以及开发环境与生产环境之间必须补齐的安全措施。

## 参考资料

- [Qdrant Local Quickstart](https://qdrant.tech/documentation/quick-start/)
- [Qdrant Installation](https://qdrant.tech/documentation/installation/)
- [Qdrant Security](https://qdrant.tech/documentation/security/)
