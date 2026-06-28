"""
Builder: Article → MkDocs 站点

1. 读取 Notion 拉取的文章（或本地 Markdown）
2. 写入 MkDocs posts/ 目录
3. 构建静态站点
"""

import os, sys, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from packages.article import Article
from datetime import datetime
import subprocess

BLOG_DIR = os.path.join(os.path.dirname(__file__), "blog")
POSTS_DIR = os.path.join(BLOG_DIR, "docs", "posts")


def write_article(article: Article) -> str:
    """写入一篇 Article 到 MkDocs posts 目录"""
    os.makedirs(POSTS_DIR, exist_ok=True)

    # 生成文件名
    date_str = article.date or datetime.now().strftime("%Y-%m-%d")
    slug = article.slug or article.title.lower().replace(" ", "-")[:50]
    filename = f"{date_str}-{slug}.md"
    filepath = os.path.join(POSTS_DIR, filename)

    # 写文件
    md_content = article.to_markdown()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"  ✅ 已写入: {filename}")
    return filepath


def build() -> bool:
    """构建 MkDocs 站点"""
    print("\n🔨 构建站点...")
    result = subprocess.run(
        ["/opt/data/home/.local/bin/mkdocs", "build", "-f", os.path.join(BLOG_DIR, "mkdocs.yml")],
        capture_output=True, text=True, cwd=BLOG_DIR
    )

    if result.returncode != 0:
        print(f"❌ 构建失败:\n{result.stderr}")
        return False

    print(f"✅ 构建成功！输出目录: {os.path.join(BLOG_DIR, 'site')}")
    return True


def clean():
    """清空 posts 目录（重新生成）"""
    if os.path.exists(POSTS_DIR):
        shutil.rmtree(POSTS_DIR)
    os.makedirs(POSTS_DIR, exist_ok=True)


def batch_write(articles: list[Article]) -> list[str]:
    """批量写入文章"""
    files = []
    for a in articles:
        fp = write_article(a)
        files.append(fp)
    return files


if __name__ == "__main__":
    # 测试：从本地 Markdown 转换
    import frontmatter
    test_dir = os.path.join(BLOG_DIR, "docs", "drafts")
    os.makedirs(test_dir, exist_ok=True)

    # 写一篇测试文章
    test_article = Article(
        title="Hello World — 我的第一篇博客",
        body="这是通过 **ContentHub** 自动生成的博客文章。\n\n## 为什么写博客\n\n记录技术成长。",
        summary="第一篇博客，测试 ContentHub 全链路",
        tags=["测试", "ContentHub"],
        date=datetime.now().strftime("%Y-%m-%d"),
        status="ready",
    )

    clean()
    batch_write([test_article])
    build()

    print(f"\n🌐 本地预览: cd {BLOG_DIR} && python3 -m http.server 8000 -d site")
