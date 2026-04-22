#!/usr/bin/env python3
"""
构建脚本：将 README.md 转换为完整的静态网站
"""

import re
import json
import os
from pathlib import Path
from datetime import datetime

# 基础配置
BASE_URL = "https://lessup.github.io/the-book-of-secret-knowledge-zh"
REPO_URL = "https://github.com/LessUp/the-book-of-secret-knowledge-zh"

# 分类映射 - 对应 README 中的实际标题格式
CATEGORIES = {
    "cli-tools": {
        "title": "CLI 工具", 
        "icon": "🛠️", 
        "patterns": ["CLI 工具", "CLI Tools"],
        "path": "tools"
    },
    "gui-tools": {
        "title": "GUI 工具", 
        "icon": "🖥️", 
        "patterns": ["GUI 工具", "GUI Tools"],
        "path": "gui-tools"
    },
    "web-tools": {
        "title": "Web 工具", 
        "icon": "🌐", 
        "patterns": ["Web 工具", "Web Tools"],
        "path": "web-tools"
    },
    "system": {
        "title": "系统/服务", 
        "icon": "⚙️", 
        "patterns": ["系统/服务", "系统服务", "System"],
        "path": "system"
    },
    "network": {
        "title": "网络", 
        "icon": "🌐", 
        "patterns": ["网络", "Network"],
        "path": "network"
    },
    "containers": {
        "title": "容器/编排", 
        "icon": "🐳", 
        "patterns": ["容器/编排", "容器编排", "Containers"],
        "path": "containers"
    },
    "guides": {
        "title": "手册/指南/教程", 
        "icon": "📖", 
        "patterns": ["手册/指南/教程", "手册指南教程", "Manuals", "Guides"],
        "path": "guides"
    },
    "lists": {
        "title": "精选列表", 
        "icon": "⭐", 
        "patterns": ["精选列表", "Awesome Lists"],
        "path": "lists"
    },
    "media": {
        "title": "博客/播客/视频", 
        "icon": "🎧", 
        "patterns": ["博客/播客/视频", "博客播客视频", "Blogs", "Podcasts"],
        "path": "media"
    },
    "pentest": {
        "title": "黑客/渗透测试", 
        "icon": "🔐", 
        "patterns": ["黑客/渗透测试", "黑客渗透测试", "Hacking", "Pentest"],
        "path": "pentest"
    },
    "cheatsheets": {
        "title": "其他速查表", 
        "icon": "📋", 
        "patterns": ["其他速查表", "Cheat Sheets"],
        "path": "cheatsheets"
    },
    "one-liners": {
        "title": "Shell 单行命令", 
        "icon": "⚡", 
        "patterns": ["Shell 单行命令", "One-liners"],
        "path": "one-liners"
    },
    "shell-tricks": {
        "title": "Shell 技巧", 
        "icon": "💡", 
        "patterns": ["Shell 技巧", "Shell Tricks"],
        "path": "shell-tricks"
    },
    "shell-functions": {
        "title": "Shell 函数", 
        "icon": "🔧", 
        "patterns": ["Shell 函数", "Shell Functions"],
        "path": "shell-functions"
    },
}


def escape_html(text):
    """转义 HTML 特殊字符"""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;"))


def parse_inline(text):
    """解析行内 Markdown 元素，保留已有 HTML 标签"""
    # Emoji 别名替换
    emoji_map = {
        ':cn:': '🇨🇳',
        ':construction:': '🚧',
        ':black_small_square:': '▪',
        ':anger:': '💢',
    }
    for alias, emoji in emoji_map.items():
        text = text.replace(alias, emoji)
    
    # 将已有的 HTML 标签暂时替换为占位符
    html_tags = []
    def store_html_tag(match):
        html_tags.append(match.group(0))
        return f"\x00HTML_{len(html_tags)-1}\x00"
    
    # 保存已存在的 HTML 标签
    text = re.sub(r'<[^>]+>', store_html_tag, text)
    
    # HTML 转义（只对非 HTML 内容）
    text = escape_html(text)
    
    # 恢复 HTML 标签
    for i, tag in enumerate(html_tags):
        text = text.replace(f"&quot;\x00HTML_{i}\x00&quot;", tag)
        text = text.replace(f"\x00HTML_{i}\x00", tag)
    
    # 粗体 **text** 或 __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    
    # 斜体 *text* 或 _text_
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    
    # 行内代码 `code`
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    
    # 链接 [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    
    # 图片 ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
    
    return text


