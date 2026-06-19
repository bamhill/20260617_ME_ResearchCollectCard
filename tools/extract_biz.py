"""从 WeChat 公众号名或文章 URL 提取 __biz 参数。

用法:
    python tools/extract_biz.py <公众号名> [...]

    按公众号名搜索:
      python tools/extract_biz.py "KGraph Pattern" "老刘NLP"

    从文章 URL 提取:
      python tools/extract_biz.py https://mp.weixin.qq.com/s/xxx

    批量从文件读:
      python tools/extract_biz.py --input accounts.txt

输出:
    JSON [{name/url, biz, source}]，可直接拼入 sources.json
"""

import json
import re
import sys
from pathlib import Path

import httpx


def extract_biz_from_html(html: str) -> str | None:
    """从 WeChat 文章 HTML 中提取 __biz 值。"""
    patterns = [
        r'var\s+biz\s*=\s*["\']([^"\']+)["\']',
        r'__biz[=:]["\']?([^"\'&\s]+)',
        r'window\.biz\s*=\s*["\']([^"\']+)["\']',
        r'["\']biz["\']\s*:\s*["\']([^"\']+)["\']',
    ]
    for p in patterns:
        m = re.search(p, html)
        if m:
            return m.group(1)
    return None


def search_by_name(name: str) -> dict:
    """通过搜狗微信搜索公众号名，从搜索结果提取 __biz。"""
    result = {"name": name, "biz": None, "error": None, "source": "sogou"}
    try:
        search_url = "https://weixin.sogou.com/weixin"
        params = {"query": name, "type": "1"}
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = httpx.get(search_url, params=params, headers=headers,
                         follow_redirects=True, timeout=15.0)
        resp.raise_for_status()

        m = re.search(r'__biz=([a-zA-Z0-9\-_=]+)', resp.text)
        if m:
            result["biz"] = m.group(1)
        else:
            m = re.search(r'url\s*=\s*["\']([^"\']*__biz=([^"\'&]+))', resp.text)
            if m:
                result["biz"] = m.group(2)
            else:
                result["error"] = "搜狗搜索结果中未找到 __biz"
    except httpx.HTTPError as e:
        result["error"] = f"HTTP 错误: {e}"
    except Exception as e:
        result["error"] = str(e)
    return result


def extract_from_url(url: str) -> dict:
    """尝试从文章 URL 直接提取 __biz。"""
    result = {"url": url, "biz": None, "error": None, "source": "direct"}
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = httpx.get(url, headers=headers, follow_redirects=True, timeout=15.0)
        resp.raise_for_status()
        biz = extract_biz_from_html(resp.text)
        if biz:
            result["biz"] = biz
        else:
            result["error"] = "HTML 中未找到 __biz"
            result["source"] = "direct_fail"
    except httpx.HTTPError as e:
        result["error"] = f"HTTP 错误: {e}"
        result["source"] = "direct_fail"
    except Exception as e:
        result["error"] = str(e)
        result["source"] = "direct_fail"
    return result


def main():
    items: list[str] = []

    if "--input" in sys.argv:
        idx = sys.argv.index("--input")
        if idx + 1 < len(sys.argv):
            path = Path(sys.argv[idx + 1])
            if path.exists():
                items.extend(
                    line.strip()
                    for line in path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                )

    skip_next = False
    for arg in sys.argv[1:]:
        if arg == "--input":
            skip_next = True
            continue
        if skip_next:
            skip_next = False
            continue
        items.append(arg)

    if not items:
        print("用法: python tools/extract_biz.py <公众号名|URL> [...] [--input file.txt]")
        sys.exit(1)

    results = []
    for item in items:
        if item.startswith("http"):
            results.append(extract_from_url(item))
        else:
            r = search_by_name(item)
            results.append(r)

    ok = [r for r in results if r.get("biz")]
    fail = [r for r in results if r.get("error")]

    print(json.dumps(results, ensure_ascii=False, indent=2))
    print()
    print(f"--- 总计: {len(results)}, 成功: {len(ok)}, 失败: {len(fail)}")
    for r in ok:
        label = r.get("name") or r.get("url", "")[:60]
        print(f"  {label} → __biz={r['biz']}")
    if fail:
        print("失败原因:")
        for r in fail:
            label = r.get("name") or r.get("url", "")[:60]
            print(f"  {label}: {r['error']}")


if __name__ == "__main__":
    main()
