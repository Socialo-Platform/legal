#!/usr/bin/env python3
"""
Generate a single-page static website with vertical tabs from markdown documentation.
Usage: python generate_site.py
Output: Creates 'site/index.html'
"""

import re
from pathlib import Path

DOCS_DIR = Path(__file__).parent
OUTPUT_DIR = DOCS_DIR / "site"
SITE_TITLE = "Socialo Legal"

DOCS_METADATA = {
    "terms_and_conditions.md": {"title": "Terms and Conditions", "order": 1},
    "privacy_policy.md": {"title": "Privacy Policy", "order": 2},
    "politica_cookies.md": {"title": "Cookie Policy", "order": 3},
    "contrato_suscripcion.md": {"title": "Subscription Contract", "order": 4},
    "contrato_encargado_tratamiento_datos.md": {"title": "Data Processing Agreement", "order": 5},
    "subprocessors.md": {"title": "Subprocessors", "order": 6},
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        :root {{
            --text: #111;
            --text-light: #555;
            --bg: #fff;
            --bg-alt: #fafafa;
            --border: #e5e5e5;
        }}

        @media (prefers-color-scheme: dark) {{
            :root {{
                --text: #eee;
                --text-light: #999;
                --bg: #111;
                --bg-alt: #191919;
                --border: #2a2a2a;
            }}
        }}

        [data-theme="light"] {{
            --text: #111;
            --text-light: #555;
            --bg: #fff;
            --bg-alt: #fafafa;
            --border: #e5e5e5;
        }}

        [data-theme="dark"] {{
            --text: #eee;
            --text-light: #999;
            --bg: #111;
            --bg-alt: #191919;
            --border: #2a2a2a;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            font-size: 16px;
            line-height: 1.7;
            color: var(--text);
            background: var(--bg);
        }}

        .layout {{
            display: flex;
            min-height: 100vh;
        }}

        /* Sidebar */
        .sidebar {{
            width: 260px;
            background: var(--bg-alt);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            position: fixed;
            height: 100vh;
            z-index: 20;
        }}

        .sidebar-header {{
            padding: 1.5rem;
            border-bottom: 1px solid var(--border);
        }}

        .logo {{
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }}

        .tagline {{
            font-size: 0.75rem;
            color: var(--text-light);
        }}

        .tabs {{
            flex: 1;
            overflow-y: auto;
            padding: 1rem 0;
        }}

        .tab {{
            display: block;
            width: 100%;
            text-align: left;
            padding: 0.75rem 1.5rem;
            font-size: 0.9rem;
            color: var(--text-light);
            background: none;
            border: none;
            cursor: pointer;
            transition: all 0.15s;
            border-left: 2px solid transparent;
        }}

        .tab:hover {{
            color: var(--text);
            background: var(--bg);
        }}

        .tab.active {{
            color: var(--text);
            background: var(--bg);
            border-left-color: var(--text);
        }}

        .sidebar-footer {{
            padding: 1rem 1.5rem;
            border-top: 1px solid var(--border);
        }}

        .theme-btn {{
            font-size: 0.8rem;
            color: var(--text-light);
            background: none;
            border: 1px solid var(--border);
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
        }}

        .theme-btn:hover {{
            border-color: var(--text-light);
        }}

        /* Main content */
        .main {{
            flex: 1;
            margin-left: 260px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}

        .content-area {{
            flex: 1;
            padding: 3rem;
            max-width: 760px;
        }}

        .panel {{
            display: none;
        }}

        .panel.active {{
            display: block;
        }}

        .doc-title {{
            font-size: 1.75rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }}

        .content h1 {{ display: none; }}

        .content h2 {{
            font-size: 1.2rem;
            font-weight: 600;
            margin: 2.5rem 0 1rem;
        }}

        .content h3 {{
            font-size: 1.05rem;
            font-weight: 600;
            margin: 2rem 0 0.75rem;
        }}

        .content h4 {{
            font-size: 1rem;
            font-weight: 600;
            margin: 1.5rem 0 0.5rem;
        }}

        .content p {{
            margin-bottom: 1rem;
            color: var(--text-light);
        }}

        .content ul, .content ol {{
            margin: 1rem 0 1.5rem 1.25rem;
            color: var(--text-light);
        }}

        .content li {{
            margin-bottom: 0.4rem;
        }}

        .content a {{
            color: var(--text);
            text-decoration: underline;
            text-underline-offset: 2px;
        }}

        .content table {{
            width: 100%;
            margin: 1.5rem 0;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}

        .content th, .content td {{
            text-align: left;
            padding: 0.75rem;
            border-bottom: 1px solid var(--border);
        }}

        .content th {{ font-weight: 600; }}
        .content td {{ color: var(--text-light); }}

        .content blockquote {{
            border-left: 2px solid var(--border);
            padding-left: 1rem;
            margin: 1.5rem 0;
            color: var(--text-light);
            font-style: italic;
        }}

        .content hr {{
            border: none;
            border-top: 1px solid var(--border);
            margin: 2.5rem 0;
        }}

        .content code {{
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 0.9em;
            background: var(--bg-alt);
            padding: 0.15rem 0.4rem;
            border-radius: 3px;
        }}

        footer {{
            padding: 1.5rem 3rem;
            font-size: 0.8rem;
            color: var(--text-light);
            border-top: 1px solid var(--border);
        }}

        footer a {{ color: var(--text-light); }}

        /* Mobile */
        .mobile-header {{
            display: none;
            position: sticky;
            top: 0;
            background: var(--bg);
            border-bottom: 1px solid var(--border);
            padding: 1rem;
            z-index: 10;
            justify-content: space-between;
            align-items: center;
        }}

        .mobile-header .logo {{
            font-size: 0.95rem;
        }}

        .menu-btn {{
            background: none;
            border: 1px solid var(--border);
            width: 36px;
            height: 36px;
            border-radius: 4px;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 4px;
        }}

        .menu-btn span {{
            display: block;
            width: 16px;
            height: 2px;
            background: var(--text);
        }}

        .overlay {{
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.4);
            z-index: 15;
        }}

        .overlay.active {{
            display: block;
        }}

        @media (max-width: 768px) {{
            .mobile-header {{
                display: flex;
            }}

            .sidebar {{
                transform: translateX(-100%);
                transition: transform 0.25s ease;
            }}

            .sidebar.open {{
                transform: translateX(0);
            }}

            .main {{
                margin-left: 0;
            }}

            .content-area {{
                padding: 2rem 1.25rem;
            }}

            .doc-title {{
                font-size: 1.4rem;
            }}

            footer {{
                padding: 1.5rem 1.25rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="overlay" id="overlay" onclick="closeSidebar()"></div>

    <div class="mobile-header">
        <div class="logo">{site_title}</div>
        <button class="menu-btn" onclick="toggleSidebar()">
            <span></span><span></span><span></span>
        </button>
    </div>

    <div class="layout">
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <div class="logo">{site_title}</div>
                <div class="tagline">Legal Documentation</div>
            </div>

            <div class="tabs">
                {tabs}
            </div>

            <div class="sidebar-footer">
                <button class="theme-btn" onclick="toggleTheme()">Toggle theme</button>
            </div>
        </aside>

        <div class="main">
            <div class="content-area">
                {panels}
            </div>

            <footer>
                Socialo, S.L. &copy; 2026 &middot;
                <a href="mailto:info@socialo.live">info@socialo.live</a> &middot;
                <a href="mailto:dpo@socialo.live">dpo@socialo.live</a>
            </footer>
        </div>
    </div>

    <script>
        const tabs = document.querySelectorAll('.tab');
        const panels = document.querySelectorAll('.panel');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');

        function showTab(id) {{
            tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === id));
            panels.forEach(p => p.classList.toggle('active', p.id === id));
            localStorage.setItem('activeTab', id);
            closeSidebar();
        }}

        tabs.forEach(t => t.addEventListener('click', () => showTab(t.dataset.tab)));

        const saved = localStorage.getItem('activeTab');
        if (saved && document.getElementById(saved)) {{
            showTab(saved);
        }} else if (tabs[0]) {{
            showTab(tabs[0].dataset.tab);
        }}

        function getSystemTheme() {{
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }}

        function getCurrentTheme() {{
            const saved = localStorage.getItem('theme');
            if (saved) return saved;
            return getSystemTheme();
        }}

        function toggleTheme() {{
            const current = getCurrentTheme();
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
        }}

        // Apply saved theme if exists, otherwise let CSS media query handle it
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {{
            document.documentElement.setAttribute('data-theme', savedTheme);
        }}

        function toggleSidebar() {{
            sidebar.classList.toggle('open');
            overlay.classList.toggle('active');
        }}

        function closeSidebar() {{
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        }}
    </script>
</body>
</html>
"""


def markdown_to_html(text):
    lines = text.split('\n')
    html = []
    in_ul, in_ol, in_table = False, False, False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            if in_ul: html.append('</ul>'); in_ul = False
            if in_ol: html.append('</ol>'); in_ol = False
            if in_table: html.append('</tbody></table>'); in_table = False
            continue

        if stripped.startswith('#### '): html.append(f'<h4>{inline(stripped[5:])}</h4>'); continue
        if stripped.startswith('### '): html.append(f'<h3>{inline(stripped[4:])}</h3>'); continue
        if stripped.startswith('## '): html.append(f'<h2>{inline(stripped[3:])}</h2>'); continue
        if stripped.startswith('# '): html.append(f'<h1>{inline(stripped[2:])}</h1>'); continue

        if stripped in ['---', '***', '___']: html.append('<hr>'); continue

        if '|' in stripped and stripped.startswith('|'):
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            if not in_table:
                html.append('<table><thead><tr>')
                html.extend(f'<th>{inline(c)}</th>' for c in cells)
                html.append('</tr></thead><tbody>')
                in_table = True
            elif not re.match(r'^[\s\-:|]+$', stripped):
                html.append('<tr>')
                html.extend(f'<td>{inline(c)}</td>' for c in cells)
                html.append('</tr>')
            continue

        if stripped.startswith('- ') or stripped.startswith('* '):
            if in_ol: html.append('</ol>'); in_ol = False
            if not in_ul: html.append('<ul>'); in_ul = True
            html.append(f'<li>{inline(stripped[2:])}</li>')
            continue

        if re.match(r'^\d+\.\s', stripped):
            if in_ul: html.append('</ul>'); in_ul = False
            if not in_ol: html.append('<ol>'); in_ol = True
            html.append(f'<li>{inline(re.sub(r"^\d+\.\s", "", stripped))}</li>')
            continue

        if stripped.startswith('>'):
            html.append(f'<blockquote>{inline(stripped[1:].strip())}</blockquote>')
            continue

        if in_ul: html.append('</ul>'); in_ul = False
        if in_ol: html.append('</ol>'); in_ol = False
        html.append(f'<p>{inline(stripped)}</p>')

    if in_ul: html.append('</ul>')
    if in_ol: html.append('</ol>')
    if in_table: html.append('</tbody></table>')

    return '\n'.join(html)


def inline(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'<([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>', r'<a href="mailto:\1">\1</a>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    docs = []
    for md in DOCS_DIR.glob('*.md'):
        if md.name.lower() == 'readme.md':
            continue
        meta = DOCS_METADATA.get(md.name, {})
        docs.append({
            'id': md.stem.replace('_', '-'),
            'title': meta.get('title', md.stem.replace('_', ' ').title()),
            'order': meta.get('order', 99),
            'content': md.read_text(encoding='utf-8')
        })

    docs.sort(key=lambda x: x['order'])

    tabs = '\n                '.join(
        f'<button class="tab" data-tab="{d["id"]}">{d["title"]}</button>'
        for d in docs
    )

    panels = '\n                '.join(
        f'''<div class="panel" id="{d['id']}">
                    <h1 class="doc-title">{d['title']}</h1>
                    <div class="content">{markdown_to_html(d['content'])}</div>
                </div>'''
        for d in docs
    )

    html = HTML_TEMPLATE.format(site_title=SITE_TITLE, tabs=tabs, panels=panels)

    out = OUTPUT_DIR / 'index.html'
    out.write_text(html, encoding='utf-8')
    print(f"Created: {out}")


if __name__ == '__main__':
    main()
