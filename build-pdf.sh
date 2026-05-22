#!/bin/bash
# Build Chinese and English PDFs from FDE Book markdown files.
# Mirrors openbook/build-pdf.sh but renamed for FDE Book output.
set -uo pipefail

BOOK_DIR="/home/ubuntu/workspace/fde-book"
cd "$BOOK_DIR"

build_pdf() {
  local lang="$1"
  local output="$2"
  local src_dir="$3"
  local title="$4"

  echo "=== Building $lang PDF ==="

  local files=()

  # Front matter
  [ -f "$src_dir/preface.md" ] && files+=("$src_dir/preface.md")
  [ -f "$src_dir/reading-guide.md" ] && files+=("$src_dir/reading-guide.md")

  # Parts 1-8
  for p in 1 2 3 4 5 6 7 8; do
    local part_dir="$src_dir/part-$p"
    [ -d "$part_dir" ] || continue
    [ -f "$part_dir/intro.md" ] && files+=("$part_dir/intro.md")
    for ch in "$part_dir"/chapter-*.md; do
      [ -f "$ch" ] && files+=("$ch")
    done
  done

  # Appendices
  for ap in a b c d; do
    local ap_file="$src_dir/appendix/appendix-$ap.md"
    [ -f "$ap_file" ] && files+=("$ap_file")
  done

  # Back matter
  [ -f "$src_dir/glossary.md" ] && files+=("$src_dir/glossary.md")
  [ -f "$src_dir/bibliography.md" ] && files+=("$src_dir/bibliography.md")

  echo "  Files: ${#files[@]}"

  local combined="/tmp/fdebook-${lang}-combined.md"
  echo "% $title" > "$combined"
  echo "" >> "$combined"

  for f in "${files[@]}"; do
    cat "$f" >> "$combined"
    echo "" >> "$combined"
    echo "\\newpage" >> "$combined"
    echo "" >> "$combined"
  done

  # Strip HTML helpers that pandoc handles awkwardly
  sed -i '/<div id="backlink-home">/,/<\/div>/d' "$combined"
  sed -i '/← 返回目录/d' "$combined"
  sed -i '/← Back to Contents/d' "$combined"
  sed -i '/<p align="center">/,/<\/p>/d' "$combined"

  pandoc "$combined" \
    -o "$output" \
    --pdf-engine=xelatex \
    -V geometry:margin=2.5cm \
    -V fontsize=11pt \
    -V documentclass=report \
    -V mainfont="Noto Serif CJK SC" \
    -V sansfont="Noto Serif CJK SC" \
    -V monofont="DejaVu Sans Mono" \
    -V CJKmainfont="Noto Serif CJK SC" \
    --toc \
    --toc-depth=2 \
    -V colorlinks=true \
    -V linkcolor=blue \
    -V urlcolor=blue \
    --highlight-style=tango \
    2>&1

  if [ -f "$output" ]; then
    local size=$(du -h "$output" | cut -f1)
    echo "  Done: $output ($size)"
  else
    echo "  FAILED!"
    return 1
  fi
}

build_pdf "zh" "$BOOK_DIR/OpenBook-FDE-zh.pdf" "$BOOK_DIR" "OpenBook · Forward Deployed Engineer — AI 应用的落地工程学"
build_pdf "en" "$BOOK_DIR/OpenBook-FDE-en.pdf" "$BOOK_DIR/en" "OpenBook · Forward Deployed Engineer — A Field Manual for AI Deployment"

echo ""
echo "=== Done ==="
ls -lh "$BOOK_DIR"/OpenBook-FDE-*.pdf 2>/dev/null
