#!/usr/bin/env python3
"""Inject Just-the-Docs front matter into book chapters.

Idempotent: if front matter already present, it gets replaced (same logic).
Run from repo root: python3 scripts/inject-frontmatter.py

Strategy:
- ZH chapters get full sidebar nav (parent: Part X, nav_order: N).
- EN chapters get a flat title + nav_exclude (still searchable, not in sidebar).
- Top-level pages (preface, glossary, etc.) sit at sidebar root.
- Part stub pages get has_children: true so Just-the-Docs builds the tree.
"""

from pathlib import Path

PARTS = [
    ("part-1", "Part I — 角色与心智",   11),
    ("part-2", "Part II — 客户发现",     12),
    ("part-3", "Part III — 技术选型",    13),
    ("part-4", "Part IV — 工程化落地",   14),
    ("part-5", "Part V — 上线与运营",    15),
    ("part-6", "Part VI — Agent 与 MCP",16),
    ("part-7", "Part VII — 交接与持续",  17),
]

# (filepath_relative_to_root, title, nav_order_within_parent)
CHAPTER_TITLES_ZH = {
    "part-1/intro.md":      ("Part I 引言",                        0),
    "part-1/chapter-01.md": ("第 1 章 FDE 的真实工作流",            1),
    "part-1/chapter-02.md": ("第 2 章 FDE 的心智模型",              2),
    "part-1/chapter-03.md": ("第 3 章 FDE 不是什么",                3),
    "part-2/intro.md":      ("Part II 引言",                       0),
    "part-2/chapter-04.md": ("第 4 章 进客户第一周",                1),
    "part-2/chapter-05.md": ("第 5 章 从需求到 SOW 与评估集",       2),
    "part-3/intro.md":      ("Part III 引言",                      0),
    "part-3/chapter-06.md": ("第 6 章 第一周的技术选型",            1),
    "part-3/chapter-07.md": ("第 7 章 RAG / 微调 / Agent 决策树",   2),
    "part-3/chapter-08.md": ("第 8 章 评估先于代码",                3),
    "part-4/intro.md":      ("Part IV 引言",                       0),
    "part-4/chapter-09.md": ("第 9 章 数据工程",                    1),
    "part-4/chapter-10.md": ("第 10 章 Scaffolding 与开发循环",     2),
    "part-4/chapter-11.md": ("第 11 章 VPC、SSO、合规",             3),
    "part-5/intro.md":      ("Part V 引言",                        0),
    "part-5/chapter-12.md": ("第 12 章 PoC 到生产",                 1),
    "part-5/chapter-13.md": ("第 13 章 监控与 Guardrails",          2),
    "part-6/intro.md":      ("Part VI 引言",                       0),
    "part-6/chapter-14.md": ("第 14 章 Agent Toolset 设计",         1),
    "part-6/chapter-15.md": ("第 15 章 MCP 集成",                   2),
    "part-7/intro.md":      ("Part VII 引言",                      0),
    "part-7/chapter-16.md": ("第 16 章 项目交接",                   1),
    "part-7/chapter-17.md": ("第 17 章 FDE 的下一步",               2),
}

# (filepath, title, top-level nav_order, optional extra fields)
TOP_LEVEL_ZH = [
    ("preface.md",        "前言",       1,  {}),
    ("reading-guide.md",  "阅读指南",   2,  {}),
    ("glossary.md",       "术语表",     90, {}),
    ("bibliography.md",   "参考文献",   91, {}),
]

# Appendix gets its own parent group
APPENDIX_ZH = [
    ("appendix/appendix-a.md", "附录 A 工具栈速查", 1),
    ("appendix/appendix-b.md", "附录 B 比较矩阵",   2),
    ("appendix/appendix-c.md", "附录 C 评估集模板", 3),
    ("appendix/appendix-d.md", "附录 D 客户启动包", 4),
]


def write_frontmatter(filepath: Path, fm: dict) -> None:
    text = filepath.read_text(encoding="utf-8")

    # Strip any existing front matter
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            text = text[end + 5:].lstrip("\n")

    fm_lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, bool):
            fm_lines.append(f'{k}: {"true" if v else "false"}')
        elif isinstance(v, str):
            fm_lines.append(f'{k}: "{v}"')
        else:
            fm_lines.append(f'{k}: {v}')
    fm_lines.append("---")
    fm_block = "\n".join(fm_lines) + "\n\n"

    filepath.write_text(fm_block + text, encoding="utf-8")
    print(f"  {filepath.relative_to(filepath.parents[2] if 'appendix' in str(filepath) or any(p in str(filepath) for p in ['part-', 'en/']) else filepath.parent.parent if filepath.parent.name != filepath.parents[1].name else filepath.parent)}")


def main() -> None:
    root = Path(__file__).resolve().parent.parent

    # ZH top-level
    print("ZH top-level:")
    for rel, title, order, extra in TOP_LEVEL_ZH:
        fp = root / rel
        if not fp.exists():
            print(f"  SKIP missing: {rel}")
            continue
        fm = {"title": title, "nav_order": order}
        fm.update(extra)
        write_frontmatter(fp, fm)

    # ZH parts and chapters
    print("ZH parts and chapters:")
    for part_folder, part_title, part_order in PARTS:
        # Part stub doesn't exist as its own file. Just-the-Docs needs a
        # "parent" with has_children. We use the part's intro.md as the parent
        # by giving it has_children: true and using its title as the parent
        # value for chapters.
        intro_path = root / part_folder / "intro.md"
        if intro_path.exists():
            write_frontmatter(intro_path, {
                "title": part_title,
                "nav_order": part_order,
                "has_children": True,
            })

        for rel, (title, sub_order) in CHAPTER_TITLES_ZH.items():
            if not rel.startswith(part_folder + "/"):
                continue
            if rel.endswith("intro.md"):
                continue  # already wrote it above
            fp = root / rel
            if not fp.exists():
                print(f"  SKIP missing: {rel}")
                continue
            write_frontmatter(fp, {
                "title": title,
                "parent": part_title,
                "nav_order": sub_order,
            })

    # ZH appendix — needs a stub page
    print("ZH appendix:")
    appendix_index = root / "appendix" / "index.md"
    appendix_index.write_text(
        '---\ntitle: "附录"\nnav_order: 80\nhas_children: true\n---\n\n# 附录\n\n四份可复用的工程模板。\n',
        encoding="utf-8",
    )
    print(f"  appendix/index.md")
    for rel, title, order in APPENDIX_ZH:
        fp = root / rel
        if not fp.exists():
            print(f"  SKIP missing: {rel}")
            continue
        write_frontmatter(fp, {
            "title": title,
            "parent": "附录",
            "nav_order": order,
        })

    # EN: every page gets nav_exclude (kept out of ZH sidebar) but still
    # searchable. EN landing page is en/preface.md, reachable from the
    # root index.md.
    print("EN: hide all from ZH sidebar:")
    en_root = root / "en"
    if en_root.exists():
        for md in en_root.rglob("*.md"):
            if md.name == "SUMMARY.md":
                continue
            text = md.read_text(encoding="utf-8")
            if text.startswith("---\n"):
                end = text.find("\n---\n", 4)
                if end != -1:
                    text = text[end + 5:].lstrip("\n")
            stem = md.stem.replace("chapter-", "Ch ")
            md.write_text(
                f'---\ntitle: "{md.parent.name}/{md.name}"\nnav_exclude: true\nsearch_exclude: false\n---\n\n' + text,
                encoding="utf-8",
            )
            print(f"  {md.relative_to(root)}")


if __name__ == "__main__":
    main()
