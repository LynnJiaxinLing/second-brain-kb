---
name: second-brain-kb
license: MIT
github: https://github.com/hey-lynn/second-brain-kb
description:
  给 AI 搭一个「第二大脑」知识库:你只管收藏和发链接,读、转录、原样存档、整理成带来源的结论都由 AI 完成。
  触发场景:用户说「建知识库」「初始化知识库」「落库」「存进知识库」「扔进 KB」,发来小红书/推特/YouTube/B站/网页/PDF 链接要求收录,
  说「编译」「整理知识库」「把原料整理成结论」,问「我之前存过什么关于 X」「X 问题怎么解决」并且已有知识库,
  要求出研究报告/brief/学习大纲,或做出值得记录的结构性决定(「以后都按 A 来」「这个规则改掉」)。
metadata:
  author: Lynn
  version: "1.0.0"
---

# second-brain-kb

一句话:**人只判断「这条要不要让 AI 学」,其余全部交给 AI。**

知识库分两层:
- **raw(原料)**:原文、逐字稿,一个字不改,开头写来源和日期。像毛坯房,原样留着。
- **wiki(结论)**:从原料整理出的结论页,每句话都标出自哪份原料。像精装,在毛坯上做。

另有一本 **decision-log(决策日志)**,记用户定过的规矩,AI 不许偷偷推翻。

本 skill 有四个场景:init(建库)、ingest(落库)、compile(编译)、query/decide(查询与决策)。先定位知识库,再按场景执行。

## 第 0 步:定位知识库(每个场景都先做)

1. 用户指定了路径就用用户的。否则检查 `~/knowledge-base/CLAUDE.md` 是否存在且含 `second-brain-kb` 字样。
2. 找到了:按顺序读 `<KB>/docs/decision-log.md` 和 `<KB>/CLAUDE.md`,再进场景。这两份文件的规则优先于本 skill 的默认值。
3. 没找到:用户要的是建库就走 init;否则问用户一句「知识库在哪个目录?还没建的话我现在帮你建」。

下文 `<KB>` 指知识库根目录,`<SKILL>` 指本 skill 所在目录(`${CLAUDE_SKILL_DIR}`,未设置时通常是 `~/.claude/skills/second-brain-kb`)。

## 依赖检测(用到哪样查哪样,不要假设已装)

缺什么就告诉用户一行安装命令,请他确认后再装。不要一次性把全部依赖都装上。

| 用途 | 检测 | 没装时给用户的一行命令 |
|---|---|---|
| 网页/PDF 转正文 | `command -v markitdown` | `pip install 'markitdown[all]'` |
| 下载视频音频 | `command -v yt-dlp` | `pip install -U yt-dlp`(Mac 也可 `brew install yt-dlp`) |
| 抽音频 | `command -v ffmpeg` | Mac:`brew install ffmpeg`;Ubuntu:`sudo apt install ffmpeg`;Windows:`winget install ffmpeg` |
| 本地转录(Apple 芯片,`uname -sm` 为 `Darwin arm64`) | `command -v mlx_whisper` | `pip install mlx-whisper` |
| 本地转录(其他电脑) | `python3 -c "import faster_whisper"` | `pip install faster-whisper`(备选 `pip install openai-whisper`) |
| 读需要登录的站 | `ls ~/.claude/skills/web-access/SKILL.md` | 让用户对 AI 说:「帮我安装这个 skill:https://github.com/eze-is/web-access」 |
| 体检脚本 | `python3 --version` | 到 python.org 装 Python 3.8+ |

Jina Reader(`https://r.jina.ai/<网址>`)不用安装,curl 即可,但会把网址发给第三方服务,私密链接不要用。

## 场景一:init(用户说「建知识库」)

1. 确认目录:用户没说就用 `~/knowledge-base`。目录已存在且非空时,先列出里面有什么,问用户是否在此基础上建(init.sh 不覆盖已有文件,但要让用户知道)。
2. 运行:
   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/init.sh" ~/knowledge-base
   ```
   它会建好 `domains/ inbox/ docs/ _template/ scripts/`,拷入 `CLAUDE.md`、决策日志、模板和体检脚本。
3. 问用户**一个问题**:「你最想让 AI 帮你积累的 2 到 3 个领域是什么?比如 AI 工具、写作、投资。」
   - 用户说不上来,就建议从最近收藏最多的两类内容起步,并说明以后随时能加。
4. 拿到领域名后,转成英文 kebab-case 短名(如「AI 工具」→ `ai-tools`),再跑一次:
   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/init.sh" ~/knowledge-base ai-tools writing
   ```
   每个领域会得到 `raw/inbox/`、`wiki/synthesis/` 和一份 `DOMAIN.md`。