def generate_anchor(text):
    """生成标题锚点"""
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 移除 emoji
    text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]', '', text)
    # 清理并生成锚点
    anchor = text.strip().lower()
    anchor = re.sub(r'[^\w\s-]', '', anchor)
    anchor = re.sub(r'\s+', '-', anchor)
    anchor = anchor.strip('-')
    return anchor or 'section'


def parse_markdown_content(lines, start_idx=0):
    """解析 Markdown 内容块，返回 HTML"""
    result = []
    in_code_block = False
    code_lang = ''
    code_lines = []
    
    i = start_idx
    while i < len(lines):
        line = lines[i]
        
        # 代码块
        if line.startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_lang = line[3:].strip() or 'text'
                code_lines = []
            else:
                in_code_block = False
                code_content = '\n'.join(escape_html(l) for l in code_lines)
                result.append(f'<pre><code class="language-{code_lang}">{code_content}</code></pre>')
            i += 1
            continue
        
        if in_code_block:
            code_lines.append(line)
            i += 1
            continue
        
        # 检测是否是新的主分类标题（停止解析）
        # 在 README 中，分类标题是 #### 级别，所以遇到下一个 #### 标题时停止
        if line.startswith('#### ') and i > start_idx:
            break
        
        # 标题
        if line.startswith('#### '):
            title = line[5:].strip()
            anchor = generate_anchor(title)
            result.append(f'<h4 id="{anchor}">{parse_inline(title)}</h4>')
        elif line.startswith('#####'):
            # 处理五级和六级标题
            level = 5
            title_start = 6
            # 计算#的数量
            while title_start < len(line) and line[title_start] == '#':
                level += 1
                title_start += 1
            title = line[title_start:].strip()
            anchor = generate_anchor(title)
            tag = f'h{min(level, 6)}'
            result.append(f'<{tag} id="{anchor}">{parse_inline(title)}</{tag}>')
        # 引用块
        elif line.startswith('>'):
            content = line[1:].strip()
            result.append(f'<blockquote>{parse_inline(content)}</blockquote>')
        # 普通段落（非空行）
        elif line.strip():
            stripped = line.strip()
            # 如果行以 HTML 标签开头和结尾，则不添加额外的 <p> 包裹
            if (stripped.startswith('<') and stripped.endswith('>') and 
                not stripped.startswith('<a ') and not stripped.startswith('<img')):
                result.append(parse_inline(line))
            # 检测是否是工具链接行
            elif '&nbsp;&nbsp;' in line and '<a href=' in line:
                # 处理工具列表
                result.append(parse_tool_line(line))
            else:
                result.append(f'<p>{parse_inline(line)}</p>')
        
        i += 1
    
    return '\n'.join(result), i


def parse_tool_line(line):
    """解析工具链接行，转换为卡片"""
    # 提取所有链接和描述
    # 格式: &nbsp;&nbsp; <a href="url"><b>Name</b></a> - Description<br>
    
    pattern = r'<a href="([^"]+)"[^>]*><b>([^<]+)</b></a>\s*-\s*([^<]+)'
    matches = re.findall(pattern, line)
    
    if not matches:
        return f'<p>{parse_inline(line)}</p>'
    
    cards = []
    for url, name, desc in matches:
        # 提取域名
        domain = url.replace('https://', '').replace('http://', '').split('/')[0]
        domain = domain.replace('www.', '')
        
        cards.append(f'''<div class="tool-card">
    <div class="tool-header">
        <a href="{url}" target="_blank" rel="noopener" class="tool-name">{name}</a>
        <span class="tool-domain">{domain}</span>
    </div>
    <p class="tool-desc">{desc.strip()}</p>
</div>''')
    
    return '\n'.join(cards)


