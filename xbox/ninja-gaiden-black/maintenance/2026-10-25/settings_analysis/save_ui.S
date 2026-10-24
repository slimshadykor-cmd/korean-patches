.intel_syntax noprefix
.code32
.section .text
.global preview_mode, slot_draw, profile_read, ko_warning, en_warning, ko_digit, en_digit
preview_mode:
 pushfd
 pushad
 xor eax,eax
 cmp edi,0x572f40
 jne saved_mode
 mov eax,dword ptr [0xe04274]
 and eax,1
 jmp cache_mode
saved_mode:
 call classify_save
cache_mode:
 mov byte ptr [esi+0x75],al
 mov word ptr [esi+0x76],0x4d53
 popad
 popfd
 ret

# Exact original call arguments, then independent overlay; no save mutations.
slot_draw:
 push ebp
 mov ebp,esp
 sub esp,16
 mov [ebp-4],eax
 push dword ptr [ebp+12]
 push dword ptr [ebp+8]
 call 0x229f20
 add esp,8
 pushfd
 pushad
 sub esp,0x270
 and esp,-16
 fxsave [esp+0x60]
 mov esi,[ebp+8]
 cmp byte ptr [esi+0x1c],1
 jne draw_done
 cmp word ptr [esi+0x76],0x4d53
 jne draw_done
 mov ecx,offset black_ko
 cmp dword ptr [0xdb9890],0
 je choose_ko
 mov ecx,offset black_en
 cmp byte ptr [esi+0x75],2
 jne 6f
 mov ecx,offset unknown_en
 jmp chosen
6:
 cmp byte ptr [esi+0x75],1
 jne chosen
 mov ecx,offset storm_en
 jmp chosen
choose_ko:
 cmp byte ptr [esi+0x75],2
 jne 5f
 mov ecx,offset unknown_ko
 jmp chosen
5:
 cmp byte ptr [esi+0x75],1
 jne chosen
 mov ecx,offset storm_ko
chosen:
 mov eax,esp
 mov edx,[ebp-4]
 add edx,143
 push 2
 push 0x1ca
 push edx
 push 164
 call 0x168730
 add esp,16
 mov byte ptr [esp+0x4a],0x11
 mov dword ptr [esp+0x1c],0x3f333333
 mov dword ptr [esp+0x20],0x3f333333
 mov eax,[ebp+12]
 mov [esp+0x14],eax
 push esp
 call 0x1e6d30
 add esp,4
draw_done:
 fxrstor [esp+0x60]
 lea esp,[ebp-52]
 popad
 popfd
 mov esp,ebp
 pop ebp
 ret

# Observe error without changing the native warning, validation, or write policy.
profile_read:
 pushfd
 pushad
 cmp dword ptr [esp+0x34c],0xdb9380
 jne profile_done
 cmp dword ptr [esp+0x350],0x508
 jne profile_done
 mov dword ptr [last_profile_status],ebp
profile_done:
 popad
 popfd
 jmp 0xe04350
.balign 4
black_ko: .byte 0x8b,0xdd,0x8a,0xa5,0
storm_ko: .byte 0x8e,0xea,0x8e,0xf5,0
black_en: .asciz "BLACK"
storm_en: .asciz "STORM"
ko_warning:
 .incbin "settings_analysis/ko_prefix.bin"
ko_digit:
 .incbin "settings_analysis/ko_suffix.bin"
 .byte 0x0a
 .byte 0x82,0x76,0x81,0x46
warning_digits: .fill 8,2,0x4881
 .byte 0x20,0x82,0x71,0x81,0x46
read_digits: .fill 8,2,0x4881
 .byte 0
en_warning: .ascii "Unable to load game settings.\nSettings will be reset.\nPress A to continue.\nW:"
en_digit: .ascii "????????"
 .ascii " R:"
en_read: .asciz "????????"
.global common_write, restore_mode, classify_save
common_write:
 pushfd
 pushad
 cmp dword ptr [esp+44],0x572f40
 jne 1f
 cmp dword ptr [esp+48],0x17460
 jne 1f
 call 0xe04280
1: popad
 popfd
 sub esp,0x5c
 mov eax,dword ptr [0x41ccd8]
 jmp 0x30f9d8

# Valid metadata is authoritative. Legacy Storm scroll is fallback evidence.
# EDI=state buffer; EAX=0 Black,1 Storm,2 unmarked/unknown.
classify_save:
 cmp dword ptr [edi+0x17454],0x5342474e
 jne legacy_mode
 cmp dword ptr [edi+0x17458],0x314d5254
 jne unknown_mode
 movzx ecx,word ptr [edi+0x1745c]
 test ecx,0xfff8
 jne unknown_mode
 mov dx,cx
 not dx
 cmp dx,word ptr [edi+0x1745e]
 jne unknown_mode
 mov eax,ecx
 and eax,1
 ret
legacy_mode:
 lea edx,[edi+0x16290]
 mov ecx,128
7:
 cmp word ptr [edx],316
 jne 8f
 cmp byte ptr [edx+2],0
 je 8f
 mov eax,1
 ret
8: add edx,4
 loop 7b
unknown_mode:
 mov eax,2
 ret
restore_mode:
 pushfd
 pushad
 mov edi,0x572f40
 call classify_save
 cmp eax,2
 jne 9f
 xor eax,eax
9: mov [esp+28],eax
 popad
 popfd
 jmp 0xe04080
unknown_en: .asciz "UNMARKED"
unknown_ko: .incbin "settings_analysis/unknown_ko.bin"

.global warning_enter, warning_digits, read_digits, last_profile_status
warning_enter:
 pushfd
 pushad
 mov edx,ebx
 mov edi,offset warning_digits
 mov esi,offset en_digit
 call hex_status
 mov edx,dword ptr [last_profile_status]
 mov edi,offset read_digits
 mov esi,offset en_read
 call hex_status
 popad
 popfd
 mov ebx,0x100
 mov ebp,1
 jmp 0x168941
hex_status:
 mov ecx,8
10:
 rol edx,4
 mov eax,edx
 and eax,15
 cmp eax,10
 jb 11f
 add eax,7
11:
 add eax,0x30
 mov [esi],al
 inc esi
 cmp al,0x39
 jbe 12f
 add al,0x1f
 jmp 13f
12: add al,0x1f
13:
 mov byte ptr [edi],0x82
 mov [edi+1],al
 add edi,2
 loop 10b
 ret
last_profile_status: .long 0xeeeeeeee
.global common_read_success
common_read_success:
 call 0x311140
 pushfd
 pushad
 cmp dword ptr [esp+0x1f8],0x572f40
 jne 1f
 cmp dword ptr [esp+0x1fc],0x17460
 jne 1f
 call 0xe042c7
1: popad
 popfd
 ret