5. 把每个领域的 `DOMAIN.md` 的「范围」一节按用户原话填两三行;一级分类和查询风格先留模板说明,等原料攒起来再填。
6. 在 `docs/decision-log.md` 的 D-001 上方追加 D-002:「D-002 | 今天日期 | 初始领域为 X、Y | 用户选定 | 某领域三个月内少于 5 份原料就合并或删除」。
7. 跑体检 `python3 <KB>/scripts/kb-lint.py --root <KB>`,应显示 0 个问题。
8. 告诉用户:目录建在哪;以后刷到好内容,把链接发给你说「落库」就行;可选一步,在自己的全局说明文件(Claude Code 是 `~/.claude/CLAUDE.md`)加一行「我的知识库在 ~/knowledge-base,涉及知识库的任务用 second-brain-kb skill」,这样以后每个会话都知道去哪找。这一行要用户同意后再加。

## 场景二:ingest(用户发链接或说「落库」)

目标:把一条内容**原样**存进 raw,加五字段标签。**此时不整理、不总结、不进 wiki。**

### 1. 判断来源类型

| 来源 | source_type | 怎么读 |
|---|---|---|
| 普通网页、公众号、博客 | `web` | `markitdown <网址或下载的 html>`;失败或是动态页面就用 `curl -s https://r.jina.ai/<网址>` |
| PDF | `pdf` | `markitdown 文件.pdf`;中文 PDF 可能字间多空格,转完过目 |
| 小红书 | `xhs` | 需要登录,用 web-access 打开已登录的浏览器读正文和评论。没装 web-access 就停下,告诉用户安装方法(见依赖表),不要硬抓 |
| 推特 / X | `tw` | 同上,用 web-access;只读推文文字不够,带视频的必须转录 |
| YouTube | `yt` | 先试字幕,但**自动字幕和人工字幕要分两次取**(见下方「视频一律要有逐字稿」);都没有就走视频转录 |
| B站、抖音等其他视频站 | `video` | 走视频转录 |
| 用户直接贴的文字 | `text` | 直接用 |

公众号页面的图片是懒加载的:先把 `data-src` 填回 `src` 再交给 markitdown,否则图片会变成空链接。转完用正则裁掉页头页尾的固定套话(推荐条、点赞在看、扫码),正文不动。

### 2. 视频一律要有逐字稿(先看字幕,再决定要不要转录)

只要内容主体是视频,**以逐字稿为准,标题和文案不算数**。标题党很常见:一条自称「免费课程」的视频,转录后可能是卖课广告。

逐字稿有两条来路,**先试字幕能省掉下载和转录**,但两种字幕不是一回事,要分开取才知道拿到的是哪种:

```bash
# 自动字幕(平台机器转的,等于逐字稿,可直接用)
yt-dlp --skip-download --write-auto-subs --sub-langs "zh.*,en.*" -o "%(id)s" <网址>
# 人工字幕(作者上传的,可能被删减润色,不能当逐字稿)
yt-dlp --skip-download --write-subs --sub-langs "zh.*,en.*" -o "%(id)s" <网址>
```

- 拿到**自动字幕**:直接当逐字稿存,frontmatter 写 `transcript_source: auto-caption`。
- 只有**人工字幕**:别当逐字稿。它可以用来校正错字,但正文仍要自己转录,或者写明 `transcript_source: human-caption(可能经编辑)`。
- 两个 flag 一起跑只会落一个文件,事后分不清来路,所以分两次。
- 取不到字幕,或者字幕是烧在画面里的(小红书常见),走下面的下音频加转录。
- 只对**你有权获取**的视频做这件事。
- 某些地区直连视频站不通,yt-dlp 要走你自己的代理。

```bash
# 只下音频,选最小的音频流
yt-dlp -f "ba[abr<=64]/ba/worst" -x --audio-format m4a -o "audio.%(ext)s" <网址>
# yt-dlp 下不下来(小红书常见):用浏览器拿到 mp4 地址,带 Referer 下载后抽音频
curl -L -H "Referer: <原帖网址>" -o video.mp4 "<mp4 地址>" && ffmpeg -i video.mp4 -vn -ac 1 -ar 16000 audio.m4a

# 转录:Apple 芯片
mlx_whisper audio.m4a --model mlx-community/whisper-large-v3-turbo --output-format srt --output-dir .
# 转录:其他电脑(faster-whisper)
python3 -c "from faster_whisper import WhisperModel as M; s,_=M('small').transcribe('audio.m4a'); print('\n'.join(x.text for x in s))" > transcript.txt
# 备选:openai-whisper
whisper audio.m4a --model small --output_format srt
```

逐字稿规矩:
- **一个字都不改写、不概括、不翻译**。外语就存外语原文。
- 同音字、符号错误可以对照正文校正,校正处注明。
- 想加结构化整理,另起一节,标题写明「二次整理,以逐字稿为准」。
- 视频没有人声(纯音乐、纯画面)时,用 `ffmpeg -i video.mp4 -vf fps=1/3 frame_%03d.png` 抽帧识别画面文字,并注明用的是抽帧。
- 逐字稿放进 raw 文件的 `## 视频转录` 一节;太长就存成同目录的 `.srt` 文件,frontmatter 加 `transcript_file: <文件名>`。
- 音频、视频、抽帧图是临时文件,转完删掉,不进知识库。

### 3. 写入 raw

