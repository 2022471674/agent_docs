---
title: NewStarCTF 2023 - Web - 泄漏的秘密
date: 2026-11-14 18:19:00
categories:
  - CTF
  - NewStarCTF 2023
  - Web
tags:
  - 敏感文件泄露
  - robots.txt
  - 源码备份
  - www.zip
cover: /img/cover/pink-hair-flower-girl.jpg
description: NewStarCTF 2023 公开赛道 Web 简单题，考察敏感文件与整站源码备份泄露。首页提示管理员泄漏了两个敏感信息，扫描根目录发现爬虫协议文件给出前半段、整站压缩包里的首页源码给出后半段，拼接两段即可还原完整 flag。
keywords:
  - 泄漏的秘密
  - robots.txt
  - www.zip
  - 源码备份
  - 信息泄露
ai: >-
  本题是 NewStarCTF 2023 公开赛道 Web 方向的信息泄露题，环境为 PHP 与 openresty。首页返回一段编码混淆的提示，解码后是管理员泄漏了两个敏感信息，关键词是两个。漏洞并非注入或逻辑绕过，而是运维把敏感文件直接放在网站根目录：爬虫协议文件写有答案前半段，整站源码压缩包解压后的首页文件写有后半段。利用链为扫描常见敏感路径、分别读取两处泄露点、把两段拼接还原完整答案，其余版本库与环境文件均不存在。最终拿到脱敏后的 flag，核心教训是爬虫协议文件与源码备份是最经典的泄露入口，上线前必须清理，乱码提示也要先正确解码。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | NewStarCTF 2023 公开赛道 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |
| 服务器 | PHP/7.3.15 + openresty |

## 信息收集

访问根路径返回一段 UTF-8 编码的提示（浏览器可能显示为乱码，实为 GBK 与 UTF-8 混淆）：`粗心的管理员泄漏了一些敏感信息，请你找出他泄漏的两个敏感信息！` 关键信息是「泄漏了**两个**敏感信息」。

对 Web 根目录常见敏感文件进行扫描，结果：

| 路径 | 状态码 | 说明 |
|---|---|---|
| `/robots.txt` | 200 | 泄露 flag 第一部分 |
| `/www.zip` | 200 | 源码备份，泄露 flag 第二部分 |
| 其他（`.git`、`.svn`、`.env` 等） | 404 | 不存在 |

攻击链总览（源 wp 原链转写）：

```bash
# 访问首页 → 提示「泄漏了两个敏感信息」
#   → 扫描 Web 根目录敏感文件
#   → robots.txt 泄露 PART ONE
#   → www.zip 源码备份泄露 index.php 中的 PART TWO
#   → 拼接得到完整 flag
```

## 漏洞分析

- 敏感文件泄露：`robots.txt` 是经典的目录/信息泄露入口，本题直接把 flag 前半段写在里面。
- 源码备份文件泄露：`www.zip` 常见于管理员把整站源码打包后遗留在 Web 根目录，解压即可得到 `index.php` 等源文件。
- 本题不涉及注入、反序列化或命令执行，是纯粹的「配置 / 运维失误」型信息泄露；flag 被人为拆成两段，分别藏进两个泄露点，首页的「两个」是唯一提示。

## 利用过程

### 1. robots.txt 泄露 PART ONE

`GET /robots.txt` 返回 200，正文直接写有 flag 的前半段（真实值已脱敏，仅保留结构）：

```http
GET /robots.txt HTTP/1.1
Host: target:8080

HTTP/1.1 200 OK

PART ONE: flag{xxxx
```

### 2. www.zip 泄露 PART TWO

下载并解压 `www.zip`，得到 `index.php`：

```php
<?php
$PART_TWO = "xxxx}";  // flag 后半段，真实值已脱敏
echo "<h1>粗心的管理员泄漏了一些敏感信息，请你找出他泄漏的两个敏感信息！</h1>";
```

### 3. 拼接完整 flag

`robots.txt` 的前半段与 `index.php` 里的 `$PART_TWO` 后半段直接拼接，即还原完整 flag（见「Flag」段）。

## 完整 EXP

```bash
curl "http://target:8080/robots.txt"            # PART ONE
curl -o www.zip "http://target:8080/www.zip"    # 下载源码备份
unzip www.zip                                    # 解压得到 index.php，含 PART TWO
```

```http
GET /www.zip HTTP/1.1
Host: target:8080
```

## Flag

`flag{xxxx}`（真实值已脱敏）。原题采用 NewStarCTF 2023 的 flag 格式；两部分分别来自 `robots.txt` 与 `www.zip` 中的 `index.php`，拼接后即为完整值。

## 踩坑与总结

1. **「两个敏感信息」是明确提示**：flag 被拆成两部分，分别藏在两个泄露点，缺一不可。
2. **`robots.txt` 是经典入口**：用于告知爬虫哪些路径不可访问，反倒常暴露后台、备份路径，甚至像本题一样直接写敏感数据。
3. **`www.zip` 是源码备份泄露**：管理员打包源码到 Web 根目录是高频失误，扫描字典里应有 `www.zip`、`www.rar`、`backup.zip` 等。
4. **先扫目录再谈利用**：Easy 难度的信息泄露题往往不需要复杂漏洞，目录扫描 + 备份文件枚举即可解题。
5. **乱码不等于无用**：首页提示的 GBK/UTF-8 混淆要先正确解码，才能读出「两个」这个关键线索。

> 仅记录授权靶场环境下的研究；复现命令与源码来自本地 WP 归档。
