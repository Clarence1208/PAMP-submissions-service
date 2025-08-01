# Sample Assembly program
.section .data
    hello_msg: .ascii "Hello, World!\n"
    hello_len = . - hello_msg

.section .text
    .global _start

_start:
    # Write system call
    mov $1, %rax        # sys_write
    mov $1, %rdi        # stdout
    mov $hello_msg, %rsi # message
    mov $hello_len, %rdx # message length
    syscall

    # Exit system call
    mov $60, %rax       # sys_exit
    mov $0, %rdi        # exit status
    syscall 