def extract_category_content(content, category_patterns):
    """从 README 内容中提取特定分类的内容"""
    lines = content.split('\n')
    
    # 查找分类标题（必须是 #### 级别的主分类）
    start_idx = -1
    for i, line in enumerate(lines):
        # 检查是否是目标分类标题 - 必须是 #### 开头
        if line.startswith('#### '):
            title_part = line[5:].strip()
            for pattern in category_patterns:
                # 检查模式是否在标题的主要部分（不在括号内）
                # 移除 HTML 标签和链接后检查
                clean_title = re.sub(r'<[^>]+>', '', title_part)
                clean_title = re.sub(r'\[.*?\]', '', clean_title)
                # 检查模式是否是标题的主要名称（开头或完整匹配）
                if clean_title.startswith(pattern) or f' {pattern}' in clean_title:
                    start_idx = i
                    break
        if start_idx >= 0:
            break
    
    if start_idx < 0:
        return None
    
    # 根据匹配的模式确定使用哪个预定义标题
    category_title = None
    title_line = lines[start_idx]
    for pattern in category_patterns:
        if pattern in title_line:
            # 找到匹配的分类配置
            for cat in CATEGORIES.values():
                if pattern in cat['patterns']:
                    category_title = cat['title']
                    break
            break
    
    if not category_title:
        # 降级：尝试从行中提取
        category_title = title_line[5:].strip()
        category_title = re.sub(r'<[^>]+>', '', category_title)
        category_title = re.sub(r':\w+:', '', category_title)
        category_title = re.sub(r'\s*\[.*\]\s*', '', category_title)
        category_title = re.sub(r'\s*\(.*\)\s*$', '', category_title)
        category_title = ' '.join(category_title.split())
    
    # 解析内容直到下一个主标题
    html_content, _ = parse_markdown_content(lines, start_idx + 1)
    
    return {
        'title': category_title,
        'html': html_content
    }


def get_outline_from_html(html):
    """从 HTML 中提取大纲"""
    outline = []
    
    # 匹配 h4 和 h5
    for match in re.finditer(r'<h([45]) id="([^"]+)">(.+?)</h\1>', html):
        level = int(match.group(1)) - 2  # h4 -> 2, h5 -> 3
        anchor = match.group(2)
        title = re.sub(r'<[^>]+>', '', match.group(3))
        outline.append({'level': level, 'anchor': anchor, 'title': title})
    
    return outline


def generate_page(title, content, outline, category_info=None):
    """生成完整 HTML 页面"""
    
    # 构建面包屑
    breadcrumb = ''
    if category_info:
        breadcrumb = f'''
        <nav class="breadcrumb">
            <a href="/the-book-of-secret-knowledge-zh/">首页</a>
            <span class="separator">/</span>
            <span class="current">{category_info["title"]}</span>
        </nav>'''
    
    # 构建右侧大纲
    outline_html = ''
    if outline:
        outline_html = '<nav class="page-outline"><h4>本页大纲</h4><ul>'
        for item in outline:
            indent = 'class="level-3"' if item['level'] == 3 else ''
            outline_html += f'<li {indent}><a href="#{item["anchor"]}">{item["title"]}</a></li>'
        outline_html += '</ul></nav>'
    
    # 生成分类导航
    cat_nav = ''
    for key, cat in CATEGORIES.items():
        cat_nav += f'<a href="/the-book-of-secret-knowledge-zh/{cat["path"]}/" class="toc-item">{cat["icon"]} {cat["title"]}</a>'
    
    # 计算相对路径
    css_path = "/the-book-of-secret-knowledge-zh/css/style.css"
    js_search = "/the-book-of-secret-knowledge-zh/js/search.js"
    js_theme = "/the-book-of-secret-knowledge-zh/js/theme.js"
    js_nav = "/the-book-of-secret-knowledge-zh/js/nav.js"
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | 秘密知识之书</title>
    <meta name="description" content="{title} - 秘密知识之书中文版，系统管理员、DevOps工程师和安全研究人员的知识宝库">
    <meta name="keywords" content="DevOps, SysAdmin, Security, Pentest, Tools, CLI, 中文翻译, 渗透测试, 安全工具">
    <meta property="og:title" content="{title} | 秘密知识之书">
    <meta property="og:description" content="系统管理员、DevOps工程师和安全研究人员的知识宝库">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{BASE_URL}/">
    <link rel="canonical" href="{BASE_URL}/">
    <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E📚%3C/text%3E%3C/svg%3E">
    <link rel="stylesheet" href="{css_path}">
    <link rel="stylesheet" href="/the-book-of-secret-knowledge-zh/css/highlight.css">
