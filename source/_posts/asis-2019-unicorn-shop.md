---
title: ASIS 2019 - Web - Unicorn shop
date: 2026-11-14 18:04:00
categories:
  - CTF
  - ASIS 2019
  - Web
tags:
  - Unicode数值解析
  - 逻辑漏洞
  - unicodedata.numeric
  - 价格校验绕过
cover: /img/cover/girl-window-white-flowers.jpg
description: Unicode 逻辑漏洞题，购买接口用 unicodedata.numeric(price) 解析价格且限制单字符，用「兆」「亿」等单个 Unicode 大数值字符即可绕过 1337 价格校验买下商品拿 flag。
keywords:
  - Unicode
  - unicodedata.numeric
  - 逻辑漏洞
  - Tornado
  - ASIS
ai: >-
  本题是 ASIS 2019 的 Web 逻辑漏洞题，场景是独角兽商店，购买接口 POST /charge 接收 id 与 price。后端用 unicodedata.numeric(price) 解析价格，限制 price 为单字符，而买 ultra unicorn 需数值不小于 1337。直接传 1337 触发 Only one char allowed，传空值则泄漏 Tornado Traceback。该函数支持大数值单字符，如兆为一万亿、亿为一亿，提交 id=4&price=兆 即可买下商品返回 flag。核心是用字符个数代替数值范围校验，被 Unicode 数值字符打破假设。
copyright_author: Hunter
---

> 结论先行：后端用 `unicodedata.numeric(price)` 解析价格且限制单字符，用「兆」「亿」这类单个 Unicode 大数值字符即可 ≥1337 买下 ultra unicorn 拿 flag。

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | ASIS 2019 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

## 信息收集

商品列表页存在购买表单 `POST /charge`，参数 `id`、`price`。探测过程：

- `id=4&price=1337` → `Only one char(?) allowed!`（单字符限制）
- `id=4&price=0` → `You don't have enough money!`
- `id=4&price=`（空白）→ 泄漏 Tornado Traceback：`unicodedata.numeric(price)` 在 `Shop.py:34`

由此确认后端是 Python Tornado，价格由 `unicodedata.numeric()` 解析。

## 漏洞分析

### 类型

逻辑漏洞：Unicode 数值解析绕过价格校验。

### 原理

`ultra unicorn`（id=4）价格为 1337，需要 `unicodedata.numeric(price) >= 1337` 才能购买。由于 price 只能是一个字符，而 `unicodedata.numeric()` 支持 Unicode 大数值字符（如 CJK 数字、罗马数字、梅罗伊特数字等），可以用单个字符表示远超 1337 的数值。

- `unicodedata.numeric('兆')`（U+5146）= 1000000000000.0
- `unicodedata.numeric('亿')`（U+4EBF）= 100000000.0

均远超 1337。后端用「字符个数」代替「数值范围」做校验，被 Unicode 数值字符打破隐含假设。

## 利用过程

1. 探测接口：首页为商品列表，购买表单 `POST /charge`，参数 `id`、`price`。
2. 识别校验逻辑：如上三处探测，确认单字符限制与 `unicodedata.numeric` 解析点。
3. 利用 Unicode 大数值字符：`unicodedata.numeric('兆')` = 1000000000000.0，远超 1337。
4. 购买 ultra unicorn：`POST /charge`，`id=4&price=兆`，返回 flag。

## 完整 EXP

最终 payload：

```http
POST /charge
id=4&price=兆
```

`兆` 可替换为 `亿` 等任意 `unicodedata.numeric() >= 1337` 的单字符。

curl 命令：

```bash
curl -X POST "http://target:8080/charge" \
  --data-urlencode "id=4" \
  --data-urlencode "price=兆"
```

其他可用字符：

- `亿` (U+4EBF) = 100000000.0
- `兆` (U+5146) = 1000000000000.0
- 任意 `unicodedata.numeric() >= 1337` 的单字符

## Flag

```text
flag{xxxx}
```

（提交记录：accepted，+1 分）

## 踩坑与总结

1. 空 price 触发的 Traceback 是定位 `unicodedata.numeric` 的关键线索，报错信息本身就是信息收集的一部分。
2. 「单字符」限制针对的是字符个数而非数值上限，Unicode 数值字符正好击穿这一假设。
3. 校验应落在解析后的数值上（如 `>= 1337` 且类型/范围检查），而非输入长度。
