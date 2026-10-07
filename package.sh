#!/usr/bin/env bash
# Rebuild the uploadable archives in dist/ from skills/ and gemini-gems/.
#   dist/claude/<name>.skill       Claude skill (also ChatGPT)
#   dist/claude/<name>-gem.skill   Gem wrapped as a Claude skill
#   dist/copilot/<name>.zip        Copilot
#   dist/gemini/<name>.skill or <name>-gem.zip   Gemini
set -euo pipefail
cd "$(dirname "$0")"
rm -rf dist && mkdir -p dist/claude dist/copilot dist/gemini
build=$(mktemp -d); trap 'rm -rf "$build"' EXIT

for dir in skills/*/; do
  name=$(basename "$dir")
  (cd skills && zip -qrX "../dist/claude/$name.skill" "$name" -x '*.DS_Store' '*__pycache__*')
  cp "dist/claude/$name.skill" "dist/copilot/$name.zip"
  [ -d "gemini-gems/$name" ] || cp "dist/claude/$name.skill" "dist/gemini/$name.skill"
done

for dir in gemini-gems/*/; do
  name=$(basename "$dir")
  (cd "$dir" && zip -qrX "$OLDPWD/dist/gemini/$name-gem.zip" "$name.md" engine.html)
  out="$build/$name-gem"; mkdir -p "$out"
  cat "$dir/claude-frontmatter.md" "$dir/$name.md" > "$out/SKILL.md"
  cp "$dir/engine.html" "$out/"
  (cd "$build" && zip -qrX "$OLDPWD/dist/claude/$name-gem.skill" "$name-gem")
done

ls -1 dist/*/
