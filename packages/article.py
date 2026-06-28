"""
Article — 全系统唯一数据模型
所有 Provider 输出此格式，所有 Publisher/Builder 消费此格式
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class Article:
    """文章统一模型"""
    title: str
    body: str                          # Markdown 正文
    summary: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    cover: Optional[str] = None        # 封面图 URL
    assets: list[str] = field(default_factory=list)  # 引用的图片/附件
    slug: Optional[str] = None         # URL 路径名
    date: Optional[str] = None         # 发布日期 "2026-06-28"
    status: str = "draft"              # draft | ready | published
    metadata: dict = field(default_factory=dict)

    def to_markdown(self) -> str:
        """转成带 frontmatter 的 Markdown（Hexo/MkDocs 兼容）"""
        lines = ["---"]
        lines.append(f'title: "{self.title}"')
        if self.date:
            lines.append(f"date: {self.date}")
        if self.tags:
            lines.append(f"tags: [{', '.join(self.tags)}]")
        if self.summary:
            lines.append(f"description: {self.summary}")
        if self.cover:
            lines.append(f"cover: {self.cover}")
        for k, v in self.metadata.items():
            lines.append(f"{k}: {v}")
        lines.append("---")
        lines.append("")
        lines.append(self.body)
        return "\n".join(lines)

    @classmethod
    def from_markdown(cls, text: str) -> "Article":
        """从 frontmatter Markdown 反解析"""
        import frontmatter
        fm = frontmatter.loads(text)
        return cls(
            title=fm.get("title", ""),
            body=fm.content,
            summary=fm.get("description"),
            tags=fm.get("tags", []),
            cover=fm.get("cover"),
            date=str(fm.get("date", "")),
            metadata={k: v for k, v in fm.metadata.items()
                      if k not in ("title", "date", "tags", "description", "cover")},
        )
