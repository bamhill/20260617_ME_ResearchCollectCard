# 科研新资讯卡片生成器

> 一句话生成杂志风 AI 科研日报——arXiv 顶会 + 32 本期刊 + 公众号，三路聚合，自动热点提取。

## 解决的问题

每天追踪文献需要刷 arXiv、逐本翻期刊、手动排版简报——至少 1.5 小时。这个工具一键完成抓取→热点提取→杂志风渲染。

**核心流程：**
1. 三路数据源自动聚合（arXiv 顶会/CS分类 + CrossRef 期刊 + RSS 公众号）
2. YAKE 英文关键词提取 → DeepSeek 翻译分类为「研究主题」和「技术方法」
3. 杂志风 HTML 渲染 → 一键 Save PNG

## 快速使用

### 方式一：对话式（推荐，零门槛）

在 Claude Code 中直接说出需求：

```
"生成今天的科研日报"
"出 ABS3 管理期刊可解释性卡片"
"生成这周 CS 类的论文日报"
"公众号日报"
"期刊精选卡片，只看中科院 1 区"
```

### 方式二：命令行

```bash
git clone https://github.com/bamhill/20260617_ME_ResearchCollectCard.git
pip install -r requirements.txt

python cli.py paper                              # 今日顶会日报（默认6源）
python cli.py paper --source cs                  # CS类（cat:cs.CL + cs.AI）
python cli.py paper --source journal             # 32本期刊（CrossRef）
python cli.py paper --source journal --topic CAS1              # 中科院1区
python cli.py paper --source journal --topic ABS4 管理信息系统   # ABS4管理类
python cli.py wechat                             # 公众号
```

### 交叉筛选

多标签 AND 交集，空格分隔：

```bash
# 中科院1区 + 可解释性 + 期刊
python cli.py paper --source journal --topic CAS1 可解释性
# 日期区间（自动合并为一张卡）
python cli.py paper --from 2026-06-10 --to 2026-06-18 --source journal --topic 工程
```

## 数据源

| 来源 | 内容 | 数量 | 数据方 |
|------|------|------|--------|
| `--source top` | ICML/NeurIPS/ICLR/ACL/CVPR/AAAI | 6 | arXiv |
| `--source cs` | arXiv CS.CL + CS.AI | 2 | arXiv |
| `--source journal` | ABS4/3, FMS A/B, CAS1/2 | 32 | CrossRef |
| `--source all` | 全部 | 40 | arXiv+CrossRef |
| `wechat` | 老刘NLP/专知/KGraph | 3 | RSS(WeWe) |

### 筛选标签

**分级**: `ABS4` `ABS3` `FMS_A` `FMS_B` `CAS1` `CAS2`
**领域**: `CS` `工程` `管理` `大模型` `NLP` `多模态` `可解释性` `数据挖掘` `软计算` `系统工程` `制造` `管理信息系统` `知识管理` `风险分析`

## 项目结构

```
├── SKILL.md                  # Claude Code Skill 主文件
├── cli.py                    # typer CLI 入口
├── sources.json              # 40 源配置（数据驱动）
├── src/
│   ├── fetchers/             # 策略模式：arxiv / crossref / rss / biorxiv
│   ├── pipeline/             # fetch → transform → render 三阶段
│   ├── hotspot.py            # YAKE + DeepSeek 热点提取
│   ├── models.py             # Pydantic v2 数据模型
│   └── utils.py              # 共享工具
├── templates/                # Jinja2 杂志风模板
├── tests/                    # 46 tests, pytest
└── docs/                     # 方案文档 + 投稿文章
```

## 输出

| 产出 | 格式 | 说明 |
|------|------|------|
| 论文日报卡片 | .html | 杂志风竖版，双击即开，零 CDN |
| 公众号日报卡片 | .html | 同上 |
| Dashboard | .html | 卡片浏览面板 |
| 卡片数据 | .json | data/cards/ 积累，可做 idea 库 |

## 设计特色

- ✅ **杂志风视觉**：米色纸张(#e9e2d6) + 红黑配色(#d7382f/#15130f) + 衬线体
- ✅ **热点自动提取**：YAKE 关键词 + DeepSeek 主题/方法分类
- ✅ **方法→文章映射**：点击方法标签展开对应论文列表
- ✅ **多标签交叉筛选**：ABS4+管理、CAS1+可解释性，精准定位
- ✅ **区间合并**：多天数据自动合为一张卡
- ✅ **完全离线**：HTML 双击即开，不依赖任何 CDN
- ✅ **46 tests**，pytest 1.29s 全绿

## 环境

- Python 3.10+
- `DEEPSEEK_API_KEY` — 热点提取翻译（可选，缺了跳过热点）
- WeWe RSS Docker：`docker start wewe-rss`（公众号源需要）

## 投稿

本项目的 Skill 创作分享已投稿至 TRAE 官方中文社区 SOLO 技能创作赛。

---

**仓库地址：** https://github.com/bamhill/20260617_ME_ResearchCollectCard
