"""RenderPipeline: Card -> Jinja2 template -> HTML file."""

import base64
import json
from datetime import datetime
from pathlib import Path
import httpx
from jinja2 import Environment, FileSystemLoader
from src.models import Card

HTML2CANVAS_JS_URL = "https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"


class RenderPipeline:
    """Render Card objects into magazine-style HTML files."""

    def __init__(self, template_dir: Path, output_dir: Path, data_dir: Path | None = None):
        self._env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._data_dir = Path(data_dir) if data_dir else Path("data/cards")
        self._html2canvas_b64 = self._load_html2canvas()

    def _load_html2canvas(self) -> str:
        try:
            resp = httpx.get(HTML2CANVAS_JS_URL, timeout=15.0)
            resp.raise_for_status()
            return base64.b64encode(resp.content).decode("ascii")
        except Exception:
            stub = b'function html2canvas(e,t){var n=document.createElement("canvas");return n.getContext("2d"),Promise.resolve(n)}'
            return base64.b64encode(stub).decode("ascii")

    def render(self, card: Card, **extra) -> Path:
        template_name = f"{card.type.value}.html"
        template = self._env.get_template(template_name)

        sections = self._group_by_topic(card)
        source_names = list(dict.fromkeys(item.source_id for item in card.items))

        html = template.render(
            card=card,
            sections=sections,
            sources=source_names,
            html2canvas_b64=self._html2canvas_b64,
            filename=card.id,
            subtitle=extra.get("subtitle", ""),
            team=extra.get("team", ""),
        )

        # Use card.id as filename if available, fallback to type_date
        safe_id = card.id.replace("/", "_").replace("\\", "_").replace(" ", "_")
        output_path = self._output_dir / f"{safe_id}.html"
        output_path.write_text(html, encoding="utf-8")
        return output_path

    def build_index(self) -> Path:
        """Generate index.html dashboard from all JSON cards in data_dir."""
        cards_data: list[dict] = []
        for p in sorted(self._data_dir.glob("*.json")):
            data = json.loads(p.read_text(encoding="utf-8"))
            cards_data.append(data)

        template = self._env.get_template("index.html")
        html = template.render(
            cards_json=json.dumps(cards_data, ensure_ascii=False, default=str),
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

        output_path = self._output_dir / "index.html"
        output_path.write_text(html, encoding="utf-8")
        return output_path

    @staticmethod
    def _group_by_topic(card: Card) -> list[dict]:
        """Group items by topic tags. Each item appears in its first meaningful tag section."""
        groups: dict[str, list] = {}
        SKIP_TAGS = {"期刊", "顶会"}  # source-type labels, not topics
        TAG_PRIORITY = ["大模型", "可解释性", "NLP", "多模态", "CS",
                        "数据挖掘", "软计算", "信息检索",
                        "工程", "系统工程", "制造", "能源",
                        "管理", "管理信息系统", "决策支持",
                        "知识管理", "风险分析", "技术预测",
                        "项目管理", "运营管理", "生产管理", "运筹", "信息系统",
                        "ABS4", "ABS3", "FMS_A", "FMS_B", "CAS1", "CAS2"]
        for item in card.items:
            tags = [t for t in (getattr(item, "tags", []) or []) if t not in SKIP_TAGS]
            if not tags:
                tags = ["未分类"]
            ordered = sorted(tags, key=lambda t: TAG_PRIORITY.index(t) if t in TAG_PRIORITY else 99)
            groups.setdefault(ordered[0], []).append(item)
        return [{"label": k, "entries": v} for k, v in groups.items()]
