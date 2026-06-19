---
name: research-collect-card
description: >
  科研新资讯卡片生成器。四路输入——arXiv顶会/CS分类 + CrossRef 32本ABS/FMS/CAS期刊
  + 期刊RSS直连(19本Elsevier/Springer/IEEE) + RSS公众号——
  生成杂志风竖版HTML日报。支持按来源、分级、领域交叉筛选。
  TRIGGER: "生成科研日报", "出论文卡片", "今日AI论文", "期刊精选", "顶会日报",
  "可解释性论文", "ABS3期刊", "工程类论文", "research digest",
  "公众号日报", "公众号论文", "RSS论文", "wechat card", "微信论文"
  DO NOT trigger on: 纯翻译请求, 不涉及论文抓取的文献检索
---

# ResearchCollectCard — 科研新资讯卡片生成器

Python CLI, 四路输入(arXiv/bioRxiv/CrossRef期刊/期刊RSS直连/RSS公众号) → 杂志风HTML → 一键PNG.

## Commands

### 论文卡 (paper)

```bash
python cli.py paper                              # 今日顶会日报 (默认6源: ICML/NeurIPS/ICLR/ACL/CVPR/AAAI)
python cli.py paper --source cs                  # CS类 (cat:cs.CL + cs.AI)
python cli.py paper --source journal             # 期刊精选 (32本CrossRef + 19本RSS直连)
python cli.py paper --source all                 # 全源
# 交叉筛选
python cli.py paper --source journal --topic CAS1           # 中科院1区
python cli.py paper --source journal --topic ABS4 管理信息系统 # ABS4管理类
python cli.py paper --source journal --topic 可解释性         # 可解释性期刊
# 日期区间 (多天自动合并为一张卡)
python cli.py paper --from 2026-06-10 --to 2026-06-18 --source journal --topic CS
```

### 公众号卡 (wechat)

```bash
python cli.py wechat                             # 今日公众号精选 (7源RSS)
python cli.py wechat --from 2026-06-10 --to 2026-06-17  # 区间
```

> 公众号依赖 WeWe RSS Docker: `docker start wewe-rss` (如未启动先执行)

### 管理命令

```bash
python cli.py sources         # 列出62源
python cli.py cards           # 列出已生成卡片
python cli.py build           # 重建 out/index.html dashboard
```

## Source types

| --source | 内容 | 数量 | 数据源 |
|----------|------|------|--------|
| `top` (默认) | 顶会: ICML/NeurIPS/ICLR/ACL/CVPR/AAAI | 6 | arXiv |
| `cs` | arXiv CS.CL + CS.AI | 2 | arXiv |
| `journal` | ABS4/3, FMS A/B, CAS1/2 期刊 | 51源(32 CrossRef + 19 RSS) | CrossRef + 期刊RSS |
| `all` | 全部论文源 | 59 | arXiv+CrossRef+RSS期刊 |
| *(wechat)* | 公众号: 老刘NLP/专知/KGraph/知识图谱科技/计算机学报/AI前沿速递/开放知识图谱 | 7 | RSS(WeWe) |

### 期刊 RSS 直连

19/32 本期刊已接入 RSS 直连，比 CrossRef 更快（出版当天即抓取）：

| 出版商 | 期刊数 | 状态 |
|--------|--------|------|
| Elsevier | 15 | ✅ 直连 (`rss.sciencedirect.com`) |
| Springer | 2 | ✅ 直连 (`link.springer.com`) |
| IEEE | 2 | ✅ 直连 (`ieeexplore.ieee.org`) |
| T&F/Wiley/INFORMS/ACM/SAGE/Emerald | 13 | ⏸ WAF拦截 |

RSS 和 CrossRef 双源并存，pipeline 自动 URL 去重。新增期刊 RSS: 在 `sources.json` 加 `{"type":"rss", "query":"<RSS_URL>", "tags":[...]}` 即可。

## Topic tags (空格分隔 = AND 交集)

**分级**: `ABS4` `ABS3` `FMS_A` `FMS_B` `CAS1` `CAS2`

**领域**: `CS` `工程` `管理` `大模型` `NLP` `多模态` `可解释性` `数据挖掘` `软计算` `系统工程` `制造` `管理信息系统` `知识管理` `风险分析` `能源` `信息检索` `决策支持` `项目管理` `运营管理` `信息系统` `技术预测`

## Output

- HTML 卡片: `out/paper_{source}_{topic}_{date}.html` (区间: `out/paper_{source}_{topic}_{start}_{end}.html`)
- 公众号卡: `out/wechat_{date}.html`
- Dashboard: `out/index.html`
- 卡片数据: `data/cards/*.json`
- 设计: 米色纸张(#e9e2d6) + 红黑配色 + 衬线体 + 双灰框热点区(主题/方法两列) + 点击展开方法列表

## Architecture

```
cli.py → Config → FetchPipeline → TransformPipeline → RenderPipeline → out/*.html
           │         │    │              │                 │
       sources.json  │  fetchers/   src/hotspot.py    templates/
                     │  (策略模式)   YAKE+DeepSeek    (Jinja2杂志风)
                     │  arxiv/crossref/rss
                     │
               CardRepository
               data/cards/*.json
```

- 数据结构: `src/models.py` (Pydantic v2)
- Fetcher 策略: `ArxivFetcher` / `CrossrefFetcher` / `RssFetcher` (含 Elsevier summary 日期回落 + TOC 过滤)
- 新增期刊(CrossRef): 编辑 `sources.json`, 加 `{"type":"crossref", "query":"<ISSN>", "tags":[...]}`
- 新增期刊(RSS): 加 `{"type":"rss", "query":"<RSS_URL>", "tags":[...]}`
- 未收录期刊清单: `docs/期刊待收录.md`

## Environment

- `DEEPSEEK_API_KEY` — 热点提取翻译 (缺了卡片仍生成，仅跳过热区)
- WeWe RSS: `docker start wewe-rss` (公众号源依赖)
- Python 3.10+, `pip install -r requirements.txt`
- 测试: `python -m pytest tests/ -q` (46 tests)

## 设计规则

卡片 CSS 设计约束（详见 `templates/_base.html`）:
- 对比度 ≥5.3:1 (`--muted` #5c554c on `--paper` #e9e2d6)
- 红色仅用于结构性强调（分区标题、编号、hover、kicker 徽章），不在琐碎标签上撒
- 主题/方法标签 11px 内联流式，不换行
- 分区标题: 红底白字, 12px sans-serif, 4px letter-spacing
