#!/usr/bin/env bash
# Rebuild the uploadable archives in dist/ from the skill folders.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p dist/claude dist/copilot dist/gemini
for dir in skills/*/; do
  name=$(basename "$dir")
  rm -f "dist/claude/$name.skill" "dist/copilot/$name.zip"
  (cd skills && zip -qrX "../dist/claude/$name.skill" "$name" -x '*.DS_Store')
  cp "dist/claude/$name.skill" "dist/copilot/$name.zip"
  if [ -d "gemini-gems/$name" ]; then
    rm -f "dist/gemini/$name-gem.zip"
    (cd "gemini-gems/$name" && zip -qrX "../../dist/gemini/$name-gem.zip" . -x '*.DS_Store')
  else
    cp "dist/claude/$name.skill" "dist/gemini/$name.skill"
  fi
done
echo "Archives written to dist/"
