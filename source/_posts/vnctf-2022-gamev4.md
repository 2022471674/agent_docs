---
title: VNCTF2022 - Web - GameV4.0
date: 2026-11-14 18:25:00
categories:
  - CTF
  - VNCTF2022
  - Web
tags:
  - 前端JS源码审计
  - base64编码
  - URL编码
  - 信息泄露
cover: /img/cover/backless-girl-magnolia.jpg
description: VNCTF2022 公开赛 Web 题表面是推箱子小游戏，实为前端脚本源码审计。下载关卡数据文件后在答案关卡定义末尾发现编码字段，其值经基础编码与网址编码双层解码还原出 flag，全程无需通关游戏，也无需后端接口。
keywords:
  - GameV4.0
  - boxboy
  - data.js
  - base64
  - URL解码
ai: >-
  本题来自 VNCTF2022 公开赛 Web 方向简单难度，环境为纯静态前端加推箱子小游戏，题目描述会踩冰块吗是障眼法。漏洞不在游戏逻辑，而在前端关卡数据文件：它包含全部关卡定义，在答案关卡末尾藏有一个键名经编码的字段，其值是一段双重编码的字符串。利用链为下载并审计前端脚本、搜索关键字定位该字段、先做基础编码解码得到带百分号转义的网址编码串、再做一次网址解码还原括号，最终得到脱敏后的 flag。关键点在于不必真的通关，后端登录目录在这套环境里未部署，说明答案完全不依赖服务端，纯前端即可解出。核心教训是前端资源里的敏感常量同样是泄露源，审计应覆盖所有静态数据文件。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | VNCTF2022 公开赛 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |
| 服务器 | openresty（纯静态前端 + Vue 推箱子游戏） |

## 信息收集

访问根路径返回一个名为 `boxboy` 的推箱子游戏（Sokoban），基于 Vue 构建，加载了多个 JS 文件：

```text
js/data.js  js/index.js  js/item.js  js/base.js
js/story.js js/editor.js js/ui.js
```

题目描述「你会踩冰块吗？」暗示是「踩冰块」推箱子谜题。注意后端 PHP 端点（`login/` 目录）在这套环境里未部署，返回 404，说明 flag 不依赖后端。

## 漏洞分析

- 前端 JS 源码审计
- 多层编码（base64 + URL 编码）

攻击链总览（源 wp 原链转写）：

```text
访问首页 → 识别为 boxboy 推箱子游戏（Vue 前端）
  → 下载前端 JS 文件（js/data.js 等）
  → 在 data.js 末尾 FLAG 关卡定义里发现 base64 字段
  → base64 + URL 双层解码得到 flag
```

下载所有 JS 文件，`js/data.js` 最大（77KB），包含全部关卡数据。搜索 `flag` 关键字，发现关键位置：

```text
js_data.js:357  Levels["FLAG"] = { ... }
js_data.js:2098 "name": "FLAG"
```

## 利用过程

### 1. 定位 flag 字段

在 `data.js` 文件末尾，`Levels["FLAG"]` 关卡定义的最后，藏有一个 base64 字段：

```json
"ZmxhZw==": "Vk5DVEYlN0JXZWxjb21lX3RvX1ZOQ1RGMjAyMiU3RA=="
```

- `ZmxhZw==` 是 base64 编码的 `flag`（字段名提示这是 flag）
- 对应的值是双层编码的 flag 数据

### 2. 双层解码

```python
import base64, urllib.parse

s = 'Vk5DVEYlN0JXZWxjb21lX3RvX1ZOQ1RGMjAyMiU3RA=='
a = base64.b64decode(s).decode()       # 得到 URL 编码串（%7B/%7D 即花括号）
b = urllib.parse.unquote(a)            # URL 解码还原，得到最终 flag
print(b)                                # flag{xxxx}（真实值已脱敏）
```

先 base64 解码，再 URL 解码（`%7B` = `{`、`%7D` = `}`），即可还原完整 flag（见「Flag」段，真实值已脱敏）。

## 完整 EXP

```bash
curl "http://target:8080/js/data.js" | grep -A2 "ZmxhZw=="
# 得到 base64 值后先 base64 解码，再 URL 解码 %7B -> {, %7D -> }
```

```python
import base64, urllib.parse, urllib.request

# 直接抓取 data.js 并做双层解码
js = urllib.request.urlopen("http://target:8080/js/data.js").read().decode("utf-8", "ignore")
# 取出 "ZmxhZw==" 键对应的值后：
s = "Vk5DVEYlN0JXZWxjb21lX3RvX1ZOQ1RGMjAyMiU3RA=="
flag = urllib.parse.unquote(base64.b64decode(s).decode())  # 真实值已脱敏：flag{xxxx}
print(flag)
```

## Flag

`flag{xxxx}`（真实值已脱敏）。最终值由 `data.js` 中 `Levels["FLAG"]` 末尾的 base64 字段经 base64 + URL 双层解码得到。

## 踩坑与总结

1. **题目表面是游戏，实则是前端源码审计**：flag 不需要真的「踩冰块」通关，而是藏在 JS 数据文件里。
2. **flag 藏在 `Levels["FLAG"]` 关卡定义的末尾**，以 base64 字段名 `ZmxhZw==`（= `flag`）为提示。
3. **双层编码**：先 base64 解码，再 URL 解码（`%7B` = `{`，`%7D` = `}`）——只做一层会看到一串带百分号的乱码，容易误判。
4. **后端 PHP 端点（login/ 目录）在这套环境里未部署**，返回 404，说明 flag 不依赖后端，纯前端可解。
5. **别被标题和描述带偏**：「GameV4.0」「你会踩冰块吗」都是叙事包装，先通读静态资源再决定是否玩游戏。
6. 前端打包的 JS / JSON 数据文件属于公开可读资源，敏感常量不应写进客户端。

> 仅记录授权靶场环境下的研究；base64 字段与解码脚本来自本地 WP 归档，真实 flag 值已脱敏。
