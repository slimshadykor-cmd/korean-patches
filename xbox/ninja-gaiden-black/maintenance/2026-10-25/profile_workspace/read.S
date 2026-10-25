.intel_syntax noprefix
.code32
.section .text
.global profile_workspace_gate,profile_workspace
profile_workspace_gate:
 pushfd
 cmp dword ptr [esp+8],1
 jne native
 cmp dword ptr [esp+16],0xdb9380
 jne native
 cmp dword ptr [esp+20],0x508
 jne native
 cmp dword ptr [esp+24],0x1da9e0
 jne native
 cmp dword ptr [esp+28],0
 jne native
 mov dword ptr [esp+28],offset profile_workspace
 mov dword ptr [esp+32],0x4000
native:
 popfd
 sub esp,0x30c
 jmp 0x30fce6
.balign 16
profile_workspace:
 .fill 0x4000,1,0
