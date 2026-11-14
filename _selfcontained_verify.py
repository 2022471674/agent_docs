# -*- coding: utf-8 -*-
"""自包含决定性验证：脚本内临时起 http.server serve public/，测完关闭。

不依赖外部长期 hexo server（之前 session rebound 后 4000 已停）。
验证 3 件新需求 + 全站回归：
  [A] source/public 封面文件名集合(hex)一致
  [B] 12 张封面 HTTP GET 200 + Content-Type image/jpeg
  [C] 首页 footer 合规渲染（备案号/工信部链接/power By/agent@Hunter/真<a>标签）
  [D] covers.yml 清单对齐
  [E] 全站路由 200 回归
"""
import os, urllib.request, urllib.parse, yaml, re, threading, functools
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = r"D:\Ai-Agent渗透测试\workspace"
PUB = os.path.join(ROOT, "public")
PUB_COVER = os.path.join(PUB, "img", "cover")
SRC_COVER = os.path.join(ROOT, "source", "img", "cover")
COVERS = os.path.join(ROOT, "source", "_data", "covers.yml")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def hx(s):
    return os.fsencode(s).hex(" ")


def main():
    handler = functools.partial(QuietHandler, directory=PUB)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    BASE = "http://127.0.0.1:%d" % port
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    print("temporary_server:", BASE, "(serving public/)")
    print("=" * 72)

    def get(path, timeout=10):
        url = BASE + path
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "hexo-selfverify/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
                return r.status, len(body), r.headers.get("Content-Type", ""), body
        except urllib.error.HTTPError as e:
            return e.code, 0, "", b""
        except Exception as e:
            return "ERR", 0, str(e), b""

    try:
        print("[A] source/public 封面文件名集合(hex)一致")
        sn = sorted(n for n in os.listdir(SRC_COVER) if os.path.isfile(os.path.join(SRC_COVER, n)))
        pn = sorted(n for n in os.listdir(PUB_COVER) if os.path.isfile(os.path.join(PUB_COVER, n)))
        print("    source=%d public=%d names_equal=%s" % (len(sn), len(pn), sn == pn))

        print("\n[B] 12 张封面 HTTP（URL 取自 public 真实名）")
        all_ok = True
        for n in pn:
            path = "/img/cover/" + urllib.parse.quote(n)
            st, length, ctype, _ = get(path)
            ok = (st == 200 and length > 0 and "image" in ctype)
            all_ok = all_ok and ok
            print("    %-4s %-8s %-12s %s  %s" % (st, length, ctype.split(";")[0], "OK" if ok else "FAIL", n))
        print("    all_covers_200 =", all_ok)

        print("\n[C] 首页 footer 合规渲染（HTTP GET /）")
        st, length, _, body = get("/")
        html = body.decode("utf-8", "replace")
        checks = [("icp_number", "蜀ICP备2026047258号-1"),
                  ("icp_link", "beian.miit.gov.cn"),
                  ("icp_real_anchor", 'href="https://beian.miit.gov.cn/"'),
                  ("power_by", "power By deepseek-v4 pro@onwer 28.7"),
                  ("hunter_dev", "本网站由agent@Hunter管理和开发"),
                  ("footer_custom_text_div", "footer_custom_text")]
        results = {label: (kw in html) for label, kw in checks}
        for label, ok in results.items():
            print("    %-24s = %s" % (label, ok))
        m = re.search(r'footer_custom_text[^>]*>(.{0,300})', html)
        if m:
            print("    rendered_segment:", ascii(m.group(1)[:220]))
        print("    footer_all_ok =", all(results.values()))

        print("\n[D] covers.yml 清单对齐")
        with open(COVERS, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        urls_target_ok = all(r["url"].split("/")[-1] in pn for r in data)
        content_ok = all("Unknown" not in str(r["content"]) for r in data)
        print("    records=%d all_urls_have_target=%s content_inferred_ok=%s" % (
            len(data), urls_target_ok, content_ok))

        print("\n[E] 全站路由回归")
        routes = ["/", "/about/", "/equipment/", "/comments/", "/archives/",
                  "/categories/", "/tags/", "/categories/Web/",
                  "/2026/11/14/welcome/", "/2026/11/14/hctf2018-hideandseek/",
                  "/atom.xml", "/img/avatar.jpg", "/img/cover-default.webp", "/favicon.ico"]
        route_ok = True
        for p in routes:
            st, length, _, _ = get(p)
            ok = st == 200
            route_ok = route_ok and ok
            print("    %-46s %-4s %sB %s" % (p, st, length, "" if ok else "FAIL"))
        print("    all_routes_200 =", route_ok)

        print("=" * 72)
        print("VERDICT:", "ALL PASS" if (all_ok and all(results.values()) and
              urls_target_ok and content_ok and route_ok and sn == pn) else "SOME CHECK FAILED")
    finally:
        httpd.shutdown()
        httpd.server_close()
        print("temporary_server: stopped")


if __name__ == "__main__":
    main()
