#!/usr/bin/env python3
"""
FlashSloth 自动构建推送脚本
每 N 分钟运行一次：
1. 检查 blog/docs/posts/ 是否有新/修改的文件
2. 如果有变化 → mkdocs build → git commit → git push
3. GitHub Actions 自动部署到 GitHub Pages
"""

import os, sys, subprocess, hashlib, json
from datetime import datetime

BLOG_DIR = "/opt/data/contenthub/blog"
POSTS_DIR = os.path.join(BLOG_DIR, "docs", "posts")
SITE_DIR = os.path.join(BLOG_DIR, "site")
STATE_FILE = "/opt/data/contenthub/tmp/builder_state.json"
GIT_DIR = "/opt/data/contenthub"

os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)


def get_posts_hash() -> str:
    """计算 posts 目录的 MD5，快速判断是否有变化"""
    hasher = hashlib.md5()
    if not os.path.exists(POSTS_DIR):
        return ""
    for f in sorted(os.listdir(POSTS_DIR)):
        if f.endswith(".md"):
            fpath = os.path.join(POSTS_DIR, f)
            try:
                with open(fpath, "rb") as fh:
                    hasher.update(fh.read())
            except:
                pass
    return hasher.hexdigest()


def build_site() -> bool:
    """运行 mkdocs build"""
    mkdocs = "/opt/data/home/.local/bin/mkdocs"
    result = subprocess.run(
        [mkdocs, "build", "-f", os.path.join(BLOG_DIR, "mkdocs.yml")],
        capture_output=True, text=True, cwd=BLOG_DIR
    )
    if result.returncode != 0:
        print(f"[{datetime.now().isoformat()}] ❌ 构建失败:\n{result.stderr[:500]}")
        return False
    return True


def git_push():
    """提交并推送变化到 GitHub"""
    token_path = "/opt/data/contenthub/secrets/GITHUB_TOKEN"
    if not os.path.exists(token_path):
        print("⚠️ 没有 GitHub token，跳过推送")
        return False

    with open(token_path) as f:
        token = f.read().strip()

    # Check if there are changes
    result = subprocess.run(
        ["git", "-C", GIT_DIR, "status", "--porcelain"],
        capture_output=True, text=True
    )

    if not result.stdout.strip():
        print(f"[{datetime.now().isoformat()}] 📭 没有变化，跳过推送")
        return False

    # Commit and push
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    cmds = [
        ["git", "-C", GIT_DIR, "add", "-A"],
        ["git", "-C", GIT_DIR, "commit", "-m", f"📝 auto: 博客更新 @ {date_str}"],
        ["git", "-C", GIT_DIR, "push", f"https://duxingkei33:{token}@github.com/duxingkei33/duxingkei33.github.io.git", "main"],
    ]

    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 and "nothing to commit" not in result.stderr:
            print(f"[{datetime.now().isoformat()}] ⚠️ git 操作: {result.stderr[:200]}")
            return False

    print(f"[{datetime.now().isoformat()}] ✅ 已推送 {len(result.stdout.split(chr(10)))} 个文件")
    return True


def main():
    print(f"[{datetime.now().isoformat()}] 🔄 FlashSloth 自动构建检查...")

    # 1. 检查文章是否有变化
    current_hash = get_posts_hash()

    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        last_hash = state.get("posts_hash", "")
    except:
        last_hash = ""

    if current_hash == last_hash:
        print(f"[{datetime.now().isoformat()}] 📭 文章无变化")
        # 还是会检查 git 是否有未推送的构建产物变化
        git_push()
        return

    # 2. 构建
    print(f"[{datetime.now().isoformat()}] 🔨 检测到文章变化，开始构建...")
    if not build_site():
        return

    # 3. 推送
    git_push()

    # 4. 保存状态
    with open(STATE_FILE, "w") as f:
        json.dump({"posts_hash": current_hash, "last_build": datetime.now().isoformat()}, f)

    print(f"[{datetime.now().isoformat()}] ✅ 完成")


if __name__ == "__main__":
    main()
