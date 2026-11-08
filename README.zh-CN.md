# FairDetect

**本地优先的 AI 文本检测研究原型。** 双窗口分类器、可解释的判决层、Turnitin 风格报告，以及一个可以接上你自己本地模型的适配层。

> [!WARNING]
> **这个仓库开箱不能检测 AI 文本。**
> 产出下方数字的 DeBERTa 微调权重**没有随仓库发布**——它们训练所用的语料不允许再分发。你必须自己接一个本地模型：Hugging Face 分类器、本地 OpenAI 兼容大模型，或一个小的 HTTP 打分服务。
>
> 就算拿回原始权重，这套系统在**高能力人类学术写作**（MICUSP）上的实测误报率是 **26.7%**，在 3,478 篇人类留出集上是 **8.22%**。它没有和 Turnitin 校准，**绝不能拿它当处分或指控的唯一依据**。

---

## 这个项目在问什么

商业 AI 检测器对非母语英语写作者误伤严重。Liang 等（2023, *Patterns*）发现，人类写的 TOEFL 作文平均 **61.3%** 被判成 AI；最差的一个检测器把 **97.8%** 的人类作文标成 AI。Turnitin 自己也说明 AI 分是概率估计、可能误报，且不能作为处分的唯一依据。

FairDetect 只问一个更窄的问题：

> 能不能做一个本地、可检查的检测器，**对人类写作足够保守**，同时还能抓人化 AI？

答案是**部分可以**。失败的地方写在 [docs/LIMITS.md](docs/LIMITS.md) 和 [docs/EVALUATION.md](docs/EVALUATION.md)。

这个仓库是**能公开的最好版本**：完整推理管道、判决层、审阅界面、模型适配契约——除了权重，全都在。

---

## 仓库里有什么

| 部分 | 作用 |
| --- | --- |
| `app/` | React + Vite + Tailwind 审阅台。拖入 `.docx` / `.md` / `.txt`，选模型和判决档，出报告。 |
| `server/` | Python 标准库 HTTP 服务，不需要 FastAPI/Flask。加载适配器、跑任务、渲染 HTML/PDF 报告。 |
| `server/adapters.py` | **让这套东西能复用的关键。** `hf`（本地 Hugging Face 分类器）、`openai`（任意 OpenAI 兼容本地大模型）、`http`（你自己的打分服务）。 |
| `judge/judge.py` | 便携命令行，单篇和批量都行，和网页端同一套管道。 |
| `config/` | 模型与判决档定义，含默认、单模型、本地大模型、HTTP 四种示例。 |
| `docs/` | 评测、局限、模型契约、架构、伦理。 |
| `examples/` | 两段合成的冒烟测试文本，不是真实稿件。 |

没有权重、没有训练数据、没有学生文本。这个仓库刻意保持数据为零。

---

## 工作方式

```
.docx / .md / .txt
        |
        v
  提取文本  ->  切句  ->  每 8 句一个窗口，步长 2，最多 30 窗
                                      |
                         +------------+------------+
                         |                         |
                         v                         v
                   盾适配器                  矛适配器
                （保守，少冤枉）          （激进，少放过）
                         |                         |
                         +------------+------------+
                                      |
                                      v
                       每句均值 -> 判决规则 -> HTML/PDF/JSON
```

- **盾（shield）** 的训练目标是“别把真人判成 AI”，宁可漏。
- **矛（spear）** 的训练目标是“别放过 AI 和人化 AI”，宁可激进。
- **判决层（judge）** 是独立的一层规则，换档不用重训模型。

已发布的判决档（Judge 4.0）：

```
g = 盾的窗口均分（0..1）
r = 矛的窗口均分（0..1）
命中  iff  g >= 0.32  或  r >= 0.80
S     = 100 * max(g, r)
flag  未命中但 r >= 0.90     （建议人工看一眼）
```

这些阈值是**原始 FairDetect 模型对**的。你接自己的模型，要自己校准；配置里放这组数只是起点。

---

## 快速开始（自带模型）

### 1. 安装

```powershell
git clone https://github.com/profanebs/FairDetect.git
cd FairDetect
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Linux / macOS：`python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`。

### 2. 把检查点放进 `models/`

```
models/
  shield/
    config.json
    tokenizer.json
    tokenizer_config.json
    special_tokens_map.json
    model.safetensors
  spear/
    ...
