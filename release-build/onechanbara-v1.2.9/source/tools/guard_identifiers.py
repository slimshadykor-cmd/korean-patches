from audit_common import *
import numpy as np
orig=(W/'original.memory.bin').read_bytes();current=(W/'current.memory.bin').read_bytes();fixed=(W/'candidate.memory.bin').read_bytes()
protected=[{'name':'bracelet classification prefix','at':0x34e98,'size':8},{'name':'goddess classification substring','at':0x34eb8,'size':8},{'name':'destructible classification substring','at':0x34eb0,'size':8},{'name':'enemy model attachment and prop definitions','at':0x6e30c0,'size':0x6e4860-0x6e30c0},{'name':'item ID/key/display-pointer table','at':0x6e4860,'size':35*16}]
for i in range(35):
 at=struct.unpack_from('>I',orig,0x6e4860+i*16+4)[0]-0x82000000
 protected.append({'name':'item resource key '+str(i),'at':at,'size':len(cstr(orig,at))+1,'text':cstr(orig,at).decode('cp932')})
for i in range(96):protected.append({'name':'area lookup metadata and filename '+str(i),'at':0x6e12f8+i*76,'size':44})
for at in range(0x2b008,0x2b060,16):
 raw=cstr(orig,at)
 if raw.startswith('イベントキー'.encode('cp932')):protected.append({'name':'event key '+str(at),'at':at,'size':len(raw)+1,'text':raw.decode('cp932')})
result={}
for version,b in [('v128',current),('candidate',fixed)]:
 failed=[r for r in protected if b[r['at']:r['at']+r['size']]!=orig[r['at']:r['at']+r['size']]]
 result[version]={'protected_checks':len(protected),'failed':failed}
assert not result['v128']['failed']
assert not result['candidate']['failed']
writej('protected_identifiers_regression.json',{'checks':protected,'results':result})
# Account for every logical executable modification, rather than trusting the old text classification.
mask=np.zeros(len(orig),dtype=bool)
records=json.loads((W/'workbench/analysis/ingame_v006/translation_records.json').read_text())
for r in records:
 at=int(r['memory_offset'],16);mask[at:at+r['original_slot_bytes']]=True
for a,b in [(0x151a4,0x15220),(0x34ed0,0x34ee4)]:mask[a:b]=True
relocations=[(0x6bdba8,0x27e10,0x3c9d4),(0x6bdb98,0x27e34,0x3bc90),(0x6bdb90,0x27e48,0x3c9e0),(0x6bd49c,0x2c698,0x3bca4),(0x6bd498,0x2c69c,0x3bcac)]
for ptr,old,new in relocations:
 assert struct.unpack_from('>I',orig,ptr)[0]==0x82000000+old
 assert struct.unpack_from('>I',current,ptr)[0]==0x82000000+new
 mask[ptr:ptr+4]=True
for i in range(96):mask[0x6e12f8+i*76+44:0x6e12f8+i*76+76]=True
changes=np.flatnonzero(np.frombuffer(orig,'u1')!=np.frombuffer(current,'u1'));unknown=[int(x) for x in changes if not mask[x]]
assert not unknown
assert orig[0xd0000:0x6668ec]==current[0xd0000:0x6668ec]
loading_allowed=set(range(0x230,0x234))|set(range(0x4ecd68,0x4ecd6c))|set(range(0x666900,0x666964))
loading_changes=np.flatnonzero(np.frombuffer(fixed,"u1")!=np.frombuffer(current,"u1"))
assert set(loading_changes)<=loading_allowed and len(loading_changes)==90
writej("logical_diff_complete_accounting.json",{"translation_records":len(records),"unaccounted_translation_bytes":unknown,"loading_changed_bytes":len(loading_changes),"loading_changes_within_entry_wrapper_and_text_size_only":True,"no_other_logic_data_or_timing_constants_changed":True})
print({v:r["protected_checks"] for v,r in result.items()})
