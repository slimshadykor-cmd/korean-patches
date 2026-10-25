.intel_syntax noprefix
.section .text
.global ensure_chooser,ensure_costumes,current_profile

ensure_chooser:
 mov eax,offset chooser_profile
 jmp ensure_profile
ensure_costumes:
 mov eax,offset costume_profile
ensure_profile:
 push ebx
 push esi
 push edi
 push ebp
 mov ebp,eax
 cmp dword ptr [current_profile],eax
 jne switch_profile
 cmp dword ptr [0xe0498c],1
 je ensure_ok
switch_profile:
 cmp dword ptr [0xe049e8],0
 je allocate
 call 0xf40df2
allocate:
 mov dword ptr [current_profile],ebp
 push 0xb6800000
 push dword ptr [ebp]
 call 0x32bd3e
 test eax,eax
 jz ensure_return
 mov dword ptr [0xe049e8],eax
 mov ebx,eax
 mov edi,eax
 mov ecx,0x200
 xor eax,eax
 cld
 rep stosd
 mov edi,ebx
 mov esi,dword ptr [ebp+4]
 mov ecx,dword ptr [ebp+8]
 shr ecx,2
 rep movsd
 mov edx,dword ptr [ebp+12]
 lea edi,[ebx+0x800]
copy_payload:
 mov esi,dword ptr [edx]
 test esi,esi
 jz parse
 mov ecx,dword ptr [edx+4]
 shr ecx,2
 rep movsd
 add edx,8
 jmp copy_payload
parse:
 mov edi,offset temporary_resources
 mov ecx,12
 xor eax,eax
 rep stosd
 # The private object must never unregister the game's global sprite slots.
 mov dword ptr [0xe049a8],0
 mov dword ptr [0xe049b0],6
 mov eax,ebx
 mov ecx,0xe04980
 push dword ptr [ebp+16]
 push 0xe049e4
 push offset temporary_resources
 call 0x21aac0
 test eax,eax
 jne failed
 mov eax,dword ptr [ebp+16]
 cmp dword ptr [0xe049e4],eax
 jne failed
 mov edi,0xe049b4
 mov ecx,12
 xor eax,eax
 rep stosd
 mov esi,offset temporary_resources
 mov eax,dword ptr [ebp+20]
 lea edi,[eax*8+0xe049b4]
 mov ecx,dword ptr [ebp+16]
 shl ecx,1
 rep movsd
ensure_ok:
 mov eax,1
 jmp ensure_return
failed:
 # Expose resources already returned by the parser so release waits for them.
 mov esi,offset temporary_resources
 mov edi,0xe049b4
 mov ecx,12
 rep movsd
 call 0xf40df2
 xor eax,eax
ensure_return:
 pop ebp
 pop edi
 pop esi
 pop ebx
 ret

.balign 16
current_profile: .long 0
temporary_resources: .zero 48
chooser_profile:
 .long CHOOSER_SIZE,chooser_header,chooser_header_end-chooser_header,chooser_payload,2,0
costume_profile:
 .long COSTUME_SIZE,costume_header,costume_header_end-costume_header,costume_payload,3,2
chooser_payload:
 .long TEX0_SOURCE,0x80400,TEX1_SOURCE,0x480,0,0
costume_payload:
 .long TEX2_SOURCE,0x20400,TEX3_SOURCE,0x20400,TEX4_SOURCE,0x20400,0,0
chooser_header:
 .incbin "hakux_audit/chooser_header.bin"
chooser_header_end:
costume_header:
 .incbin "hakux_audit/costume_header.bin"
costume_header_end:
