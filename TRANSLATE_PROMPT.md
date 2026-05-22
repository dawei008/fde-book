Translate FDE Book from Chinese to English.

Source: ./ (Chinese originals — DO NOT modify)
Target: ./en/ (English translations)

RULES:
- Mirror the source directory under en/.
- Keep all Markdown formatting, ASCII boxes, tables, links.
- Keep technical terms in English: FDE, PoC, GTM, RAG, MCP, Eval, Ontology, SSO, SCIM, VPC, Agent, Toolset.
- Professional technical English, not machine-translation style.
- Fix en/ internal links to point within en/ (e.g., en/preface.md → en/reading-guide.md).
- Code samples / tables / matrices — translate the prose around them; keep the code identifiers and table cells in English.
- Each iteration: translate up to 5 files, then review and commit.

PROGRESS CHECK:
Run: find ./en -name "*.md" 2>/dev/null | wc -l
Target: 33 files total

FILE LIST (33 files):
README.md, preface.md, reading-guide.md, glossary.md, bibliography.md,
part-1/intro.md, part-1/chapter-01.md, part-1/chapter-02.md, part-1/chapter-03.md,
part-2/intro.md, part-2/chapter-04.md, part-2/chapter-05.md,
part-3/intro.md, part-3/chapter-06.md, part-3/chapter-07.md, part-3/chapter-08.md,
part-4/intro.md, part-4/chapter-09.md, part-4/chapter-10.md, part-4/chapter-11.md,
part-5/intro.md, part-5/chapter-12.md, part-5/chapter-13.md,
part-6/intro.md, part-6/chapter-14.md, part-6/chapter-15.md,
part-7/intro.md, part-7/chapter-16.md, part-7/chapter-17.md,
appendix/appendix-a.md, appendix/appendix-b.md, appendix/appendix-c.md, appendix/appendix-d.md

DONE CONDITION:
When all 33 files exist in en/ and are reviewed, output:
<promise>TRANSLATION COMPLETE</promise>
