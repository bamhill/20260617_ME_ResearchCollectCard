# Spec: 热点提取 + 主题报 + 默认顶会

Date: 2026-06-18

## Overview

四个增强合为一个迭代：
1. 默认顶会源 + `--all` 开关
2. 日期区间 + 主题过滤 → 主题报
3. 摘要热点提取：KeyBERT → DeepSeek 翻译 + 主题/方法分类
4. 模板热点区两列渲染

## Changes

### 1. CLI: `--all` + `--topic`

```
python cli.py paper                          # 今日顶会（6源）
python cli.py paper --all                    # 今日全部（8源）
python cli.py paper --topic 大模型            # 今日顶会，含标签"大模型"
python cli.py paper --from 06-10 --to 06-18 --topic 多模态  # 区间主题报
```

- `cli.py`: paper 命令新增 `--all` (bool flag) 和 `--topic` (str option)
- `config.py`: 新增 `top_conference_sources()` 方法，按 tags 含"顶会"过滤
- `--topic` 过滤在 TransformPipeline 中按 item.tags 匹配

### 2. `src/hotspot.py` — 热点提取模块

```
extract_hotspots(items: list, translate_fn: callable, top_n: int=15) -> dict:
    {
        "themes": ["大语言模型", "视频生成", "多模态对齐"],
        "methods": ["扩散模型", "思维链推理", "RLHF", "检索增强生成"]
    }
```

流程：
1. 收集所有 item 的 title + summary_raw 拼成 corpus
2. KeyBERT (`all-MiniLM-L6-v2`, keyphrase-ngram 1-3) 提取 top_n 英文短语
3. DeepSeek API 一次调用：翻译 + 分类为 themes/methods 两组
4. 返回分组后的中文热点词

依赖：`keybert` + `sentence-transformers`（首次自动下载 ~80MB 模型）

### 3. `src/models.py` — Card 加字段

```python
class Hotspots(BaseModel):
    themes: list[str] = Field(default_factory=list)   # 研究主题热点
    methods: list[str] = Field(default_factory=list)   # 技术方法热点

class Card(BaseModel):
    ...
    hotspots: Hotspots | None = None
```

### 4. `templates/paper.html` — 热点区两列渲染

替换当前「今日热点」区（目前硬编码取前 3 篇论文）为：

```jinja2
{% if card.hotspots %}
<div class="hot-section">
  <div class="hot-label">今日热点</div>
  <div class="hot-grid">
    <div class="hot-col">
      <div class="hot-col-label">📌 研究主题</div>
      {% for t in card.hotspots.themes %}
        <span class="hot-tag">{{ t }}</span>
      {% endfor %}
    </div>
    <div class="hot-col">
      <div class="hot-col-label">⚙️ 技术方法</div>
      {% for m in card.hotspots.methods %}
        <span class="hot-tag">{{ m }}</span>
      {% endfor %}
    </div>
  </div>
</div>
{% endif %}
```

CSS 新增 `.hot-grid` 两列 grid 容器 + `.hot-tag` 标签样式，保留现有红色双线边框 + 红底白字 label。

### 5. `src/pipeline/transform.py` — 集成热点

TransformPipeline.run() 中：
- `--topic` 过滤：按 item.tags 匹配
- 当 items 数量 >= 3 时，调用 `extract_hotspots()`
- 将结果设入 `card.hotspots`

### 6. `requirements.txt`

添加 `keybert`

## Non-goals

- 不做定时任务
- 不做 Web GUI
- 不生成微信公众号摘要（wechat 命令不受影响）
