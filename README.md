# 🦥 duxingkei 的博客

> 技术笔记与项目管理 | ESPHome / Home Assistant / 嵌入式开发

个人技术博客，由 [Hugo](https://gohugo.io/) + [PaperMod](https://github.com/adityatelange/hugo-PaperMod) 构建，通过 GitHub Actions 自动部署到 GitHub Pages。

## 本地开发

```bash
# 构建
cd blog && hugo

# 本地预览
cd blog && hugo server -D
```

## 发布文章

在 `blog/content/posts/` 下创建 Markdown 文件，frontmatter 格式：

```yaml
---
title: "文章标题"
date: 2026-06-30
slug: "xianyu-gateway"
summary: "文章摘要"
tags:
  - 标签1
  - 标签2
---
```

文章 URL 自动生成为 `/YYYY/MM/DD/slug/`。

## 评论系统

使用 [Giscus](https://giscus.app/) — 基于 GitHub Discussions 的评论系统。配置完成后在 `hugo.toml` 中填入 `repoId` 和 `categoryId`。

## 🔗 链接

- **博客地址：** https://duxingkei33.github.io
- **FlashSloth 项目：** https://github.com/duxingkei33/flashsloth
- **GitHub：** https://github.com/duxingkei33

## 📄 许可

### 文章
本博客所有文章采用 **知识共享署名-相同方式共享 4.0 国际许可协议（CC BY-SA 4.0）** 进行许可。

您可以自由地：
- **共享** — 在任何媒介以任何形式复制、发行本作品
- **演绎** — 修改、转换或以本作品为基础进行创作

惟须遵守：
- **署名** — 您必须给出适当的署名，提供指向本许可协议的链接
- **相同方式共享** — 如果您再混合、转换或者基于本作品进行创作，您必须基于同样的许可协议分发您的贡献

**欢迎转载！** 转载时请注明原文链接。

详细协议内容请见：https://creativecommons.org/licenses/by-sa/4.0/

### 代码
博客中涉及的代码片段另行许可。除特别声明外，**禁止商用**。

---

*🦥 Built with Hugo + PaperMod*