```

任何 Hugging Face `AutoModelForSequenceClassification` 检查点都行。二分类用 softmax，单 logit 用 sigmoid。`ai_label_index` 设为 `"auto"` 时会读 `id2label`；标签含糊就手动填 `0` 或 `1`。

### 3. 自检

```powershell
python scripts/check_setup.py
```

它会把每个模型标成 `READY` 或 `MISSING`；一个都没就绪时退出码非零。

### 4. 启动审阅台

```powershell
python server/fairdetect_api.py
# 打开 http://127.0.0.1:8790
```

Windows 也可以双击 `scripts/start.cmd`。

服务默认只绑 **127.0.0.1**。确实需要局域网访问时再设 `FAIRDETECT_HOST=0.0.0.0`，并且先设 token（见下）。

### 5. 或者用命令行

```powershell
python judge/judge.py --list
python judge/judge.py --config config/models.json essay.txt
python judge/judge.py --config config/models.json --json essay.docx
python judge/judge.py --config config/models.json --batch meta.jsonl --out results.jsonl
```

---

## 接本地大模型（不是分类器）

`openai` 适配器走 OpenAI chat-completions 协议，Ollama、LM Studio、llama.cpp server、vLLM 都能接。

```powershell
copy config\models.openai.example.json config\models.llm.json
# 改 base_url 和 model，然后：
$env:FAIRDETECT_CONFIG = "config/models.llm.json"
python scripts/check_setup.py --score examples/human_style.txt
python server/fairdetect_api.py
```

常见端点：

| 运行时 | `base_url` | 说明 |
| --- | --- | --- |
| Ollama | `http://127.0.0.1:11434/v1` | 模型名要写完整 tag，例如 `qwen2.5:7b`。 |
| LM Studio | `http://127.0.0.1:1234/v1` | 先启动本地 server。 |
| llama.cpp | `http://127.0.0.1:8080/v1` | `llama-server -m model.gguf`。 |
| vLLM | `http://127.0.0.1:8000/v1` | 默认就是 OpenAI 兼容。 |

**用之前先读：**

- **每个窗口一次请求**（每篇最多 30 窗），一篇可能要几分钟。
- 返回的概率**对提示词敏感、没有校准**，0.32/0.80 那组阈值不能直接套。
- 它适合用来跑通管道、做实验，不适合拿来对人做判断。

只有一个模型时，用 `config/models.single.example.json`，把 `shield` 和 `spear` 都指向同一个模型 id。管道只打一次分，按 0.50 单阈值判决。

## 接自定义 HTTP 打分服务

实现这个契约：

```http
POST http://127.0.0.1:9000/score
Content-Type: application/json

{"text": "一个最多八句的窗口"}
```

返回：

```json
{"score": 0.73}
```

接受 `score`、`ai_probability`、`probability`。见 `config/models.http.example.json`。

---

## 配置说明

`config/models.json`：

```json
{
  "models": [
    {
      "id": "shield",
      "label": "Shield",
      "role": "shield",
      "adapter": "hf",
      "path": "models/shield",
      "ai_label_index": "auto",
      "max_length": 256,
      "device": "auto",
      "batch_size": 32,
      "win_sentences": 8,
      "stride_sentences": 2,
      "cap_windows": 30
    }
  ],
  "judges": [
    {
      "id": "mean-bar",
      "label": "Shield >= 0.32 OR Spear >= 0.80",
      "shield": "shield",
      "spear": "spear",
      "mode": "or",
      "stat": "mean",
      "g0": 0.32,
      "r0": 0.8
    }
  ],
  "default_judge": "mean-bar"
}
```

| 字段 | 含义 |
| --- | --- |
| `adapter` | `hf`、`openai`、`http`。 |
| `path` | HF 检查点目录，相对仓库根。 |
| `ai_label_index` | `"auto"`（读 `id2label`），或 `0` / `1`。 |
| `device` | `auto`、`cpu`、`cuda`、`cuda:1`…… |
| `max_length` | 每窗 tokenizer 截断长度，原始为 256。 |
| `win_sentences` / `stride_sentences` / `cap_windows` | 窗口管道，原始为 8 / 2 / 30。 |
| `aliases` | 可选，`/score` 和 `/batch` 额外接受的模型名。 |
| `base_url` / `model` | OpenAI 兼容端点和模型 tag。 |
| `url` / `field` | 自定义 HTTP 打分服务与返回字段。 |

环境变量：

| 变量 | 默认 | 含义 |
| --- | --- | --- |
| `FAIRDETECT_CONFIG` | `config/models.json` | 配置路径。 |
| `FAIRDETECT_PORT` | `8790` | HTTP 端口。 |
| `FAIRDETECT_HOST` | `127.0.0.1` | 绑定地址。 |
| `FAIRDETECT_CONSOLE_TOKEN` | 若存在则读 `server/service-token.txt` | `/score` 和 `/batch` 的 Bearer token。 |

---

## HTTP 接口

| 方法 | 路径 | 鉴权 | 用途 |
| --- | --- | --- | --- |
| GET | `/health` | 无 | 存活 + 模型可用性。 |
| GET | `/api/models` | 无 | 模型、判决档、可用性。 |
| POST | `/api/jobs` | 无 | 上传文件跑任务。 |
| GET | `/api/jobs/{id}` | 无 | 任务状态与结果。 |
| GET | `/api/jobs/{id}/report` | 无 | 单文件 HTML 报告。 |
| GET | `/api/jobs/{id}/pdf` | 无 | 用 headless Edge/Chrome 导出 PDF。 |
| POST | `/score` | 配了 token 就要 | 单篇打分。 |
| POST | `/batch` | 配了 token 就要 | 批量打分。 |

