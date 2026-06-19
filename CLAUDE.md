# ME_ResearchCollectCard — Python 3.10+ CLI + Jinja2 杂志风 HTML

每日科研新资讯卡片生成器。两路输入（arXiv/bioRxiv 论文 + RSS 公众号）→ 杂志风竖版 HTML → 一键 PNG。

## Commands

```bash
python cli.py paper                    # 今日论文卡
python cli.py paper --date 2026-06-15  # 指定日期
python cli.py wechat                   # 今日公众号卡
python cli.py wechat --from 2026-06-10 --to 2026-06-17  # 日期范围
python cli.py sources                  # 列出来源
python cli.py list                     # 列出已有卡片
```

## Project Structure

```
cli.py                 # typer CLI 入口
sources.json           # 来源配置（数据驱动）
src/
  models.py            # Pydantic v2 数据模型
  config.py            # sources.json 读写
  fetchers/            # AbstractFetcher 策略：arxiv / biorxiv / rss
  pipeline/            # 三阶段流水线：fetch → transform → render
  store/               # CardRepository JSON 持久化
templates/             # Jinja2 杂志风模板
data/cards/            # JSON 卡片积累（idea 库原料）
out/                   # 生成的 HTML
```

## Architecture

```
cli.py (依赖注入组装) → FetchPipeline → TransformPipeline → RenderPipeline → out/*.html
                          ↓                    ↓
                     fetchers/            store/card_store.py
                   (策略模式)              → data/cards/*.json
```

新增来源 = 在 sources.json 加一行 + (如新类型) 实现 AbstractFetcher。

## Conventions

- Python 3.10+, typer, pydantic v2, jinja2, feedparser, httpx
- file:// 直开 HTML，零 CDN 依赖
- JSON 编码：ensure_ascii=False
- 测试：pytest + mock

## Boundaries

- 不处理 AI 摘要生成
- 不做 Web GUI
- 不做定时任务
- sources.json 的 RSS URL 需用户自行配置

## Reference Documents

- 进度与状态：@memory/下次会话.md
- 项目规则：@.claude/rules/（继承根规则）
- 通用规范：全局 `~/.claude/CLAUDE.md`
