# 原料标签模板

> 每份 raw 文件的开头必须是下面这段标签。五个必填字段,值写裸值,不加括号注释。

```yaml
---
source_url: <抓取时用的完整原链接,参数原样保留>
source_type: <web | pdf | xhs | tw | yt | video | text>
captured_at: <YYYY-MM-DD>
domain: <领域名,判断不了写 inbox>
compiled: false
---
```

| 字段 | 必填 | 取值 | 说明 |
|---|---|---|---|
| source_url | 是 | 原链接 | 用户直接贴的文字写 `user-paste` |
| source_type | 是 | 见上 | 决定放进 `raw/<source_type>/` 哪个子目录 |
| captured_at | 是 | YYYY-MM-DD | 落库当天的日期 |
| domain | 是 | 领域名 | 与 `domains/` 下目录名一致 |
| compiled | 是 | `false` / `true` / `skipped` | 新落库写 false;编译后 true;噪音或重复 skipped |
| note_type | 视频必填 | `video` / `normal` | 写了 video 就必须有转录段 |
| transcript_file | 可选 | 文件名 | 逐字稿太长单独存成 .srt 时填 |
| author | 可选 | 作者名 | |
| post_date | 可选 | YYYY-MM-DD | 原内容发布日期 |
| raw_topic_guess | 可选 | 2 到 3 个关键词 | AI 落库时猜的主题,方便日后编译 |

**反例**:`note_type: video(30分钟,有字幕)`。括号注释会让 `grep "note_type: video"` 搜不到它。

## 示例一:网页文章

```markdown
---
source_url: https://example.com/blog/how-to-take-notes
source_type: web
captured_at: 2026-01-01
domain: example-domain
compiled: false
author: Example Author
raw_topic_guess: note-taking, review habit
---

# How to Take Notes

(这里是 markitdown 转出的正文,一字不改)
```

## 示例二:视频

```markdown
---
source_url: https://www.youtube.com/watch?v=EXAMPLE
source_type: yt
captured_at: 2026-01-01
domain: example-domain
compiled: false
note_type: video
raw_topic_guess: example topic
---

# 视频标题原文

## 视频文案

(视频页面上的标题和描述,原样)

## 视频转录

(whisper 逐字稿,不改写不概括;外语保留原文。同音字校正处用〔校正:原为 xxx〕注明)
```