网页端走 `/api/jobs`；`score` / `batch` 给其他本地工具用。

---

## 实测结果（原始模型，冻结池）

这些数字来自原始 `r11-shield:ep1` × `r10-spear:ep0` 模型对、Judge 4.0 判决档。它们**不是**你接上的模型的结果。

| 指标 | 结果 |
| --- | --- |
| AHBench-10 AI 漏检 | **3 / 363**（0.83%） |
| 强人化 AI 漏检 | **2 / 23**（8.7%） |
| 人类冻结池（1,595 篇） | **99.418% 通过**（10 篇误报） |
| 人类留出集 · ESL 学习者（2,649 篇） | **97.55% 通过**（2.45% 误报） |
| 人类留出集 · MICUSP 学术写作（829 篇） | **73.34% 通过**（26.66% 误报） |
| MICUSP 母语者（681 篇） | **71.07% 通过**（28.93% 误报） |
| MICUSP 非母语者（148 篇） | **83.78% 通过**（16.22% 误报） |
| 全部人类留出集（3,478 篇） | **91.78% 通过**（8.22% 误报） |

### 怎么读这些数字

- **99.4% 的冻结池数字偏乐观。** 工作点是在包含评测材料的池子上调的。诚实数字是 3,478 篇留出集：**8.22% 的人类文档被标了**。
- **写作水平越高，越容易被误报。** 这是目前最大的系统性缺陷。
- **强人化集只有 23 篇。** 一篇就动 4.35 个百分点，只能当方向信号。
- **AI 侧阈值是在评测池上选的。** “3/363”自带选择偏差；独立定阈集一直没做完。
- **这些不是“作者用了 AI 的概率”。** 它们是越过某个模型特定阈值文本/窗口的占比。

完整细节：[docs/EVALUATION.md](docs/EVALUATION.md)。

---

## 已知局限

1. **高能力人类学术写作被过度标记**（MICUSP 在 v4 工作点 26.7% 误报；母语者 28.9%）。这是模型层面的问题，只调阈值修不好。
2. **人化 AI 会漏**。23 篇的集合不足以声称稳健。
3. **文档结构会改变分数**。某篇去掉 9 个节标题后，矛均分从 0.932 掉到 0.743，判决直接翻转。管道对切句和窗口对齐敏感。
4. **只打前 30 个窗口**。长文档实际上被截在前约 240 句。
5. **切句偏英语**。依赖拉丁标点和首字母大写。
6. **少于 4 句的文本会被拒绝。**
7. **没有和 Turnitin 校准。** 报告长得像 Turnitin，但数字不是同一个量，不能换算。
8. **没有对抗鲁棒性。** 改写和风格迁移攻击不在范围内。
9. **大模型适配器不是检测器。** 它只是把本地模型接到管道上的方式，概率对提示词敏感。
10. **审阅台是研究工具，不是服务。** 没有多用户鉴权、限流、审计日志。

更多：[docs/LIMITS.md](docs/LIMITS.md)。

---

## 合理使用与伦理

- **不要拿它去指控、惩罚或监视任何人。** 标记是“值得看一眼”的理由，不是对作者的结论。
- **学生文本留在本地。** 服务把上传文本放在进程内存里，报告/PDF 写到 `ops-reports/`。除非你配置了会外联的适配器，否则不调用外部服务。
- **不要通过这个工具把 FERPA / GDPR / 学校数据发给第三方 API。**
- **原始权重不发布**，因为训练语料包含需要注册或许可限制的资源。
- **Turnitin 是 Turnitin, LLC 的商标。** 本项目与 Turnitin 无隶属、无背书关系。

---

## 目录结构

```
FairDetect/
  app/                 React 审阅台（源码 + 构建产物）
  server/
    fairdetect_api.py  HTTP 服务、任务、报告渲染
    adapters.py        hf / openai / http 模型适配器
    report_zh.json     报告文案
  judge/judge.py       便携命令行
  config/              模型与判决档定义
  models/              你的检查点（git 忽略）
  docs/                评测、局限、契约、架构、伦理
  examples/            合成冒烟测试文本
  scripts/             自检与启动脚本
  requirements.txt
```

---

## 许可证

MIT，见 [LICENSE](LICENSE)。

## 引用

```bibtex
@misc{fairdetect2026,
  title  = {FairDetect: a local-first AI-text detection research prototype},
  author = {FairDetect contributors},
  year   = {2026},
  url    = {https://github.com/profanebs/FairDetect}
}
```
