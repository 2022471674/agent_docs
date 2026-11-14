# -*- coding: utf-8 -*-
"""UTF-8 安全的最终核验：确认主题残留清除 + 新值生效 + 双轴标注。"""
import os, re

ROOT = r"D:\Ai-Agent渗透测试\workspace"
PUB = os.path.join(ROOT, "public")


def read(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


h = read(os.path.join(PUB, "index.html"))
welcome = read(os.path.join(PUB, "2026", "11", "14", "welcome", "index.html"))

print("=" * 60)
print("[1] 主题默认残留（预期全部 0 / cleared）")
for k in ["欢迎使用安知鱼", "生活明朗", "万物可爱", "anheyu.com",
          "前端开发", "大学生涯", "生活日常", "新品主题", "Theme-AnZhiYu",
          "docs.anheyu.com", "再怎么看我", "2053", "04/01/2021", "4/1/2021"]:
    n = h.count(k)
    print("  %-20s %s" % (k, ("cleared" if n == 0 else "STILL %d hit(s)" % n)))

print("\n[2] 新值生效（预期 OK）")
for k in ["证据优先", "靶场手记", "docs.lvlv.asia", "本站说明", "发刊词",
          "结论先行", "授权靶场", "Hunter", "文章归档", "关于本站"]:
    print("  %-16s %s" % (k, "OK" if k in h else "MISSING"))

print("\n[3] 建站天数 data-publishDate（应为 2026）")
m = re.search(r'id="runtimeshow"[^>]*data-publishDate="([^"]+)"', h)
print("  publishDate =", m.group(1) if m else "(not found)")

print("\n[4] 发刊词 welcome.md 双轴标注（结论三态 + 证据四态）")
for k in ["Confirmed", "Suspected", "Unverified",
          "Observed", "Verified", "Inferred", "Unknown"]:
    print("  %-14s %s" % (k, "OK" if k in welcome else "MISSING"))
print("  %-14s %s (旧自造第四级，应为 0)" % ("信息性 / Informational", welcome.count("信息性 / Informational")))

print("\n[5] 首页顶部3个分类链接是否指向真实页面")
for cat in ["/categories/Web/", "/categories/站点/", "/archives/", "/2026/11/14/welcome/"]:
    disk = os.path.join(PUB, cat.strip("/").replace("/", os.sep), "index.html")
    print("  %-34s linked=%s generated=%s" % (cat, cat in h, os.path.exists(disk)))

print("\n[6] 数据驱动页面实质内容")
for rel, keys in [("about/index.html", ["Hunter", "Nmap"]),
                  ("equipment/index.html", ["Nmap", "Burp", "Ghidra", "Kali"]),
                  ("comments/index.html", ["envelope"]),
                  ("categories/index.html", ["Web", "站点"]),
                  ("tags/index.html", ["Writeup", "CTF"])]:
    p = os.path.join(PUB, rel.replace("/", os.sep))
    hh = read(p) if os.path.exists(p) else ""
    print("  %-24s %s" % (rel, " ".join("%s=%s" % (k, "Y" if k in hh else "N") for k in keys)))
print("=" * 60)
