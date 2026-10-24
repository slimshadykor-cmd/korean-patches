from pathlib import Path
import sys,json,struct,re,hashlib
R=Path(__file__).resolve().parent.parent;A=R.parent/'audit1024'
sys.path[:0]=[str(A/'tools'),str(A/'tools/deps')]
from xex_codec import unpack
import unicorn as u
from unicorn.ppc_const import *
sha=lambda b:hashlib.sha256(b).hexdigest()
old=bytes(unpack((A/'current/default.xex').read_bytes())[0])
b=bytes(unpack((R/'candidate/default.xex').read_bytes())[0])
report=json.loads((R/'audit/translation_build.json').read_text())
ranges=report['permitted_logical_ranges'];cursor=0
for start,end in sorted(ranges):
    assert old[cursor:start]==b[cursor:start];cursor=end
assert old[cursor:]==b[cursor:]
assert old[0xaa4b4:0x690000]==b[0xaa4b4:0x690000]
assert old[0x4ecd68:0x4ecd6c]==b[0x4ecd68:0x4ecd6c] and old[0x666900:0x666964]==b[0x666900:0x666964]

def db(image):
    base=0x5370000;magic,version,cap,used,fcount,fused=struct.unpack_from('>6I',image,base)
    assert magic==0x58444246 and used<=cap and fused<=fcount
    fbase=base+24+18*cap;data=fbase+8*fcount;entries={};spans=[]
    for i in range(used):
        ns,ident,off,size=struct.unpack_from('>HQII',image,base+24+i*18)
        assert (ns,ident) not in entries and data+off+size<=len(image)
        entries[ns,ident]=(off,size,image[data+off:data+off+size]);spans.append((off,off+size))
    spans.sort();assert all(spans[i][1]<=spans[i+1][0] for i in range(len(spans)-1))
    free=[]
    for i in range(fused):
        off,size=struct.unpack_from('>II',image,fbase+i*8)
        if size:
            assert all(off+size<=a or off>=z for a,z in spans)
            assert not any(image[data+off:data+off+size]);free.append((off,size))
    payload=entries[3,2][2];magic,version,declared,count=struct.unpack_from('>4sIIH',payload)
    assert (magic,version)==(b'XSTR',1) and declared+4==len(payload)
    strings={};pos=14
    for i in range(count):
        sid,n=struct.unpack_from('>HH',payload,pos);pos+=4
        assert sid not in strings and pos+n<=len(payload)
        strings[sid]=payload[pos:pos+n].decode('utf-8');pos+=n
    assert pos==len(payload) and len(strings)==128
    return entries,strings,free
oe,os,of=db(old);ne,ns,nf=db(b)
assert set(oe)==set(ne)
for key in oe:
    assert oe[key][0]==ne[key][0]
    if key!=(3,2):assert oe[key]==ne[key]
expected=json.loads((R/'audit/xstr_strings.json').read_text())
assert set(os)==set(ns)=={int(x['id'],16) for x in expected}
for x in expected:
    sid=int(x['id'],16);assert ns[sid]==x['korean'] and os[sid]==x['original']
    assert re.findall(r'\{[^{}]*\}',os[sid])==re.findall(r'\{[^{}]*\}',ns[sid])
    assert not re.search('[ぁ-ゖァ-ヺ一-龯ｦ-ﾝ]',ns[sid])
assert sum(os[k]!=ns[k] for k in os)==103 and len(nf)==1
achievements=json.loads((A/'results/xdbf_achievement_mapping.json').read_text())
resolved=[]
for x in achievements:
    if x['variant']!='current':continue
    resolved.append({'id':x['achievement_id'],**{k:ns[int(x[k],16)] for k in ['label_id','earned_description_id','unearned_description_id']}})
assert len(resolved)==27

def machine():
    uc=u.Uc(u.UC_ARCH_PPC,u.UC_MODE_64|u.UC_MODE_BIG_ENDIAN);uc.ctl_set_tlb_mode(u.UC_TLB_VIRTUAL);uc.reg_write(UC_PPC_REG_MSR,0)
    uc.mem_map(0x82000000,(len(b)+4095)&~4095);uc.mem_write(0x82000000,b);uc.mem_map(0x90000000,0x20000);uc.mem_map(0x91000000,0x2000)
    uc.reg_write(UC_PPC_REG_1,0x90010000);return uc
def read_wide(uc,ptr):
    raw=bytes(uc.mem_read(ptr,256));end=next(i for i in range(0,256,2) if raw[i:i+2]==b'\0\0')
    return raw[:end].decode('utf-16-be')
uc=machine();save=[]
for i,s in [(0,'게임 데이터'),(1,'의상 데이터'),(2,'오류 파일')]:
    uc.mem_write(0x91000000,b'\xcc'*0x1000);uc.reg_write(UC_PPC_REG_1,0x90010000);uc.reg_write(UC_PPC_REG_4,0x91000000);uc.reg_write(UC_PPC_REG_5,i);uc.reg_write(UC_PPC_REG_LR,0x90001000)
    uc.emu_start(0x822cf6f8,0x90001000,count=200000);assert uc.reg_read(UC_PPC_REG_PC)==0x90001000
    actual=read_wide(uc,0x91000000);assert actual==s
    save.append({'type':i,'actual':actual,'passed':True})
uc=machine();prompt=[]
def hook(uc,at,size,data):
    if at==0x824e5870:
        uc.reg_write(UC_PPC_REG_3,0);uc.reg_write(UC_PPC_REG_PC,uc.reg_read(UC_PPC_REG_LR))
    if at==0x824dc2f8:
        ptr=uc.reg_read(UC_PPC_REG_6)&0xffffffff;actual=read_wide(uc,ptr)
        assert ptr==0x82033e90 and actual=='의상 이름을 입력해 주세요.';prompt.append(actual)
        uc.reg_write(UC_PPC_REG_3,0x3e5);uc.reg_write(UC_PPC_REG_PC,uc.reg_read(UC_PPC_REG_LR))
uc.hook_add(u.UC_HOOK_CODE,hook);uc.reg_write(UC_PPC_REG_31,0x91000000)
uc.emu_start(0x82280614,0x82280954,count=1000);assert len(prompt)==1
result={'version':'1.3.0','confirmed_records_resolved':107,'xdbf_strings_read':128,'unchanged_english_records':25,'achievement_definitions_unchanged':27,'achievement_text_references_resolved':81,'resource_offsets_and_nonstring_blocks_unchanged':True,'non_text_game_code_unchanged':True,'loading_code_byte_identical':True,'free_regions_nonoverlapping':True,'free_regions':nf,'save_function_probes':save,'keyboard_prompt':prompt,'actual_powerpc_instructions_executed':True,'platform_calls_stubbed':True,'platform_ui_rendered':False,'xenia_gameplay_performed':False}
(R/'audit/text_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
(R/'audit/achievement_resolution.json').write_text(json.dumps(resolved,ensure_ascii=False,indent=2));print(result,flush=True)
