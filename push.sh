#!/bin/bash
# Push workflow: init git (if needed), add all files, commit, push to GitHub
# Usage: ./push.sh <GH_TOKEN>
#
# This script is meant to be run manually after Terry provides a valid GH_TOKEN.
# It will:
#   1. Initialize local git repo (first time only)
#   2. Set up remote using the provided token
#   3. Create the GitHub repo via API (first time only)
#   4. Push to main branch
#   5. Enable GitHub Pages (Settings → Pages → main branch)

set -e

TOKEN="${1:-${GH_TOKEN}}"
REPO="lex-fridman-podcast"
USER="goutou08"
DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$TOKEN" ]; then
    echo "ERROR: No GH_TOKEN provided. Usage: $0 <gh_token>"
    exit 1
fi

echo "=== Checking GitHub API access ==="
AUTH_CHECK=$(curl -s -H "Authorization: token $TOKEN" https://api.github.com/user)
LOGIN=$(echo "$AUTH_CHECK" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('login','ERROR'))" 2>/dev/null)
if [ "$LOGIN" = "ERROR" ]; then
    echo "ERROR: Invalid GH_TOKEN (bad credentials)"
    echo "$AUTH_CHECK"
    exit 1
fi
echo "Authenticated as: $LOGIN"

cd "$DIR"

echo "=== Initializing git ==="
git config user.name "Hermes Agent" 2>/dev/null || true
git config user.email "hermes@agent.local" 2>/dev/null || true
# Workaround: environment may not support HTTP/2, force HTTP/1.1
git config http.version HTTP/1.1

if [ ! -d ".git" ]; then
    git init
    git checkout -b main
fi

echo "=== Checking if repo exists ==="
REPO_CHECK=$(curl -s -H "Authorization: token $TOKEN" "https://api.github.com/repos/${USER}/${REPO}")
if echo "$REPO_CHECK" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('full_name') else 1)" 2>/dev/null; then
    echo "Repo ${USER}/${REPO} already exists"
else
    echo "Creating repo ${USER}/${REPO} on GitHub..."
    CREATE_RESP=$(curl -s -X POST -H "Authorization: token $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"name":"'"$REPO"'","description":"Lex Fridman Podcast 中文精读 TTS 版 — AI 语音播客","private":false}' \
        "https://api.github.com/user/repos")
    echo "Repo created: $CREATE_RESP"
fi

echo "=== Committing files ==="
git add -A
COMMIT_MSG="Initial commit: 13 episodes, generate_feed.py, feed.xml"
if git diff --cached --quiet; then
    echo "Nothing to commit"
else
    git commit -m "$COMMIT_MSG"
fi

echo "=== Setting remote ==="
git remote set-url origin "https://${USER}:${TOKEN}@github.com/${USER}/${REPO}.git"
git remote -v

echo "=== Pushing to GitHub ==="
git push -u origin main --force

echo "=== Enabling GitHub Pages ==="
sleep 2
PAGES_RESP=$(curl -s -X PUT -H "Authorization: token $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"source":{"branch":"main","path":"/"}}' \
    "https://api.github.com/repos/${USER}/${REPO}/pages")
echo "Pages setup: $PAGES_RESP"

echo ""
echo "=== DONE ==="
echo "Feed URL: https://${USER}.github.io/${REPO}/feed.xml"
echo "Podcast RSS: https://${USER}.github.io/${REPO}/feed.xml"
echo ""
echo "订阅步骤：iPhone 播客 app → 添加节目 → 粘贴上方 RSS 地址"
