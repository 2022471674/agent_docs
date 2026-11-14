# -*- coding: utf-8 -*-
"""把 cover/ 里的图片搬(复制)进 Hexo 合法静态目录，并生成素材清单。

- 源: D:\\Ai-Agent渗透测试\\cover
- 落点: <workspace>\\source\\img\\cover\\  ->  URL /img/cover/<file>
- 文件名按 os.listdir 的真实 str 处理（不硬编码，规避显示层折叠/隐藏字符）
- 规范化为小写 kebab-case，保证 URL 友好
- 逐文件校验 sha256(源) == sha256(目标)
- 生成 source/_data/covers.yml（依据文件名推断内容，标注 inferred_from_filename）
- 只复制，不删除源文件
"""
import os, re, hashlib, shutil, sys

SRC = r"D:\Ai-Agent渗透测试\cover"
ROOT = r"D:\Ai-Agent渗透测试\workspace"
DST = os.path.join(ROOT, "source", "img", "cover")
DATA = os.path.join(ROOT, "source", "_data", "covers.yml")
URL_PREFIX = "/img/cover/"

# 依据文件名推断的图像内容（Inferred，未做图像识别/未打开图片）
CONTENT = {
    "anime-characters-collage": "动漫角色群像拼贴",
    "backless-girl-magnolia": "露背女孩与木兰花",
    "blindfold-side-portrait": "蒙眼侧脸肖像",
    "girl-wading-rainy-street": "雨中街道蹚水的女孩",
    "girl-window-white-flowers": "窗边白花与女孩",
    "green-hair-letter-girl": "绿发读信女孩",
    "petal-smiley-faces": "花瓣笑脸",
    "pink-hair-flower-girl": "粉发花间女孩",
    "rainy-night-white-hair-girl": "雨夜白发女孩",
    "silver-hair-blue-eyes-girl": "银发蓝眼女孩",
    "sword-girl-blue-sky": "蓝天下持剑女孩",
    "three-people-indoor": "室内三人",
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def norm(name, used):
    stem, ext = os.path.splitext(name)
    s = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    cand = s + ext.lower()
    i = 2
    while cand in used:
        cand = "%s-%d%s" % (s, i, ext.lower())
        i += 1
    used.add(cand)
    return cand, s


def main():
    os.makedirs(DST, exist_ok=True)
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    files = sorted(n for n in os.listdir(SRC) if os.path.isfile(os.path.join(SRC, n)))
    used, records, bad = set(), [], []

    print("SRC :", SRC)
    print("DST :", DST)
    print("files:", len(files))
    print("=" * 78)

    for n in files:
        sp = os.path.join(SRC, n)
        # 校验 JPEG magic
        with open(sp, "rb") as f:
            head = f.read(3)
        if head != b"\xff\xd8\xff":
            bad.append((n, "not JPEG"))
            print("  SKIP (not JPEG):", ascii(n))
            continue

        tgt, stem = norm(n, used)
        dp = os.path.join(DST, tgt)
        shutil.copy2(sp, dp)
        h_src, h_dst = sha256(sp), sha256(dp)
        ok = h_src == h_dst
        if not ok:
            bad.append((tgt, "sha256 mismatch"))
        # 目标名必须纯 ASCII（URL 友好）
        ascii_safe = all(ord(c) < 128 for c in tgt)
        if not ascii_safe:
            bad.append((tgt, "non-ascii target name"))

        content = CONTENT.get(stem, "Unknown（无法据文件名推断）")
        records.append({
            "file": tgt,
            "url": URL_PREFIX + tgt,
            "content": content,
            "content_source": "inferred_from_filename",
            "original_name": ascii(n),
            "sha256": h_src,
            "size": os.path.getsize(dp),
        })
        print("  %-38s %-38s %s  sha=%s" % (
            ascii(n), tgt, "OK" if ok else "FAIL", h_src[:12]))

    # 生成素材清单（结构化，便于以后文章/程序引用 site.data.covers）
    import yaml
    header = ("# 封面/插画素材清单\n"
              "# 内容为依据文件名的推断(inferred_from_filename)，未经图像识别或人工看图确认\n"
              "# 用法: 文章 front-matter  cover: /img/cover/<file>\n"
              "#   或 Markdown  ![描述](/img/cover/<file>)\n")
    with open(DATA, "w", encoding="utf-8", newline="\n") as f:
        f.write(header)
        f.write(yaml.safe_dump(records, allow_unicode=True, sort_keys=False,
                               default_flow_style=False))

    print("=" * 78)
    print("copied:", len(records), "/", len(files))
    print("manifest:", DATA)
    print("problems:", bad if bad else "NONE")
    # 反向确认特殊文件名的真实字节
    special = [r for r in records if r["file"].startswith("silver-hair")]
    if special:
        print("special file ->", special[0]["file"], "| original_name:", special[0]["original_name"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
