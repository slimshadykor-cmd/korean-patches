.intel_syntax noprefix
.section .text
.global ensure_badge,ensure_scroll,release_compact,scene_gate,white_record,scroll_record

ensure_badge:
 mov eax,offset white_record
 jmp ensure_compact
ensure_scroll:
 mov eax,offset scroll_record
ensure_compact:
 push ebx
 push esi
 push edi
 push ebp
 mov ebp,eax
 cmp dword ptr [ebp+16],1
 je ensure_ok
 cmp dword ptr [ebp],0
 jne ensure_failed
 push 0xb6800000
 push dword ptr [ebp+124]
 call 0x32bd3e
 test eax,eax
 jz ensure_return
 mov dword ptr [ebp],eax
 mov ebx,eax
 mov edi,eax
 mov ecx,dword ptr [ebp+124]
 shr ecx,2
 xor eax,eax
 cld
 rep stosd
 mov edi,ebx
 mov esi,dword ptr [ebp+128]
 mov ecx,dword ptr [ebp+132]
 shr ecx,2
 rep movsd
 lea edi,[ebx+0x800]
 mov esi,WHITE_SOURCE
 mov ecx,0x120
 rep movsd
 cmp dword ptr [ebp+136],2
 jne register_art
 mov esi,SCROLL_SOURCE
 mov ecx,0x4100
 rep movsd
register_art:
 lea ecx,[ebp+4]
 mov eax,ebx
 push dword ptr [ebp+136]
 lea edx,[ebp+120]
 push edx
 lea edx,[ebp+104]
 push edx
 call 0x21aac0
 test eax,eax
 jne ensure_failed
 mov eax,dword ptr [ebp+136]
 cmp dword ptr [ebp+120],eax
 jne ensure_failed
 # Preserve original sprite texture indices: white=1, scroll=5.
 mov eax,dword ptr [ebp+104]
 mov dword ptr [ebp+64],eax
 mov eax,dword ptr [ebp+108]
 mov dword ptr [ebp+68],eax
 cmp dword ptr [ebp+136],2
 jne ensure_ok
 mov eax,dword ptr [ebp+112]
 mov dword ptr [ebp+96],eax
 mov eax,dword ptr [ebp+116]
 mov dword ptr [ebp+100],eax
ensure_ok:
 mov eax,1
 jmp ensure_return
ensure_failed:
 mov eax,ebp
 call release_compact
 xor eax,eax
ensure_return:
 pop ebp
 pop edi
 pop esi
 pop ebx
 ret

# EAX=record. Texture count in each private object is permanently zero so
# native unregister (including its parser-failure path) cannot clear global
# sprite slots. Parser receives its actual count as an explicit argument.
release_compact:
 push ebx
 push esi
 push edi
 push ebp
 mov ebp,eax
 mov ebx,dword ptr [ebp]
 test ebx,ebx
 jz release_done
 lea esi,[ebp+4]
 call 0x21aa10
 lea esi,[ebp+104]
 lea edi,[esi+16]
release_wait:
 mov eax,dword ptr [esi]
 test eax,eax
 jz release_next
 call 0x3cadf0
release_next:
 add esi,4
 cmp esi,edi
 jb release_wait
 push 0xb6800000
 push ebx
 call 0x32bdde
 xor eax,eax
 mov dword ptr [ebp],eax
 lea edi,[ebp+56]
 mov ecx,17
 cld
 rep stosd
release_done:
 pop ebp
 pop edi
 pop esi
 pop ebx
 ret

scene_gate:
 pushfd
 pushad
 mov ebp,esp
 sub esp,528
 and esp,-16
 fxsave [esp]
 mov dword ptr [0xe044e8],0
 call RELEASE_LARGE
 mov eax,offset white_record
 call release_compact
 mov eax,offset scroll_record
 call release_compact
 fxrstor [esp]
 mov esp,ebp
 popad
 popfd
 cmp byte ptr [0xdb9888],0xc
 jmp 0x21a9b7

.balign 16
white_record:
 .long 0
 # Native object, 13 dwords. Private texture count(+28)=0, sprite count(+30)=1.
 .long 0,0,0,0,0,0,0,0,0,0,0,0,1
 .zero 48
 .zero 16
 .long 0,0xc80,white_header,white_header_end-white_header,1,0
scroll_record:
 .long 0
 .long 0,0,0,0,0,0,0,0,0,0,0,0,2
 .zero 48
 .zero 16
 .long 0,0x11080,scroll_header,scroll_header_end-scroll_header,2,0
white_header:
 .incbin "save_crash_fix/white_header.bin"
white_header_end:
scroll_header:
 .incbin "save_crash_fix/scroll_header.bin"
scroll_header_end:
