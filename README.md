# Lex Fridman Podcast — 中文精读 TTS 版

Lex Fridman 播客 AI 中文语音版，通过 Apple Podcasts 私人电台订阅。

**订阅地址（RSS）**: `https://goutou08.github.io/lex-fridman-podcast/feed.xml`

## 如何订阅

### iPhone / iPad
1. 打开**播客** app
2. 点击右上角头像 → **设置** → **添加节目**
3. 粘贴上面的 RSS 地址
4. 搜索"Lex Fridman 中文"确认订阅

### Mac
1. 打开**播客** app
2. 文件 → **添加节目** → 粘贴 RSS 地址

## 内容说明

- 每期是从 Lex Fridman 播客英文原文提取核心议题
- 由 AI 生成中文精读 TTS 音频（edge-tts，语速-15%）
- 由 Hermes Agent 自动化制作

## 文件结构

```
lex-fridman-podcast/
├── feed.xml              ← RSS feed（Apple Podcasts 订阅用）
├── episodes/             ← MP3 音频文件
│   ├── 495-lars-brownworth.mp3
│   ├── 494-jensen-huang.mp3
│   └── ...
└── generate_feed.py      ← RSS 生成脚本
```

## 手动更新 feed

```bash
python generate_feed.py --base-url https://goutou08.github.io/lex-fridman-podcast
git add -A && git commit -m "Update feed" && git push
```

GitHub Pages 会自动从 `main` 分支的 `/` 根目录发布，约 1-2 分钟后生效。
