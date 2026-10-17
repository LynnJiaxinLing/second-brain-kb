#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识库体检脚本。只读,不改任何文件。

检查三件事:
  1. raw 原料:五字段标签齐全,枚举字段是裸值,日期格式正确
  2. raw 原料:note_type 为 video 时必须有转录段
  3. wiki 结论:每行正文都带指向 raw 的来源链接,且链接指向的文件存在

用法:
  python3 kb-lint.py                       在当前目录(知识库根目录)体检全部文件
  python3 kb-lint.py --root ~/knowledge-base
  python3 kb-lint.py --root ~/knowledge-base domains/x/raw/web/a.md   只查指定文件
退出码:0 = 全部通过,1 = 有问题。
"""
import argparse
import glob
import io
import os
import re
import sys

REQUIRED = ['source_url', 'source_type', 'captured_at', 'domain', 'compiled']
BARE_ONLY = {'compiled': {'true', 'false', 'skipped'},
             'note_type': {'video', 'normal'}}
ENUM_FIELDS = ['source_type', 'domain', 'compiled', 'note_type']
# 转录段标题的常见写法,任何一个都算数
TRANSCRIPT_HEADING = re.compile(r'^##[^\n]*(视频转录|逐字稿|视频字幕|抽帧|transcript)', re.M | re.I)
SOURCE_LINK = re.compile(r'\]\(([^)\s]*raw/[^)\s]+)\)')
EXEMPT_SECTION = re.compile(r'^##\s*(相关|related|see also)', re.I)


def split_frontmatter(txt):
    """返回 (frontmatter 文本或 None, 正文, 正文起始行号)。"""
    if not txt.startswith('---'):
        return None, txt, 1
    parts = txt.split('\n---', 1)
    if len(parts) < 2:
        return None, txt, 1
    fm = parts[0][3:]
    body = parts[1].split('\n', 1)[1] if '\n' in parts[1] else ''
    return fm, body, fm.count('\n') + 3


def lint_raw(path, txt):
    fm, _, _ = split_frontmatter(txt)
    if fm is None:
        return ['缺 frontmatter(文件开头没有 --- 标签段)']
    kv = dict(re.findall(r'^([A-Za-z_]+):[ \t]*(.*?)[ \t]*$', fm, re.M))
    bad = []
    for k in REQUIRED:
        if not kv.get(k):
            bad.append('缺字段 %s' % k)
    for k, v in kv.items():
        if k in ENUM_FIELDS and re.search(r'[（(]', v):
            bad.append('%s 是枚举字段,值里不能带括号注释: %s' % (k, v))
        elif k in BARE_ONLY and v and v not in BARE_ONLY[k]:
            bad.append('%s 必须是 %s 之一,实际是 %r' % (k, '/'.join(sorted(BARE_ONLY[k])), v))
    if kv.get('captured_at') and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', kv['captured_at']):
        bad.append('captured_at 必须是 YYYY-MM-DD,实际是 %r' % kv['captured_at'])
    if kv.get('note_type') == 'video':
        tf = kv.get('transcript_file')
        if tf:
            if not os.path.exists(os.path.join(os.path.dirname(path), tf)):
                bad.append('transcript_file 指向的文件不存在: %s' % tf)
        elif not TRANSCRIPT_HEADING.search(txt):
            bad.append('note_type=video 但没有转录段(需要 "## 视频转录" 或 "## 逐字稿" 一节,或 transcript_file 字段)')
    return bad


def lint_wiki(path, txt):
    _, body, start = split_frontmatter(txt)
    lines = body.split('\n')
    bad = []
    in_code = in_comment = exempt = False
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('```'):
            in_code = not in_code
            continue
        if '<!--' in s:
            in_comment = '-->' not in s
            continue
        if in_comment:
            in_comment = '-->' not in s
            continue
        if in_code or not s:
            continue
        if s.startswith('#'):
            exempt = bool(EXEMPT_SECTION.match(s))
            continue
        if exempt or s.startswith('>'):
            continue
        if s.startswith('|'):
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ''
            if re.fullmatch(r'\|?[\s:|-]+\|?', s) or re.fullmatch(r'\|?[\s:|-]+\|?', nxt):
                continue  # 表格分隔行或表头
        links = SOURCE_LINK.findall(s)
        if not links:
            bad.append('第 %d 行无回链: %s' % (start + i, s[:60]))
            continue
        for link in links:
            target = os.path.normpath(os.path.join(os.path.dirname(path), link.split('#')[0]))
            if not os.path.exists(target):
                bad.append('第 %d 行回链指向的文件不存在: %s' % (start + i, link))
    return bad


def classify(rel):
    parts = rel.replace(os.sep, '/').split('/')
    if '_template' in parts:
        return None
    if parts[0] == 'inbox' or 'raw' in parts:
        return 'raw'
    if 'wiki' in parts:
        return 'wiki'
    return None


def main():
    ap = argparse.ArgumentParser(description='知识库体检(只读)')
    ap.add_argument('--root', default='.', help='知识库根目录,默认当前目录')
    ap.add_argument('paths', nargs='*', help='只检查这些文件或 glob,默认检查全部')
    args = ap.parse_args()
    root = os.path.abspath(os.path.expanduser(args.root))

    if args.paths:
        files = []
        for p in args.paths:
            p = p if os.path.isabs(p) else os.path.join(root, p)
            files.extend(glob.glob(p, recursive=True) if any(c in p for c in '*?[') else [p])
    else:
        files = (glob.glob(os.path.join(root, 'domains/*/raw/**/*.md'), recursive=True)
                 + glob.glob(os.path.join(root, 'domains/*/wiki/**/*.md'), recursive=True)
                 + glob.glob(os.path.join(root, 'inbox/**/*.md'), recursive=True))

    checked = fails = 0
    for f in sorted(set(os.path.abspath(x) for x in files)):
        rel = os.path.relpath(f, root)
        kind = classify(rel)
        if kind is None:
            continue
        if not os.path.isfile(f):
            print('✗ %s\n    文件不存在' % rel)
            fails += 1
            continue
        checked += 1
        txt = io.open(f, encoding='utf-8').read()
        probs = lint_raw(f, txt) if kind == 'raw' else lint_wiki(f, txt)
        if probs:
            fails += 1
            print('✗ %s' % rel)
            for p in probs:
                print('    %s' % p)

    print('\n检查 %d 个文件,%d 个有问题' % (checked, fails))
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