</head>
<body data-theme="dark">
    <header class="site-header">
        <div class="header-left">
            <button class="menu-toggle" aria-label="切换菜单">
                <span></span>
                <span></span>
                <span></span>
            </button>
            <a href="/the-book-of-secret-knowledge-zh/" class="logo">
                <span class="logo-icon">📚</span>
                <span class="logo-text">秘密知识之书</span>
            </a>
        </div>
        <div class="header-center">
            <div class="search-box">
                <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="m21 21-4.3-4.3"></path>
                </svg>
                <input type="text" id="search-input" placeholder="搜索工具、资源... (Ctrl+K)" autocomplete="off">
                <div class="search-results" id="search-results"></div>
            </div>
        </div>
        <div class="header-right">
            <button class="theme-toggle" id="theme-toggle" aria-label="切换主题">
                <span class="theme-icon">🌙</span>
            </button>
            <a href="{REPO_URL}" class="github-link" target="_blank" rel="noopener" aria-label="GitHub">
                <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
                </svg>
            </a>
        </div>
    </header>

    <div class="site-container">
        <aside class="sidebar-left">
            <nav class="toc-tree">
                <div class="toc-section">
                    <h4>目录导航</h4>
                    {cat_nav}
                </div>
            </nav>
        </aside>

        <main class="content">
            {breadcrumb}
            <article class="markdown-body">
                {content}
            </article>
        </main>

        <aside class="sidebar-right">
            {outline_html}
        </aside>
    </div>

    <button class="back-to-top" id="back-to-top" aria-label="回到顶部">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="m18 15-6-6-6 6"/>
        </svg>
    </button>

    <script src="{js_search}"></script>
    <script src="{js_theme}"></script>
    <script src="{js_nav}"></script>
