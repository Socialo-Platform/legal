#!/usr/bin/env python3
"""
Generate a multi-language static website with vertical tabs from markdown documentation.
Usage: python generate_site.py
Output: Creates 'site/index.html'

Structure:
  en/*.md  - English documents
  es/*.md  - Spanish documents

Frontmatter support:
  ---
  signed_by_client: true
  ---
  # Document content...
"""

import re
from pathlib import Path


def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content.
    Returns (frontmatter_dict, content_without_frontmatter)
    """
    frontmatter = {}
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            # Parse simple YAML (key: value pairs)
            for line in parts[1].strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    # Parse boolean
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    frontmatter[key] = value
            content = parts[2].strip()
    return frontmatter, content

DOCS_DIR = Path(__file__).parent
OUTPUT_DIR = DOCS_DIR / "site"
SITE_TITLE = "Socialo Legal"

# Language configuration
LANGUAGES = {
    "en": {"name": "English", "flag": "EN"},
    "es": {"name": "Español", "flag": "ES"},
}

DEFAULT_LANG = "es"  # Fallback if browser language not supported

# Document metadata per language
# Key is the filename stem (without .md), maps to display title and sort order
DOCS_METADATA = {
    "en": {
        "terms_and_conditions": {"title": "Terms and Conditions", "order": 1},
        "privacy_policy": {"title": "Privacy Policy", "order": 2},
        "cookie_policy": {"title": "Cookie Policy", "order": 3},
        "standard_contract": {"title": "Subscription Contract", "order": 4},
        "data_processing_agreement": {"title": "Data Processing Agreement", "order": 5},
        "subprocessors": {"title": "Subprocessors", "order": 6},
    },
    "es": {
        "terms_and_conditions": {"title": "Términos y Condiciones", "order": 1},
        "privacy_policy": {"title": "Política de Privacidad", "order": 2},
        "politica_cookies": {"title": "Política de Cookies", "order": 3},
        "standard_contract": {"title": "Contrato de Suscripción", "order": 4},
        "data_processing_agreement": {"title": "Contrato de Tratamiento de Datos", "order": 5},
        "subprocessors": {"title": "Subencargados", "order": 6},
    },
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

        /* Language Switcher */
        .lang-switcher {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
        }}

        .lang-select {{
            width: 100%;
            padding: 0.6rem 0.75rem;
            font-size: 0.85rem;
            font-family: inherit;
            color: var(--text);
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 4px;
            cursor: pointer;
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23555' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 0.75rem center;
        }}

        .lang-select:focus {{
            outline: none;
            border-color: var(--text-light);
        }}

        [data-theme="dark"] .lang-select {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23999' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
        }}

        .tabs {{
            flex: 1;
            overflow-y: auto;
            padding: 1rem 0;
        }}

        .tab {{
            display: none;
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

        .tab.visible {{
            display: block;
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

        .tab.signed {{
            padding-right: 0.5rem;
        }}

        .signed-icon {{
            margin-left: 0.5rem;
            font-size: 0.85rem;
            opacity: 0.6;
        }}

        .signed-badge {{
            display: inline-block;
            font-size: 0.7rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            padding: 0.25rem 0.5rem;
            margin-left: 0.75rem;
            background: var(--bg-alt);
            border: 1px solid var(--border);
            border-radius: 3px;
            color: var(--text-light);
            vertical-align: middle;
        }}

        .tab-divider {{
            display: none;
            padding: 1rem 1.5rem 0.5rem;
            margin-top: 0.25rem;
        }}

        .tab-divider.visible {{
            display: block;
        }}

        .tab-divider span {{
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-light);
            opacity: 0.7;
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

        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-light);
        }}

        .empty-state p {{
            margin-bottom: 0.5rem;
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

        .mobile-controls {{
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }}

        .mobile-lang {{
            font-size: 0.75rem;
            font-family: inherit;
            padding: 0.4rem 0.5rem;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--text);
            cursor: pointer;
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
        <div class="mobile-controls">
            <select class="mobile-lang" id="mobileLangSelect" onchange="setLang(this.value)">
                {lang_options}
            </select>
            <button class="menu-btn" onclick="toggleSidebar()">
                <span></span><span></span><span></span>
            </button>
        </div>
    </div>

    <div class="layout">
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <div class="logo">{site_title}</div>
                <div class="tagline">Legal Documentation</div>
            </div>

            <div class="lang-switcher">
                <select class="lang-select" id="langSelect" onchange="setLang(this.value)">
                    {lang_options}
                </select>
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

                <div class="panel empty-state" id="empty-state">
                    <p><strong>No documents available</strong></p>
                    <p>Documents for this language have not been added yet.</p>
                </div>
            </div>

            <footer>
                Socialo, S.L. &copy; 2026 &middot;
                <a href="mailto:info@socialo.live">info@socialo.live</a> &middot;
                <a href="mailto:dpo@socialo.live">dpo@socialo.live</a>
            </footer>
        </div>
    </div>

    <script>
        const LANGS = {langs_json};
        const DEFAULT_LANG = '{default_lang}';

        const tabs = document.querySelectorAll('.tab');
        const panels = document.querySelectorAll('.panel:not(.empty-state)');
        const dividers = document.querySelectorAll('.tab-divider');
        const langSelect = document.getElementById('langSelect');
        const mobileLangSelect = document.getElementById('mobileLangSelect');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        const emptyState = document.getElementById('empty-state');

        let currentLang = DEFAULT_LANG;
        let currentTab = null;

        function getBrowserLang() {{
            const lang = navigator.language.slice(0, 2).toLowerCase();
            return LANGS.includes(lang) ? lang : DEFAULT_LANG;
        }}

        function setLang(lang) {{
            currentLang = lang;
            localStorage.setItem('lang', lang);

            // Update select dropdowns
            langSelect.value = lang;
            mobileLangSelect.value = lang;

            // Show/hide tabs and dividers for this language
            let firstVisibleTab = null;
            tabs.forEach(t => {{
                const isVisible = t.dataset.lang === lang;
                t.classList.toggle('visible', isVisible);
                if (isVisible && !firstVisibleTab) firstVisibleTab = t;
            }});

            dividers.forEach(d => {{
                d.classList.toggle('visible', d.dataset.lang === lang);
            }});

            // If current tab is not in this language, switch to first available
            const currentTabElement = currentTab ? document.querySelector(`.tab[data-tab="${{currentTab}}"]`) : null;
            if (!currentTabElement || currentTabElement.dataset.lang !== lang) {{
                if (firstVisibleTab) {{
                    showTab(firstVisibleTab.dataset.tab);
                }} else {{
                    // No docs for this language
                    panels.forEach(p => p.classList.remove('active'));
                    tabs.forEach(t => t.classList.remove('active'));
                    emptyState.classList.add('active');
                    currentTab = null;
                }}
            }}

            closeSidebar();
        }}

        function showTab(id) {{
            currentTab = id;
            localStorage.setItem('activeTab', id);

            tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === id));
            panels.forEach(p => p.classList.toggle('active', p.id === id));
            emptyState.classList.remove('active');

            closeSidebar();
        }}

        tabs.forEach(t => t.addEventListener('click', () => showTab(t.dataset.tab)));

        // Initialize language
        const savedLang = localStorage.getItem('lang');
        if (savedLang && LANGS.includes(savedLang)) {{
            setLang(savedLang);
        }} else {{
            setLang(getBrowserLang());
        }}

        // Restore tab if saved and matches current language
        const savedTab = localStorage.getItem('activeTab');
        if (savedTab) {{
            const tabEl = document.querySelector(`.tab[data-tab="${{savedTab}}"]`);
            if (tabEl && tabEl.dataset.lang === currentLang) {{
                showTab(savedTab);
            }}
        }}

        // Theme
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

        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {{
            document.documentElement.setAttribute('data-theme', savedTheme);
        }}

        // Mobile sidebar
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

    all_docs = []
    available_langs = []

    # Scan each language folder
    for lang_code, lang_info in LANGUAGES.items():
        lang_dir = DOCS_DIR / lang_code
        if not lang_dir.exists():
            continue

        available_langs.append(lang_code)
        lang_metadata = DOCS_METADATA.get(lang_code, {})

        for md in lang_dir.glob('*.md'):
            if md.name.lower() == 'readme.md':
                continue

            stem = md.stem
            meta = lang_metadata.get(stem, {})

            raw_content = md.read_text(encoding='utf-8')
            frontmatter, content = parse_frontmatter(raw_content)

            # Title priority: frontmatter > DOCS_METADATA > filename
            title = frontmatter.get('title') or meta.get('title') or stem.replace('_', ' ').title()
            # Order priority: frontmatter > DOCS_METADATA > 99
            order = frontmatter.get('order') or meta.get('order') or 99
            signed = frontmatter.get('signed_by_client', False)

            all_docs.append({
                'id': f'{lang_code}-{stem}',
                'lang': lang_code,
                'title': title,
                'order': order,
                'content': content,
                'signed': signed
            })

    # Sort by language then order
    all_docs.sort(key=lambda x: (x['lang'], x['order']))

    # Generate language options for dropdown
    lang_options = '\n                '.join(
        f'<option value="{code}">{info["name"]}</option>'
        for code, info in LANGUAGES.items()
        if code in available_langs
    )

    # Generate tabs (all languages, JS will show/hide) with section dividers
    def make_tab(d):
        signed_class = ' signed' if d['signed'] else ''
        return f'<button class="tab{signed_class}" data-tab="{d["id"]}" data-lang="{d["lang"]}">{d["title"]}</button>'

    # Group docs by language, then split into unsigned and signed
    tabs_html = []
    for lang_code in available_langs:
        lang_docs = [d for d in all_docs if d['lang'] == lang_code]
        unsigned = [d for d in lang_docs if not d['signed']]
        signed = [d for d in lang_docs if d['signed']]

        for d in unsigned:
            tabs_html.append(make_tab(d))

        if signed:
            # Add section divider for signed documents
            tabs_html.append(f'<div class="tab-divider" data-lang="{lang_code}"><span>Contracts</span></div>')
            for d in signed:
                tabs_html.append(make_tab(d))

    tabs = '\n                '.join(tabs_html)

    # Generate panels
    def make_panel(d):
        signed_badge = '<span class="signed-badge">Requires client signature</span>' if d['signed'] else ''
        return f'''<div class="panel" id="{d['id']}">
                    <h1 class="doc-title">{d['title']}{signed_badge}</h1>
                    <div class="content">{markdown_to_html(d['content'])}</div>
                </div>'''

    panels = '\n                '.join(make_panel(d) for d in all_docs
    )

    # Generate HTML
    html = HTML_TEMPLATE.format(
        site_title=SITE_TITLE,
        lang_options=lang_options,
        tabs=tabs,
        panels=panels,
        langs_json=str(available_langs).replace("'", '"'),
        default_lang=DEFAULT_LANG
    )

    out = OUTPUT_DIR / 'index.html'
    out.write_text(html, encoding='utf-8')

    print(f"Created: {out}")
    print(f"Languages: {', '.join(available_langs)}")
    print(f"Documents: {len(all_docs)}")


if __name__ == '__main__':
    main()
