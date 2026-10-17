#!/usr/bin/env bash
# 建知识库目录树并拷入模板。重复运行是安全的:已存在的文件一律不覆盖。
# 用法:
#   bash init.sh [知识库目录] [领域名...]
#   bash init.sh ~/knowledge-base                    只建骨架
#   bash init.sh ~/knowledge-base ai-tools writing   建骨架并新增两个领域
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TPL="$SKILL_DIR/templates"
KB="${1:-$HOME/knowledge-base}"
[ $# -gt 0 ] && shift
TODAY="$(date +%Y-%m-%d)"

# 只在目标不存在时拷贝;第三个参数非空时替换占位符
put() {
  local src="$1" dst="$2" name="${3:-}"
  if [ -e "$dst" ]; then
    echo "  跳过(已存在) ${dst#$KB/}"
    return
  fi
  sed -e "s/__TODAY__/$TODAY/g" -e "s/__DOMAIN_NAME__/$name/g" "$src" > "$dst"
  echo "  新建 ${dst#$KB/}"
}

echo "知识库目录:$KB"
mkdir -p "$KB"/{domains,inbox,docs,_template,scripts}

put "$TPL/CLAUDE.md"          "$KB/CLAUDE.md"
put "$TPL/decision-log.md"    "$KB/docs/decision-log.md"
put "$TPL/DOMAIN.md"          "$KB/_template/DOMAIN.md"   "<NAME>"
put "$TPL/raw-frontmatter.md" "$KB/_template/raw-frontmatter.md"
put "$TPL/wiki-page.md"       "$KB/_template/wiki-page.md"
put "$SKILL_DIR/scripts/kb-lint.py" "$KB/scripts/kb-lint.py"
touch "$KB/inbox/.gitkeep"

for d in "$@"; do
  if ! [[ "$d" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
    echo "  领域名 \"$d\" 不合规:只能用小写英文、数字和连字符,如 ai-tools" >&2
    exit 1
  fi
  mkdir -p "$KB/domains/$d/raw/inbox" "$KB/domains/$d/wiki/synthesis"
  touch "$KB/domains/$d/raw/inbox/.gitkeep" "$KB/domains/$d/wiki/synthesis/.gitkeep"
  put "$TPL/DOMAIN.md" "$KB/domains/$d/DOMAIN.md" "$d"
done

echo "完成。体检:python3 \"$KB/scripts/kb-lint.py\" --root \"$KB\""
