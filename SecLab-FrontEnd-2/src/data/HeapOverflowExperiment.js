// 堆溢出实验模拟数据（glibc 堆利用进阶，配合操作环境本地编写漏洞程序）
export const HeapOverflowExperiment = {
  id: 17,
  name: '堆溢出实验',
  introduction:
    '本实验带你深入 glibc 堆管理机制，从 chunk 结构与 fastbin/smallbin 组织出发，理解堆溢出原理，掌握 unlink 利用与 fastbin attack 两大经典手法，最终用 pwntools 编写 exp 完成任意地址写与控制流劫持，获取 flag。适合已掌握栈溢出基础的同学进阶 PWN。',
  difficulty: 5,
  taskPoints: [
    {
      id: 1,
      name: '堆基础与 glibc malloc 机制',
      description: '理解堆 chunk 结构、标志位与 fastbin/smallbin 的组织方式',
      score: 20,
      document: `## 堆基础与 glibc malloc 机制

### 1. 堆是什么
栈由编译器自动管理（函数返回即释放），而**堆**是程序运行时通过 \`malloc/calloc/realloc\` 动态申请的内存，需由程序员手动 \`free\`。glibc 的堆管理器（ptmalloc）负责维护这些堆块（chunk）的分配与回收。

### 2. chunk 结构（64 位）
每个堆块都有一个头部，结构如下：

~~~text
struct malloc_chunk {
  size_t prev_size;   // 前一个 chunk 的大小（仅在前一个 chunk 空闲时有效）
  size_t size;        // 本 chunk 大小（含头部），低 3 位是标志位
  struct malloc_chunk* fd;  // 前向指针（空闲时有效）
  struct malloc_chunk* bk;  // 后向指针（空闲时有效）
  // 后续可能还有 fd_nextsize/bk_nextsize（large bin）
};
~~~

### 3. size 的标志位（低 3 位）
- **PREV_INUSE (0x1)**：前一个 chunk 是否在使用中。置 1 表示在使用，此时 prev_size 字段可被前一个 chunk 复用存数据。
- **IS_MMAPPED (0x2)**：是否由 mmap 分配。
- **NON_MAIN_ARENA (0x4)**：是否属于非主线程的 arena。

实际 size = chunk 大小 & ~0x7。例如 size=0x91 表示 chunk 大小 0x90，且 PREV_INUSE=1。

### 4. bin 组织
空闲 chunk 按大小被放入不同的"桶"（bin）中，便于快速分配：
- **fastbin**：管理小块（64 位下通常 0x20~0x80）。单链表（只用 fd），**LIFO**（后进先出），free 后不合并、不清空 fd，是漏洞高发区。
- **smallbin**：双链表（fd+bk），大小固定，FIFO。
- **unsorted bin**：free 的小/中块先进入此处，malloc 时遍历，找不到再分拣到 smallbin/largebin。
- **largebin**：大块，按大小范围分桶，内部再按大小排序。

### 5. 关键要点
- fastbin 的 free chunk 仍保留 fd 指针，且 free 时**不校验 chunk 是否已被释放**（旧版 glibc），这是 **double free** 的根源。
- 相邻空闲 chunk 会被**合并**（coalesce）以减少碎片，但 fastbin 不合并。
- malloc 返回的指针指向 chunk 头部之后的用户数据区。`,
      questions: [
        {
          id: 1,
          content: 'glibc chunk 的 size 字段低 3 位是标志位，其中 PREV_INUSE（0x1）表示？',
          score: 7,
          requiresTarget: false,
          type: 'single-choice',
          options: ['本 chunk 是否空闲', '前一个 chunk 是否在使用中', '是否由 mmap 分配', '是否属于主线程 arena'],
          answer: [1]
        },
        {
          id: 2,
          content: '关于 fastbin，以下说法正确的是？',
          score: 6,
          requiresTarget: false,
          type: 'single-choice',
          options: [
            'fastbin 使用双链表（fd+bk）管理空闲块',
            'fastbin free 后会与相邻空闲块合并',
            'fastbin 是单链表，LIFO，free 时通常不校验是否已释放',
            'fastbin 专门管理大块内存'
          ],
          answer: [2]
        },
        {
          id: 3,
          content: '一个 chunk 的 size 字段值为 0x91，则该 chunk 实际大小（含头部）为？',
          score: 7,
          requiresTarget: false,
          type: 'single-choice',
          options: ['0x91', '0x90', '0x88', '0x98'],
          answer: [1]
        }
      ]
    },
    {
      id: 2,
      name: '堆溢出原理与漏洞程序编写',
      description: '理解堆溢出成因，编写一个含堆溢出漏洞的 C 程序',
      score: 25,
      document: `## 堆溢出原理与漏洞程序编写

### 1. 堆溢出原理
堆溢出是指向堆 chunk 写入数据时**超过了该 chunk 的用户数据区边界**，从而覆盖了相邻 chunk 的头部（prev_size/size）或数据（fd/bk）。与栈溢出不同，堆溢出不会直接覆盖返回地址，而是通过破坏堆管理器的元数据，在后续 malloc/free 时触发任意写或控制流劫持。

### 2. 一个典型的堆溢出漏洞程序
在操作环境终端用 vim 编写 \`heap.c\`：

~~~c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void backdoor() {
    system("/bin/sh");
}

void init() {
    setvbuf(stdin, 0LL, 2, 0LL);
    setvbuf(stdout, 0LL, 2, 0LL);
    setvbuf(stderr, 0LL, 2, 0LL);
}

int main() {
    init();
    char *a = malloc(0x18);   // chunk A：用户区 0x18，实际 chunk 0x20
    char *b = malloc(0x18);   // chunk B
    char *c = malloc(0x18);   // chunk C
    puts("输入 A 的内容：");
    read(0, a, 0x40);         // 漏洞！只申请了 0x18，却读入 0x40，会溢出到 B 的头部
    free(b);                  // 触发利用
    return 0;
}
~~~

要点：
- \`a\` 申请 0x18 字节，但 \`read\` 读入 0x40 字节，多出的数据会覆盖 chunk B 的 prev_size、size、甚至 fd/bk。
- \`backdoor()\` 是预留后门，目标是让程序执行它。
- 编译时关闭保护：\`gcc -o heap heap.c -g -no-pie -z lazy\`（lazy 让 GOT 可写）。

### 3. 堆溢出的利用方向
堆溢出本身只是"能改相邻 chunk 的数据"，真正产生危害需要配合后续操作：
- **覆盖 fastbin chunk 的 fd**：实现 fastbin attack，malloc 到任意地址。
- **覆盖已释放 chunk 的 fd/bk**：触发 unlink，实现"把 P 的地址写入 P->fd 指向的位置"。
- **覆盖 chunk 的 size**：造成 chunk overlap（重叠），进一步操纵堆布局。

### 4. 调试技巧
用 pwndbg 调试堆：
- \`heap\`：查看所有堆块
- \`bins\`：查看各类 bin 的内容
- \`vis_heap_chunks\`：可视化堆布局
- \`p main_arena\`：查看主 arena

通过这些命令观察溢出前后 chunk B 的 fd/bk 变化，是理解利用过程的关键。`,
      questions: [
        {
          id: 1,
          content: '堆溢出与栈溢出的核心区别是？',
          score: 8,
          requiresTarget: false,
          type: 'single-choice',
          options: [
            '堆溢出直接覆盖返回地址',
            '堆溢出覆盖的是堆 chunk 的元数据/数据，需配合后续 malloc/free 才能产生危害',
            '堆溢出无法被利用',
            '栈溢出不能控制执行流'
          ],
          answer: [1]
        },
        {
          id: 2,
          content: '编译堆漏洞程序用于教学时，通常关闭的保护是？',
          score: 8,
          requiresTarget: false,
          type: 'single-choice',
          options: ['-O2 优化', '-no-pie 与 -z lazy', '-static 静态链接', '-fsanitize=address'],
          answer: [1]
        },
        {
          id: 3,
          content: '在 pwndbg 中查看 fastbin/smallbin 内容的命令是？',
          score: 9,
          requiresTarget: false,
          type: 'single-choice',
          options: ['heap', 'bins', 'vmmap', 'x/20gx'],
          answer: [1]
        }
      ]
    },
    {
      id: 3,
      name: 'unlink 利用与 fastbin attack',
      description: '掌握 unlink 任意写原理与 fastbin double free 攻击手法',
      score: 25,
      document: `## unlink 利用与 fastbin attack

### 1. unlink 是什么
当一个空闲 chunk 从双链表（smallbin/unsorted bin）中被摘除时，堆管理器执行 **unlink** 操作：

~~~text
P->fd->bk = P->bk;
P->bk->fd = P->fd;
~~~

即：让 P 的前驱（fd 指向的 chunk）的 bk 指向 P 的后继（bk 指向的 chunk），反之亦然，从而把 P 从链表中摘除。

### 2. unlink 利用原理（旧版 glibc）
如果我们可以伪造一个"已释放"的 chunk，并让其 fd/bk 指向我们控制的地址，那么 unlink 时：
- \`P->fd->bk = P->bk\` 等价于 \`*(P->fd + 0x18) = P->bk\`
- \`P->bk->fd = P->fd\` 等价于 \`*(P->bk + 0x10) = P->fd\`

若令 \`P->fd = &P - 0x18\`、\`P->bk = &P - 0x10\`（P 是某个全局指针，指向自身 chunk），则 unlink 后 \`P = &P - 0x18\`。此后向 P 写数据就等于从 \`&P - 0x18\` 开始写，可覆盖 GOT 表等关键位置。

**新版 glibc** 加入了 unlink 校验：\`P->fd->bk == P && P->bk->fd == P\`，上述简单伪造不再可行，需借助"已知 chunk 指针"的间接利用。

### 3. fastbin attack：double free
fastbin free 时不检查 chunk 是否已在链表中（旧版），可以**连续两次 free 同一个 chunk**：

~~~text
free(A);   // fastbin[0x20]: A
free(B);   // fastbin[0x20]: B -> A
free(A);   // fastbin[0x20]: A -> B -> A  （环！）
~~~

此时再 malloc 三次：
- 第1次 malloc 得到 A，可改写 A 的 fd
- 第2次 malloc 得到 B
- 第3次 malloc 得到 A（再次），但此时 fastbin 链表头是伪造的 fd 指向的地址
- 第4次 malloc 即可在**任意地址**分配 chunk（前提：该地址处伪造了合法 size）

### 4. fastbin attack 的应用
- **__malloc_hook 利用**：在 \`__malloc_hook\` 附近找一个能当作合法 size 的值（如 0x7f），伪造 chunk，malloc 到此处，写入 one_gadget 地址，触发 malloc 即 getshell。
- **GOT 改写**：malloc 到 GOT 表附近，改写某函数 GOT 为 system。

### 5. 关键前提
- 需要一个**堆地址泄露**（知道 chunk 指针或 libc 地址）才能构造 unlink。
- fastbin attack 需要目标地址附近存在"看起来合法"的 size 值（fastbin 范围内）。

这些泄露通常通过**格式化字符串漏洞**或**未初始化堆指针**获得，这也是各类漏洞常组合利用的原因。`,
      questions: [
        {
          id: 1,
          content: 'unlink 操作执行的链表摘除是？',
          score: 8,
          requiresTarget: false,
          type: 'single-choice',
          options: [
            'P->fd = P->bk; P->bk = P->fd;',
            'P->fd->bk = P->bk; P->bk->fd = P->fd;',
            'P->next = P->prev;',
            'P->fd->fd = P->bk;'
          ],
          answer: [1]
        },
        {
          id: 2,
          content: 'fastbin double free 能实现"任意地址分配 chunk"的关键是？',
          score: 9,
          requiresTarget: false,
          type: 'single-choice',
          options: [
            'free 时校验 chunk 是否已释放',
            'free 时不校验，可形成 A->B->A 环，再改 A 的 fd 指向目标地址',
            'fastbin 会自动合并相邻 chunk',
            'malloc 时会随机化返回地址'
          ],
          answer: [1]
        },
        {
          id: 3,
          content: '新版 glibc 在 unlink 中增加的校验是？',
          score: 8,
          requiresTarget: false,
          type: 'single-choice',
          options: [
            'P->size 必须为 0',
            'P->fd->bk == P 且 P->bk->fd == P',
            'P 必须在栈上',
            'P->fd 必须等于 P->bk'
          ],
          answer: [1]
        }
      ]
    },
    {
      id: 4,
      name: '实战 exp 编写与 getshell',
      description: '用 pwntools 编写堆溢出 exp，劫持控制流并读取 flag',
      score: 30,
      document: `## 实战 exp 编写与 getshell

### 1. 利用思路总览
以 fastbin attack 改写 \`__malloc_hook\` 为例：
1. 利用堆溢出构造 **double free**（A->B->A）。
2. 第1次 malloc 拿到 A，在 A 中伪造 fd 指向 \`__malloc_hook\` 附近的"伪 chunk"（size 为 0x7f）。
3. 连续 malloc 把链表推进到伪 chunk 位置。
4. 最后一次 malloc 返回 \`__malloc_hook\` 附近，写入 **one_gadget** 地址。
5. 触发 malloc（如再次申请大块）→ 跳转 one_gadget → getshell。

### 2. 寻找 one_gadget
在操作环境里用 \`one_gadget\` 工具扫描 libc，找到可直接 getshell 的 gadget 地址：

~~~bash
one_gadget libc.so.6
~~~

输出形如 \`0x4527a execve("/bin/sh", ...)\`，记录约束条件（如 [rsp+0x70] == NULL）。

### 3. pwntools exp 框架
~~~python
from pwn import *

context(arch='amd64', os='linux')
io = process('./heap')
libc = ELF('./libc.so.6')

def alloc(data):
    io.sendafter(b'内容：', data.ljust(0x18, b'\x00'))

# 1. 构造 double free
alloc(b'AAAA')     # A
alloc(b'BBBB')     # B
# 通过溢出 A 改 B 的 fd，或直接 free(A);free(B);free(A)

# 2. 拿到 A，写伪造 fd
alloc(p64(fake_chunk_addr))   # 让 fastbin 链指向 __malloc_hook 附近

# 3. 推进链表
alloc(b'CCCC')
alloc(b'DDDD')                 # 本次返回伪 chunk

# 4. 写 one_gadget 到 __malloc_hook
alloc(p64(one_gadget))

# 5. 触发 malloc
io.sendlineafter(b'内容：', b'trigger')
io.interactive()
~~~

### 4. getshell 后读取 flag
~~~bash
cat flag
~~~

若靶机是远程服务，将 \`process\` 改为 \`remote('host', port)\` 即可。

### 5. 调试与排查
- exp 不通时，用 \`gdb.attach(io)\` 在关键 malloc 前断下，检查 fastbin 链表是否符合预期。
- one_gadget 约束不满足时，换一个 gadget，或在触发前用 ROP 调整栈。
- 若 \`__malloc_hook\` 附近无合法 size，可改用 \`__free_hook\`（写入 system，free 一个内容为 "/bin/sh" 的 chunk）。

### 6. 提交 flag
在操作环境本地编译漏洞程序、编写 exp 成功 getshell 后，\`cat flag\` 读取你自己写入的 flag（如 flag{heap_pwned}），填到下方提交即可校验。`,
      questions: [
        {
          id: 1,
          content: '提交你成功利用堆溢出 getshell 后 cat flag 得到的 flag（格式 flag{...}）',
          score: 30,
          requiresTarget: true,
          type: 'open-ended-without-answer'
        }
      ]
    }
  ]
}
