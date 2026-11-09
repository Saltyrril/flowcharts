; Поиск максимума в массиве (NASM, x86)
section .data
arr dd 5, 9, 2, 7
n   equ 4

section .text
global _start

_start:
    mov esi, arr
    mov ecx, n
    mov eax, [esi]        ; max = arr[0]
    add esi, 4
    dec ecx
.loop:
    cmp ecx, 0
    je .done
    mov ebx, [esi]
    cmp ebx, eax
    jle .next
    mov eax, ebx
.next:
    add esi, 4
    dec ecx
    jmp .loop
.done:
    call print_num
    mov eax, 1
    int 0x80

; Печать числа
print_num:
    push eax
    test eax, eax
    jnz .nz
    mov eax, 0
.nz:
    pop eax
    ret
