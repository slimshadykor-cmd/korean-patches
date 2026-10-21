from audit_common import *
import numpy as np,re,collections
def entries(b,stride=12):
 first=struct.unpack_from('>I',b)[0];out=[]
 for i in range(first//stride+1):
  at,n=struct.unpack_from('>II',b,i*stride)
  if at==0xffffffff:assert n==0xffffffff;return out
  nameptr=struct.unpack_from('>I',b,i*stride+8)[0] if stride==12 else 0
  assert at+n<=len(b)
  name=cstr(b,nameptr).decode('ascii') if nameptr else str(i)
  out.append((at,n,nameptr,name))
 raise AssertionError('no sentinel')
def changed(o,c):assert len(o)==len(c);return np.flatnonzero(np.frombuffer(o,'u1')!=np.frombuffer(c,'u1'))
mission=[]
for p in sorted((W/'original/Media/Mission').glob('*.xmg')):
 o=p.read_bytes();q=W/'candidate/Media/Mission'/p.name;c=q.read_bytes() if q.exists() else o
 start,count=struct.unpack_from('>II',o,0x38);assert (start,count)==struct.unpack_from('>II',c,0x38)
 mask=np.zeros(len(o),dtype=bool)
 for i in range(count):mask[start+i*0x110:start+i*0x110+256]=True
 diff=changed(o,c);bad=[int(x) for x in diff if not mask[x]];assert not bad,(p,bad[:20])
 mission.append({'file':p.name,'message_slots':count,'changed_bytes':len(diff),'non_message_bytes_preserved':True})
writej('mission_structure_verified.json',{'missions':mission,'count':len(mission),'changed_files':sum(x['changed_bytes']>0 for x in mission)})
records=json.loads((W/'recovered/v125/source/translation_records.json').read_text());menus=[]
for name in sorted({r['archive'] for r in records}):
 o=(W/'original/Media/Menu'/name).read_bytes();c=(W/'candidate/Media/Menu'/name).read_bytes();oe=entries(o);ce=entries(c);assert len(oe)==len(ce)
 nr=0;untouched=0
 for i,((at,n,no,leaf),(ca,cn,cno,cleaf)) in enumerate(zip(oe,ce)):
  assert (no,leaf)==(cno,cleaf);old=o[at:at+n];cur=c[ca:ca+cn];rs=[r for r in records if r['archive']==name and r['entry']==leaf]
  if not rs:assert old==cur;untouched+=1;continue
  if rs[0]['kind']=='customize description':
   assert len(rs)==1;end=old.index(0,8);ne=cur.index(0,8)
   assert cur[:6]==old[:6] and old[end+1:]==cur[ne+1:]
   assert struct.unpack_from('<H',cur,6)[0]==ne-8+1
   assert decoded(cur[8:ne])==rs[0]['korean']
  else:
   assert len(cur)>=len(old);mask=np.zeros(len(old),dtype=bool)
   for r in rs:
    field=r['pointer_field'];mask[field:field+4]=True;pos=struct.unpack_from('>I',cur,field)[0];end=cur.index(0,pos)
    assert decoded(cur[pos:end])==r['korean'] and cur[pos-4:pos-2]==b'\x08\0'
    assert struct.unpack_from('<H',cur,pos-2)[0]==end-pos+1
   assert not any(not mask[x] for x in changed(old,cur[:len(old)]))
  nr+=len(rs)
 menus.append({'archive':name,'entries':len(oe),'display_records':nr,'unchanged_resources':untouched,'all_resource_names_and_nontext_fields_preserved':True})
writej('menu_structure_verified.json',{'archives':menus,'display_records':sum(x['display_records'] for x in menus)})
demo=[]
for p in sorted((W/'original/Media/Demo').glob('*.cat')):
 o=p.read_bytes();q=W/'candidate/Media/Demo'/p.name
 if not q.exists():
  assert p.name=='csb.cat';continue
 c=q.read_bytes();mask=np.zeros(len(o),dtype=bool);blocks=[]
 oe=entries(o,8);assert oe==entries(c,8);base,size,_,_=oe[0]
 start,stride,count,tail=struct.unpack_from('>IIII',o,base);assert start==16 and stride==44
 pool=base+start+stride*count
 rows=[struct.unpack_from('>11I',o,base+start+i*stride) for i in range(count)]
 animation_offsets=[r[2] for r in rows if r[2]!=0xffffffff]
 pool_end=pool+min(animation_offsets) if animation_offsets else base+tail
 assert pool<=pool_end<=base+size
 mask[pool:pool_end]=True
 for i,r in enumerate(rows):
  field=base+start+i*stride+16;new_offset=struct.unpack_from('>I',c,field)[0]
  if r[4]==0xffffffff:assert new_offset==r[4];continue
  mask[field:field+4]=True
  a=pool+r[4];b=pool+new_offset
  assert pool<=a<pool_end and pool<=b<pool_end
  text=cstr(o,a);translated=cstr(c,b)
  assert a+len(text)<pool_end and b+len(translated)<pool_end
  blocks.append({'record':i,'original_text_offset':hex(a),'current_text_offset':hex(b),'original':text.decode('cp932'),'current':decoded(translated)})
 diff=changed(o,c);unexplained=[int(x) for x in diff if not mask[x]];assert not unexplained,(p,runs(unexplained)[:10])
 demo.append({'file':p.name,'dialogue_records':blocks,'text_pool':[hex(pool),hex(pool_end)],'unexplained_changes':runs(unexplained),'changed_bytes':len(diff),'speaker_ids_timing_animation_and_other_archive_entries_preserved':True})
writej('demo_structure_audit.json',demo)
print('missions',len(mission),'modified',sum(x['changed_bytes']>0 for x in mission),'menus',len(menus),'records',sum(x['display_records'] for x in menus),'demo',len(demo),'texts',sum(len(x['dialogue_records']) for x in demo),'unexplained_demo',[(x['file'],x['unexplained_changes'][:10]) for x in demo if x['unexplained_changes']])