- 先 `ls` 目标目录,确认同一链接没存过(用 `grep -rl "<链接>" <KB>/domains/*/raw` 查重)。存过就告诉用户并停下。
- 路径:`<KB>/domains/<领域>/raw/<source_type>/YYYY-MM-DD-<slug>.md`,slug 是英文 kebab-case,6 个词以内。
- 判断不了领域,放 `<KB>/inbox/`,不要硬选,也不要追问用户。
- 文件开头写五字段标签(模板见 `<KB>/_template/raw-frontmatter.md`):
  ```yaml
  ---
  source_url: <抓取用的完整原链接>
  source_type: web
  captured_at: 2026-01-01
  domain: example-domain
  compiled: false
  ---
  ```
  - **值写裸值,不加括号注释**。`note_type: video(30分钟)` 会让以后的搜索失效。
  - `source_url` 原样保留抓取时的完整链接。小红书链接带的 `xsec_token` 参数不能删,删了以后链接会失效、内容取不回来。
  - 视频加 `note_type: video`。可选字段:`author`、`post_date`、`raw_topic_guess`(2 到 3 个关键词)。
- 标签下面放原文。图片里有关键文字的,识别后附在文末 `## 图片转写`。
- **不让用户分类、打标签、写感想。**

### 4. 体检并汇报

```bash
python3 <KB>/scripts/kb-lint.py --root <KB> <刚写的文件>
```
有报错先修再汇报。汇报只要一行:落到哪个文件、`raw_topic_guess` 是什么、是否转录了视频。

### 新分类门槛

不手动分类,不为一条内容新开分类或领域。**同一主题攒到 5 份原料、现有分类都装不下时**,才向用户提议新开分类或领域,用户同意后写进 decision-log。

## 场景三:compile(用户说「编译」「整理知识库」,或 raw 里 compiled: false 的文件攒多了)

1. 列出待编译文件:`grep -rl "^compiled: false" <KB>/domains/*/raw`。
2. 对每个文件:读原文,读该领域 `DOMAIN.md`,在 `wiki/` 里找已有的相关页(按标题和关键词 grep)。
3. 三种处理:
   - **全新主题**:按 `<KB>/_template/wiki-page.md` 新建 `wiki/<分类>/<topic-name>.md`。
   - **已有主题**:在该页 `## Timeline` 段末尾追加一条带日期和来源的记录;新信息改变了结论,就同时改写顶部 `## Compiled truth`。不新建重复页。
   - **重复或噪音**(广告、和已有原料完全重复、没有可用信息):不写 wiki,把 raw 的标签改为 `compiled: skipped`。
4. **每句话都要有来源**。结论页里每一行正文(段落行、列表项、表格数据行)都要带指向 raw 的链接,格式 `[来源](../../raw/web/2026-01-01-example.md)`(按实际相对路径写)。找不到来源的句子不写。多份原料说法冲突时,两种都写,各自标来源,不自己裁决。
5. 写之前先读目标页的当前内容,别覆盖别人(或别的会话)刚写的东西。
6. 编译完成的 raw 改为 `compiled: true`。
7. 跑体检 `python3 <KB>/scripts/kb-lint.py --root <KB>`,全绿再汇报:新建了哪几页、更新了哪几页、跳过了几份。

## 场景四:query / decide

### 查询(用户问「X 怎么解决」「我之前存过什么关于 Y」)

1. 先读 decision-log,再读对应领域的 `DOMAIN.md`,按其中「查询风格」回答。
2. **先读 wiki 相关页,再按需打开 raw**。wiki 没有覆盖到的,明说「知识库里没有」,再问是否联网补充;联网查到的内容不冒充知识库内容。
3. 默认三段式回答:①问题本质 ②有哪几类解法 ③每类对应的具体工具或做法。每条结论带 wiki 页或 raw 文件的路径。
4. 末尾列出值得读原文的 2 到 3 份 raw。
5. 用户要研究报告时,先问档位:Brief(5 分钟读,3 到 5 条核心观点)/ Report(20 分钟读,完整对比和空白点)/ Syllabus(5 到 10 节的学习路径)。写完存进该领域 `wiki/synthesis/`,同样每句带来源。

### 决策(用户定规矩、改规矩)

1. 出现以下信号时,问用户一句「这条要记进决策日志吗?」:选了 A 不选 B、引入新规则、改掉以前的规则、接受一个明确的取舍。小事不要提。
2. 用户同意后,按 `<KB>/docs/decision-log.md` 顶部的格式,写在最上面,编号接着当前最大号。写前先读文件头确认最大编号。
3. **冲突先反驳**:用户的新要求和决策日志里已有的某条冲突时,先引用那条原文(编号、日期、作废条件),问用户是改判还是这次例外。用户确认改判,就写一条新决策注明「推翻 D-xxx」,旧条目不删。不要默默照做,也不要默默拒绝。

## 不做的事

- 不存 AI 的总结冒充原料。原料必须是原文或逐字稿,总结只能进 wiki。
- 不在落库时顺手编译。
- 不要求用户分类、打标签、写读后感。
- 不把账号密码、私人证件、聊天记录里的他人隐私存进知识库。
- 小红书、推特等站点对自动操作查得严,有封号风险。只做读收藏夹、读单条这类小量操作,大批量抓取前先提醒用户。
