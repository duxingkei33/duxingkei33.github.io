"""
Provider: Notion → Article

从 Notion 数据库拉文章，转成 Article 统一模型。
依赖：pip install notion-client python-frontmatter

用法：
  python3 provider_notion.py             # 拉取所有 ready 状态的文章
  python3 provider_notion.py --all       # 拉取全部
  python3 provider_notion.py --once      # 拉取后标记已发布

环境变量：
  NOTION_TOKEN      — Notion Integration Token
  NOTION_DB_ID      — 文章数据库 ID
"""

import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from packages.article import Article
from notion_client import Client
from datetime import datetime


def load_config():
    """读取 Notion 配置"""
    token = os.environ.get("NOTION_TOKEN") or _read_file("NOTION_TOKEN")
    db_id = os.environ.get("NOTION_DB_ID") or _read_file("NOTION_DB_ID")
    if not token or not db_id:
        print('请设置 NOTION_TOKEN 和 NOTION_DB_ID（环境变量或 /opt/data/contenthub/secrets/ 下文件）')
        sys.exit(1)
    return token, db_id


def _read_file(name: str) -> str | None:
    path = f"/opt/data/contenthub/secrets/{name}"
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return None


def _get_text(prop) -> str:
    """从 Notion RichText property 提取文本"""
    if not prop:
        return ""
    if isinstance(prop, list):
        return "".join([t.get("plain_text", "") for t in prop])
    if isinstance(prop, dict):
        rich_text = prop.get("rich_text", []) or prop.get("title", [])
        return "".join([t.get("plain_text", "") for t in rich_text])
    return str(prop)


def _get_select(prop) -> str:
    """从 Select property 提取值"""
    if isinstance(prop, dict):
        s = prop.get("select", {})
        return s.get("name", "") if s else ""
    return str(prop) if prop else ""


def _get_multi_select(prop) -> list[str]:
    """从 Multi-select property 提取值列表"""
    if isinstance(prop, dict):
        ms = prop.get("multi_select", [])
        return [item.get("name", "") for item in ms]
    return []


def _get_date_str(prop) -> str | None:
    """从 Date property 提取日期字符串"""
    if isinstance(prop, dict):
        d = prop.get("date", {})
        if d:
            return d.get("start", "")
    return None


def _get_cover_url(page: dict) -> str | None:
    """提取封面图 URL"""
    cover = page.get("cover")
    if cover:
        if cover.get("type") == "external":
            return cover["external"]["url"]
        if cover.get("type") == "file":
            return cover["file"]["url"]
    return None


def notion_to_article(page: dict) -> Article:
    """Notion Page → Article"""
    props = page.get("properties", {})
    pid = page["id"]

    # 获取正文（从 Notion blocks 读取）
    title = _get_text(props.get("标题", props.get("Title", props.get("title", {}))))

    return Article(
        title=title or "无标题",
        body="",  # 正文由 fetch_body 单独填充
        summary=_get_text(props.get("摘要", props.get("Summary", {}))),
        tags=_get_multi_select(props.get("标签", props.get("Tags", {}))),
        cover=_get_cover_url(page),
        slug=pid.replace("-", ""),
        date=_get_date_str(props.get("日期", props.get("Date", {}))),
        status=_get_select(props.get("状态", props.get("Status", {}))),
        metadata={"notion_id": pid},
    )


def fetch_body(notion: Client, page_id: str) -> str:
    """递归拉取 Notion 页面正文 → Markdown"""
    blocks = notion.blocks.children.list(page_id).get("results", [])
    md_parts = []

    for block in blocks:
        md = _block_to_markdown(block)
        if md:
            md_parts.append(md)

    return "\n\n".join(md_parts)


def _block_to_markdown(block: dict) -> str | None:
    """单个 Notion Block → Markdown"""
    btype = block.get("type", "")
    content = block.get(btype, {})

    # 文本类
    rich_text = content.get("rich_text", [])
    text = "".join([
        t.get("plain_text", "")
        for t in rich_text
    ])

    if btype == "paragraph":
        return text if text else None
    elif btype == "heading_1":
        return f"# {text}"
    elif btype == "heading_2":
        return f"## {text}"
    elif btype == "heading_3":
        return f"### {text}"
    elif btype == "bulleted_list_item":
        return f"- {text}"
    elif btype == "numbered_list_item":
        return f"1. {text}"
    elif btype == "quote":
        return f"> {text}"
    elif btype == "code":
        lang = content.get("language", "")
        return f"```{lang}\n{text}\n```"
    elif btype == "divider":
        return "---"
    elif btype == "image":
        return _image_to_md(content)
    elif btype == "callout":
        return f"> 💡 {text}"
    elif btype == "to_do":
        checked = content.get("checked", False)
        return f"- [{'x' if checked else ' '}] {text}"
    elif btype == "table":
        # 简化处理
        return text if text else None
    return text if text else None


def _image_to_md(content: dict) -> str:
    """图片 block → Markdown 图片"""
    img = content.get("external") or content.get("file") or {}
    url = img.get("url", "")
    caption = content.get("caption", [])
    alt = "".join([t.get("plain_text", "") for t in caption]) if caption else "image"
    return f"![{alt}]({url})"


def fetch_articles(status_filter: str | None = "ready") -> list[Article]:
    """从 Notion 拉取文章列表"""
    token, db_id = load_config()
    notion = Client(auth=token)

    # 构建过滤器
    filters = []
    if status_filter:
        filters.append({
            "property": "状态",
            "select": {"equals": status_filter}
        })
    # 也支持英文属性名
    if status_filter and not filters:
        filters.append({
            "property": "Status",
            "select": {"equals": status_filter}
        })

    query = {}
    if filters:
        query["filter"] = {"and": filters} if len(filters) > 1 else filters[0]

    results = notion.databases.query(database_id=db_id, **query)
    pages = results.get("results", [])

    articles = []
    for page in pages:
        article = notion_to_article(page)
        article.body = fetch_body(notion, page["id"])
        articles.append(article)

    return articles


def mark_published(page_id: str):
    """标记 Notion 页面为已发布"""
    token, db_id = load_config()
    notion = Client(auth=token)

    # 尝试中文/英文属性名
    try:
        notion.pages.update(
            page_id=page_id,
            properties={
                "状态": {"select": {"name": "已发布"}},
            }
        )
    except Exception:
        try:
            notion.pages.update(
                page_id=page_id,
                properties={
                    "Status": {"select": {"name": "published"}},
                }
            )
        except Exception as e:
            print(f"  标记失败: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Notion → Article Provider")
    parser.add_argument("--all", action="store_true", help="拉取全部文章")
    parser.add_argument("--once", action="store_true", help="拉取后标记已发布")
    args = parser.parse_args()

    status = None if args.all else "ready"
    articles = fetch_articles(status)

    if not articles:
        print("没有找到符合条件的文章")
        return

    for a in articles:
        print(f"\n📄 {a.title}")
        print(f"   标签: {a.tags}")
        print(f"   摘要: {a.summary or '(无)'}")
        print(f"   正文长度: {len(a.body)} 字")

        if args.once and a.metadata.get("notion_id"):
            mark_published(a.metadata["notion_id"])
            print(f"   ✅ 已标记为已发布")


if __name__ == "__main__":
    main()