</body>
</html>'''
    
    return html


def generate_homepage():
    """生成首页"""
    
    # 特色卡片 - 显示前6个分类
    features_html = ''
    for i, (key, cat) in enumerate(list(CATEGORIES.items())[:6]):
        features_html += f'''
        <div class="feature-card">
            <div class="feature-icon">{cat["icon"]}</div>
            <h3>{cat["title"]}</h3>
            <a href="/the-book-of-secret-knowledge-zh/{cat["path"]}/" class="feature-link">查看全部 →</a>
        </div>'''
    
    # 分类网格 - 全部14个分类
    cat_grid = ''
    for key, cat in CATEGORIES.items():
        cat_grid += f'''
        <a href="/the-book-of-secret-knowledge-zh/{cat["path"]}/" class="category-card">
            <span class="category-icon">{cat["icon"]}</span>
            <span class="category-name">{cat["title"]}</span>
        </a>'''
    
    content = f'''
    <div class="hero-section">
        <div class="hero-content">
            <div class="hero-logo">📚</div>
            <h1 class="hero-title">秘密知识之书</h1>
            <p class="hero-subtitle">The Book of Secret Knowledge - Chinese Translation</p>
            <p class="hero-desc">系统管理员、DevOps、渗透测试与安全研究人员的知识宝库</p>
            <div class="hero-actions">
                <a href="{REPO_URL}" class="btn btn-primary" target="_blank">
                    <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
                    </svg>
                    View on GitHub
                </a>
                <a href="#categories" class="btn btn-secondary">浏览目录</a>
            </div>
        </div>
    </div>

    <div class="stats-section">
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-number">500+</div>
                <div class="stat-label">工具和资源</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">14</div>
                <div class="stat-label">主要分类</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">中文</div>
                <div class="stat-label">完整翻译</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">MIT</div>
                <div class="stat-label">开源协议</div>
            </div>
        </div>
    </div>

    <div class="features-section">
        <h2 class="section-title">核心内容</h2>
        <div class="features-grid">
            {features_html}
        </div>
    </div>

    <div class="categories-section" id="categories">
        <h2 class="section-title">内容分类</h2>
        <div class="categories-grid">
            {cat_grid}
        </div>
    </div>

    <div class="contribute-section">
        <div class="contribute-content">
            <h2>🤝 参与贡献</h2>
            <p>欢迎提交 Pull Request 帮助改进翻译或添加新内容</p>
            <a href="{REPO_URL}/blob/master/.github/CONTRIBUTING.md" class="btn btn-outline" target="_blank">
                查看贡献指南 →
            </a>
        </div>
    </div>
    '''
    
    return generate_page('首页', content, [])


def build_search_index(all_content):
    """构建搜索索引"""
    index = []
    
    for cat_key, data in all_content.items():
        if not data:
            continue
            
        # 添加分类
        cat_info = CATEGORIES.get(cat_key, {})
        index.append({
            'title': cat_info.get('title', cat_key),
            'path': f"/{cat_info.get('path', cat_key)}/",
            'type': 'category'
        })
        
        # 从内容中提取工具
        tools = re.findall(r'<a href="([^"]+)"[^>]*class="tool-name"[^>]*>([^<]+)</a>', data['html'])
        for url, name in tools:
            index.append({
                'title': name,
                'path': f"/{cat_info.get('path', cat_key)}/",
                'url': url,
                'category': cat_info.get('title', ''),
                'type': 'tool'
            })
    
    return index


def main():
    """主函数"""
    
    # 读取 README
    readme_path = Path('README.md')
    if not readme_path.exists():
        print("错误：找不到 README.md 文件")
        return 1
    
    readme_content = readme_path.read_text(encoding='utf-8')
    
    # 确保目录存在
    for cat in CATEGORIES.values():
        os.makedirs(f"docs/{cat['path']}", exist_ok=True)
    
    # 生成首页
    homepage_html = generate_homepage()
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(homepage_html)
    print("✓ 生成首页: docs/index.html")
    
    # 存储所有内容用于搜索索引
    all_content = {}
    
    # 为每个分类生成页面
    for cat_key, cat_info in CATEGORIES.items():
        content_data = extract_category_content(readme_content, cat_info['patterns'])
        
        if content_data:
            all_content[cat_key] = content_data
            
            # 提取大纲
            outline = get_outline_from_html(content_data['html'])
            
            # 生成页面
            page_html = generate_page(
                content_data['title'], 
                content_data['html'], 
                outline,
                category_info=cat_info
            )
            
            # 写入文件
            filepath = f"docs/{cat_info['path']}/index.html"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(page_html)
            
            print(f"✓ 生成页面: {filepath} ({cat_info['title']})")
        else:
            print(f"⚠ 未找到内容: {cat_info['title']}")
    
    # 生成搜索索引
    search_data = build_search_index(all_content)
    with open('docs/search-index.json', 'w', encoding='utf-8') as f:
        json.dump(search_data, f, ensure_ascii=False, indent=2)
    print(f"✓ 生成搜索索引: docs/search-index.json ({len(search_data)} 条数据)")
    
    print("\n✅ 构建完成!")
    return 0


if __name__ == '__main__':
    exit(main())
