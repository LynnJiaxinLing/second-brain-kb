# second-brain-kb

**你只管收藏,读、记、存、整理都交给 AI。**

一个给 AI 装上「第二大脑」的技能包(skill)。刷到好内容,把链接发给 AI 说一句「落库」,它自己完成五步:

1. 读帖子或文章
2. 视频转成逐字稿
3. 原样存进原料文件夹,开头写上来源和日期
4. 整理成结论页
5. 结论的每句话都标出自哪份原料

适用于所有支持 SKILL.md 的 AI 编程助手(Claude Code、Cursor、Gemini CLI、Codex CLI 等)。思路来自 Karpathy 公开的做法:把零散资料丢进一个文件夹,让 AI 整理成一本像维基百科那样的知识库。

## 技能包是什么

技能包就是一个文本文件,写着「遇到什么事、按什么步骤做」,放在 AI 固定会看的文件夹里。碰到对应的活,AI 自己去翻。这个技能包就是一份给 AI 的岗位说明书,规定知识库怎么建、怎么存、怎么整理、怎么查。

## 安装

**方式一:让 AI 自己装(推荐)**

对你的 AI 说:

```
帮我安装这个 skill:https://github.com/LynnJiaxinLing/second-brain-kb
```

**方式二:Plugin 安装(Claude Code)**

```bash
claude plugin marketplace add https://github.com/LynnJiaxinLing/second-brain-kb
claude plugin install second-brain-kb@second-brain-kb --scope user
```

**方式三:手动**

```bash
git clone https://github.com/LynnJiaxinLing/second-brain-kb ~/.claude/skills/second-brain-kb
```

## 装完第一句话说什么

```
帮我建一个知识库
```

AI 会在 `~/knowledge-base` 建好目录,然后只问你一个问题:最想积累的 2 到 3 个领域是什么。

之后日常只需要这几句:

| 你说 | AI 做什么 |
|---|---|
| 「落库」+ 链接 | 读内容,视频转逐字稿,原样存进原料,打好来源标签 |
| 「编译一下知识库」 | 把还没整理的原料整理成结论页,每句标来源 |
| 「我之前存过什么关于 X 的?」 | 先查结论,再给你值得读原文的几份原料 |
| 「出一份 X 的研究报告」 | 先问你要 5 分钟版、20 分钟版还是学习大纲,写完存回知识库 |
| 「以后都按 A 来」 | 问你要不要记进决策日志;以后你说的和它冲突,它会先提醒你 |

## 可能需要的工具

不用提前装。AI 用到哪样会先检查,没装就告诉你一行安装命令,你同意了再装。

| 工具 | 干什么 | 什么时候用到 |
|---|---|---|
| [web-access](https://github.com/eze-is/web-access) | 让 AI 用你电脑上已经登录好的浏览器读网页 | 小红书、推特这类不登录看不全的网站 |
| yt-dlp | 把视频里的声音单独下载下来 | 任何视频 |
| whisper(mlx-whisper / faster-whisper) | 装在你自己电脑上的免费转录模型,把声音转成逐字稿 | 任何视频 |
| ffmpeg | 从视频文件里抽出声音 | yt-dlp 下载不下来的时候 |
| markitdown | 把网页、PDF 转成干净的正文 | 文章和 PDF |
| Python 3 | 跑体检脚本 | 每次落库和整理之后 |

## 目录结构

```
~/knowledge-base/
├── CLAUDE.md                 全局规则(六条铁律 + 流程)
├── docs/
│   └── decision-log.md       决策日志:你定过的规矩,AI 不许偷偷推翻
├── inbox/                    AI 判断不了领域的原料先放这里
├── _template/                模板:新领域、原料标签、结论页
├── scripts/
│   └── kb-lint.py            体检脚本:查标签、查来源
└── domains/
    └── example-domain/
        ├── DOMAIN.md         这个领域收什么、怎么分、怎么回答
        ├── raw/              原料(毛坯):原文和逐字稿,一字不改
        │   ├── web/
        │   ├── yt/
        │   └── inbox/
        └── wiki/             结论(精装):每句标来源
            ├── patterns/
            └── synthesis/    研究报告
```

本仓库自身:

```
second-brain-kb/
├── SKILL.md          AI 读这个干活
├── README.md         给人看
├── templates/        建库时拷进知识库的模板
├── scripts/
│   ├── init.sh       一条命令建目录树
│   └── kb-lint.py    体检脚本
└── LICENSE
```

## 六条铁律

1. **五秒入库**:你不用分类、打标签、写感想。
2. **原料一字不改**:视频以逐字稿为准,标题和文案不算数。
3. **五字段标签**:每份原料开头写来源链接、来源类型、日期、领域、是否已整理。
4. **强制溯源**:结论每句话标出自哪份原料,标不出来源的句子不写。
5. **新分类门槛**:同一主题攒到 5 份再开新分类。
6. **写前先读**:AI 写任何文件前先读当前内容,追加不覆盖。

## FAQ

**为什么原料要一字不改,存 AI 的总结不行吗?**
这是最常犯的错。总结隔了一层 AI 的理解,丢了什么你查不到,就像拿朋友的转述当证据。原料存原文和逐字稿,总结只能进结论页。

**为什么视频一定要转录,看标题不够吗?**
标题党很常见。一条标题说「免费课程」的视频,转录完可能发现是卖课广告。逐字稿才是视频真正说了什么。

**转录要花钱吗?会上传我的视频吗?**
不花钱,也不上传。whisper 是装在你自己电脑上跑的模型。苹果芯片的 Mac 用 mlx-whisper 最快,其他电脑用 faster-whisper。

**读小红书、推特会封号吗?**
这些网站对自动操作查得严,有风险。建议只让 AI 读收藏夹、读单条这种小量的活,不要大批量抓取;能用小号就用小号。

**我不会写代码,能用吗?**
能。你需要的只是一个能在你电脑上执行命令的 AI 助手(比如 Claude Code)。所有命令都由 AI 来跑,遇到要你确认的地方它会停下来问。

**知识库能用 Obsidian 打开吗?**
能。整个知识库就是一个装满 Markdown 文件的文件夹,用 Obsidian 打开根目录即可。

**体检脚本报错怎么办?**
直接对 AI 说「跑一下体检,把问题修掉」。它会告诉你哪个文件缺了什么。也可以自己跑:

```bash
python3 ~/knowledge-base/scripts/kb-lint.py --root ~/knowledge-base
```

**换电脑或者想备份?**
整个 `~/knowledge-base` 文件夹拷走就行。想要版本记录,可以在里面 `git init`。

## License

MIT · 作者:Lynn
