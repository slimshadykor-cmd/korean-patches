.intel_syntax noprefix
.code32
.section .text
.global mark_text_gate
# Called instead of the existing text draw, preserving its exact stack argument.
mark_text_gate:
 push dword ptr [esp+4]
 call 0x1e6d30
 add esp,4
 pushfd
 pushad
 sub esp,0x60
 mov esi,[ebp+8]
 cmp byte ptr [esi+0x75],1
 ja mark_done
 movss xmm0,[ebp+12]
 comiss xmm0,[zero]
 jbe mark_done
 mov eax,[ebp-4]
 add eax,133
 cmp eax,-20
 jl mark_done
 cmp eax,480
 jg mark_done
 # Reserve queue room for the remaining native menu labels and controls.
 mov eax,[0x8f7df8]
 sub eax,[0x8f7dfc]
 cmp eax,229
 jb mark_done
 movzx eax,byte ptr [esi+0x75]
 mov [esp+0x30],eax
 call 0xe0459a
 test eax,eax
 jz mark_done
 # Only borrowing the same texture registry entries as the established menu.
 movups xmm0,[0x8dbb28]
 movups [esp+0x40],xmm0
 movups xmm0,[0xe049b4]
 movups [0x8dbb28],xmm0
 mov eax,offset black_rects
 mov edx,0x00e5e7eb
 cmp dword ptr [esp+0x30],0
 je mark_selected
 mov eax,offset storm_rects
 mov edx,0x00e8c879
mark_selected:
 mov ecx,[eax]
 add eax,4
 mov [esp+0x34],eax
 mov [esp+0x38],ecx
 # Clamp and inherit slot fade alpha; never mutate the active mode or save.
 movss xmm0,[ebp+12]
 maxss xmm0,[zero]
 minss xmm0,[one]
 movss [esp+0x3c],xmm0
 mov dword ptr [esp],0x7fff
 mov dword ptr [esp+8],0x010001ca
 mov dword ptr [esp+0xc],1
 mov dword ptr [esp+0x10],0
 mov dword ptr [esp+0x1c],0x3f800000
 mov dword ptr [esp+0x20],0x3f800000
 mov dword ptr [esp+0x24],0
mark_loop:
 mov esi,[esp+0x34]
 movzx eax,byte ptr [esi]
 add eax,115
 mov word ptr [esp+4],ax
 movzx eax,byte ptr [esi+1]
 add eax,[ebp-4]
 add eax,133
 mov word ptr [esp+6],ax
 movzx eax,byte ptr [esi+2]
 cvtsi2ss xmm0,eax
 movss [esp+0x14],xmm0
 movzx eax,byte ptr [esi+3]
 cvtsi2ss xmm0,eax
 movss [esp+0x18],xmm0
 mov eax,[esi+4]
 mov ecx,eax
 shr ecx,24
 cvtsi2ss xmm0,ecx
 mulss xmm0,[esp+0x3c]
 cvttss2si ecx,xmm0
 shl ecx,24
 and eax,0x00ffffff
 or eax,ecx
 mov [esp+0x28],eax
 mov edi,esp
 call 0x221340
 add dword ptr [esp+0x34],8
 dec dword ptr [esp+0x38]
 jnz mark_loop
 movups xmm0,[esp+0x40]
 movups [0x8dbb28],xmm0
mark_done:
 add esp,0x60
 popad
 popfd
 ret
.balign 4
zero: .float 0
one: .float 1
alpha_scale: .float 255
.include "mark_release/rects.inc"
