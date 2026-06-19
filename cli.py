"""ResearchCollectCard CLI -- daily research news card generator."""

from datetime import date
from pathlib import Path
import typer
from src.config import Config
from src.models import DateRange
from src.fetchers.arxiv import ArxivFetcher
from src.fetchers.biorxiv import BiorxivFetcher
from src.fetchers.rss import RssFetcher
from src.fetchers.crossref import CrossrefFetcher
from src.pipeline.fetch import FetchPipeline
from src.pipeline.transform import TransformPipeline
from src.pipeline.render import RenderPipeline
from src.store.card_store import CardRepository

app = typer.Typer(help="科研新资讯卡片生成器")
_SUBTITLES = {"top": "顶会精选", "cs": "CS 类精选", "journal": "期刊精选", "all": "全源精选"}


def _build_pipeline() -> FetchPipeline:
    fetchers = {
        "arxiv": ArxivFetcher(), "biorxiv": BiorxivFetcher(),
        "rss": RssFetcher(), "crossref": CrossrefFetcher(),
    }
    return FetchPipeline(fetchers)


def _parse_date_range(date_str: str, from_str: str, to_str: str) -> DateRange:
    if from_str and to_str:
        return DateRange(start=date.fromisoformat(from_str), end=date.fromisoformat(to_str))
    if date_str:
        return DateRange.single(date.fromisoformat(date_str))
    return DateRange.single(date.today())


def _render_and_report(cards, renderer, repo, date_range, source="", topic="", label="论文"):
    """Save, render, build index, print summary. Shared by paper + wechat."""
    for c in cards:
        if c.item_count == 0:
            typer.echo(f"[SKIP] {c.id} (无内容)")
            continue
        if source:
            dp = (f'{date_range.start.strftime("%Y%m%d")}_{date_range.end.strftime("%Y%m%d")}'
                  if date_range.end != date_range.start
                  else c.date.strftime("%Y%m%d"))
            c.id = f'paper_{source}{"_" + topic if topic else ""}_{dp}'
        repo.save(c)
        sub = _SUBTITLES.get(source, source)
        if topic:
            sub = topic + " · " + sub
        path = renderer.render(
            c, subtitle=sub if source else "",
            team="数据智能与知识工程团队" if source else "")
        typer.echo(f"[OK] {path} ({c.item_count} 篇{label})")
    idx_path = renderer.build_index()
    typer.echo(f"[OK] {idx_path} (dashboard)")
    valid = [c for c in cards if c.item_count > 0]
    typer.echo(f"\n生成 {len(valid)} 张卡片，共 {sum(c.item_count for c in valid)} 篇{label}")


@app.command()
def paper(
    date_str: str = typer.Option(None, "--date", help="日期 YYYY-MM-DD"),
    from_date: str = typer.Option(None, "--from", help="起始日期 YYYY-MM-DD"),
    to_date: str = typer.Option(None, "--to", help="结束日期 YYYY-MM-DD"),
    translate: bool = typer.Option(False, "--translate", help="翻译英文摘要为中文"),
    source: str = typer.Option("top", "--source", help="来源: top(顶会,默认) | cs | journal | all"),
    topic: str = typer.Option(None, "--topic", help="多标签AND筛选（空格分隔，如: ABS4 管理信息系统）"),
):
    """生成论文日报卡片. 默认仅顶会."""
    config = Config.load()
    date_range = _parse_date_range(date_str, from_date, to_date)

    source_choices = {
        "top": config.top_conference_sources,
        "cs": config.cs_sources,
        "journal": config.journal_sources,
        "all": config.all_paper_sources,
    }
    if source not in source_choices:
        typer.echo(f"[ERROR] --source 仅支持: {', '.join(source_choices.keys())}")
        raise typer.Exit(1)
    sources = source_choices[source]()

    if topic:
        topics = [t.strip() for t in topic.split()]
        sources = [s for s in sources if all(t in s.tags for t in topics)]

    cards = _build_pipeline().run("paper", sources, date_range)
    cards = TransformPipeline().run(cards, translate=translate, topic=topic)

    # Merge multi-day cards into one
    if date_range.end != date_range.start:
        merged = []
        for c in cards:
            merged.extend(c.items)
        if merged:
            merged = TransformPipeline._dedup_by_url(merged)
            merged.sort(key=lambda x: x.published or date_range.end, reverse=True)
            cards[0].items = merged
            cards = [cards[0]]
        else:
            typer.echo("[SKIP] 区间内无内容")
            raise typer.Exit(0)

    repo = CardRepository(Path("data/cards"))
    renderer = RenderPipeline(Path("templates"), Path("out"))
    _render_and_report(cards, renderer, repo, date_range, source, topic)


@app.command()
def wechat(
    date_str: str = typer.Option(None, "--date", help="日期 YYYY-MM-DD"),
    from_date: str = typer.Option(None, "--from", help="起始日期 YYYY-MM-DD"),
    to_date: str = typer.Option(None, "--to", help="结束日期 YYYY-MM-DD"),
):
    """生成公众号日报卡片 (RSS)."""
    config = Config.load()
    date_range = _parse_date_range(date_str, from_date, to_date)
    cards = _build_pipeline().run("wechat", config.all_wechat_sources(), date_range)
    cards = TransformPipeline().run(cards)
    repo = CardRepository(Path("data/cards"))
    renderer = RenderPipeline(Path("templates"), Path("out"))
    _render_and_report(cards, renderer, repo, date_range, label="文章")


@app.command()
def sources():
    """列出所有来源."""
    config = Config.load()
    typer.echo("=== 论文来源 ===")
    for s in config.paper_sources:
        typer.echo(f"  [{s.type.value}] {s.id}: {s.name} ({s.query})")
    typer.echo("\n=== 公众号来源 ===")
    for s in config.wechat_sources:
        typer.echo(f"  [{s.type.value}] {s.id}: {s.name} ({s.query})")


@app.command()
def cards():
    """列出已生成的卡片."""
    repo = CardRepository(Path("data/cards"))
    metas = repo.list_all()
    if not metas:
        typer.echo("(尚无卡片)")
        return
    for m in metas:
        typer.echo(f"  {m.id} | {m.date} | {m.item_count} items | {m.idea_count} ideas")


@app.command()
def build():
    """重建 index.html dashboard."""
    renderer = RenderPipeline(Path("templates"), Path("out"))
    path = renderer.build_index()
    typer.echo(f"[OK] {path} 已重建")


if __name__ == "__main__":
    app()
