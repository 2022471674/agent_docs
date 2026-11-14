---
title: 极客大挑战 2019 - Web - Havefun
date: 2026-11-14 18:31:00
categories:
  - CTF
  - 极客大挑战 2019
  - Web
tags:
  - 源码泄露
  - 信息泄露
  - PHP 逻辑审计
  - GET 参数
cover: /img/cover/pink-hair-flower-girl.jpg
description: 极客大挑战 2019 的签到题，页面 HTML 末尾注释泄漏了一段 PHP 逻辑：读取 cat 参数回显，当值等于 dog 时输出 flag。只需在首页追加查询串触发条件即可拿到结果，考察查看源码与阅读简单后端逻辑。
keywords:
  - 源码泄露
  - HTML 注释
  - PHP
  - cat 参数
  - 逻辑判断
ai: >-
  本题是极客大挑战 2019 的 Web 签到题 Havefun，难度 Easy，本质是信息泄露加简单逻辑判断。页面本身是一只猫的图案，直接访问看不到线索，但查看 HTML 源码会在末尾注释里发现一段泄漏的后端 PHP 代码：程序读取 GET 参数 cat 并原样回显，当 cat 的值严格等于 dog 时输出一段标记。原题注释里是一段占位字符串，而练习场环境的真实 flag 由平台注入，格式不同。利用过程无需任何注入或编码技巧，只要在首页 URL 后追加 cat 参数令其等于 dog，即可命中条件并让页面回显 flag。该题提醒解题者养成先看源码与注释的习惯。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | 极客大挑战 2019 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

## 信息收集

探测首页，查看 HTML 源码，在页面底部注释中发现泄漏的后端 PHP 逻辑。

```php
$cat=$_GET['cat'];
echo $cat;
if($cat=='dog'){
    echo 'Syc{cat_cat_cat_cat}';  // 占位符，平台真实 flag 为另一格式
}
```

练习场 ID、题目 ID、friendly_id 与提交记录 ID 等标识已脱敏。

## 漏洞分析

类型：PHP 源码注释泄漏（信息泄露 / 逻辑判断泄漏）。

原理：页面 HTML 源码的末尾注释中泄漏了后端 PHP 逻辑。后端读取 GET 参数 `cat` 并回显，当 `cat` 等于 `dog` 时输出 flag。只需构造 `?cat=dog` 即可触发。

## 利用过程

1. **探测首页**：访问 `/`，查看 HTML 源码，在页面底部注释中发现泄漏的 PHP 逻辑。
2. **触发判断**：访问 `/?cat=dog`，满足 `$cat=='dog'` 条件。
3. **拿到 flag**：页面返回真实 flag（另有原题占位符 `Syc{cat_cat_cat_cat}`，平台真实 flag 为另一格式）。

## 完整 EXP

payload 归档内容并入本节。

```http
GET /?cat=dog HTTP/1.1
Host: target:8080
User-Agent: Mozilla/5.0
```

curl 命令：

```bash
curl "http://target:8080/?cat=dog"
```

触发逻辑（源码注释泄漏）：

```php
$cat=$_GET['cat'];
echo $cat;
if($cat=='dog'){
    echo 'Syc{cat_cat_cat_cat}';  // 占位符，平台真实 flag 为另一格式
}
```

## Flag

```text
flag{xxxx}
```

提交记录：结果 accepted，+1 分（真实 flag 与提交 ID 已脱敏）。

## 踩坑与总结

- 线索藏在 HTML 源码末尾注释里，直接看渲染页面会漏掉，解题第一步应查看源码。
- 判断是严格相等 `$cat=='dog'`，参数值必须正好是 `dog`。
- 注释里的 `Syc{cat_cat_cat_cat}` 是原题占位符，练习场真实 flag 格式不同，不要误提交占位符。
- 平台提交 accepted、+1 分，二次复现稳定。
