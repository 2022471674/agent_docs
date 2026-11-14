# -*- coding: utf-8 -*-
# Live UTF-8 check against the running 4000 server.
# Separate: (1) user-requested items = pass/fail verdict; (2) diagnostics only.
import urllib.request, re

h = urllib.request.urlopen("http://127.0.0.1:4000/", timeout=10).read().decode("utf-8")

USER_REQ = [
    ("icp_number", "\u8700ICP\u59072026047258\u53f7-1"),   # 蜀ICP备2026047258号-1
    ("icp_link", "beian.miit.gov.cn"),
    ("power_by", "power By deepseek-v4 pro@onwer 28.7"),
    ("hunter_dev", "agent@Hunter"),
    ("custom_text_div", "footer_custom_text"),
    ("real_anchor", 'rel="noopener"'),
]
print("== USER-REQUESTED footer items (live 4000, utf-8) ==")
for label, kw in USER_REQ:
    print("  %-18s = %s" % (label, kw in h))
print("  USER_REQ_ALL_OK =", all(kw in h for _, kw in USER_REQ))

print("\n== diagnostic: how 'copyright' actually rendered (not a requirement) ==")
m = re.search(r'class="copyright"[^>]*>(.{0,100})', h)
print("  segment:", ascii(m.group(1)) if m else "(not found)")
for probe in ["&copy;2026 By Hunter", "\u00a92026 By Hunter", "2026 By Hunter", "&copy;", "\u00a9"]:
    print("  probe %-26s = %s" % (ascii(probe), probe in h))
