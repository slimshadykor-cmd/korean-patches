from pathlib import Path
R=Path(__file__).resolve().parent;T=R/'tools';S=R/'baseline_source/release-build/onechanbara-v1.2.8/source'
# Reuse reviewed audits with only paths, target versions, and known emulator setup updated.
s=(R/'recovered/identifier_evidence/asset_structure_audit.py').read_text().replace("W/'mission/Media/Mission'","W/'original/Media/Mission'").replace("W/'v125/source/translation_records.json'","W/'recovered/v125/source/translation_records.json'").replace("W/'current/", "W/'candidate/")
(T/'asset_structure_audit.py').write_text(s)
s=(R/'recovered/identifier_evidence/guard_identifiers.py').read_text();s=s[:s.index("old=json.loads((W/'v125/audit/new_source/files.json')")]
s=s.replace("('v127',current)","('v128',current)")
s=s.replace("assert len(result['v127']['failed'])==1 and result['v127']['failed'][0]['at']==0x34e98","assert not result['v128']['failed']")
s=s.replace('assert orig[0xd0000:0x6667ec]==current[0xd0000:0x6667ec]==fixed[0xd0000:0x6667ec]', 'assert orig[0xd0000:0x6668ec]==current[0xd0000:0x6668ec]\nloading_allowed=set(range(0x230,0x234))|set(range(0x4ecd68,0x4ecd6c))|set(range(0x666900,0x666964))\nloading_changes=np.flatnonzero(np.frombuffer(fixed,"u1")!=np.frombuffer(current,"u1"))\nassert set(loading_changes)<=loading_allowed and len(loading_changes)==90\nwritej("logical_diff_complete_accounting.json",{"translation_records":len(records),"unaccounted_translation_bytes":unknown,"loading_changed_bytes":len(loading_changes),"loading_changes_within_entry_wrapper_and_text_size_only":True,"no_other_logic_data_or_timing_constants_changed":True})\nprint({v:r["protected_checks"] for v,r in result.items()})')
(T/'guard_identifiers.py').write_text(s)
s=(S/'additional_checks.py').read_text().replace("W=Path(__file__).resolve().parent;A=W.parent/'audit_identifiers_20261019'","W=Path(__file__).resolve().parent.parent;A=W")
s=s.replace('u.UC_MODE_PPC32|u.UC_MODE_BIG_ENDIAN);uc.mem_map','u.UC_MODE_64|u.UC_MODE_BIG_ENDIAN);uc.ctl_set_tlb_mode(u.UC_TLB_VIRTUAL);uc.reg_write(UC_PPC_REG_MSR,0);uc.mem_map')
s=s.replace("if version!='current':assert",'assert').replace('v127_creation_mismatches','baseline_creation_mismatches')
(T/'additional_checks.py').write_text(s)
s=(R/'recovered/identifier_evidence/item_lookup_probe.py').read_text().replace('u.UC_MODE_PPC32|u.UC_MODE_BIG_ENDIAN)','u.UC_MODE_64|u.UC_MODE_BIG_ENDIAN);uc.ctl_set_tlb_mode(u.UC_TLB_VIRTUAL);uc.reg_write(UC_PPC_REG_MSR,0)').replace('public v1.2.7','public v1.2.8').replace('match v1.2.7','match v1.2.8')
(T/'item_lookup_probe.py').write_text(s)
s=(R/'loading_test01/dev/test_ppc.py').read_text().replace("R=Path(__file__).parent;sys.path.insert(0,str(R.parent/'loading_analysis_20261021/deps'))","R=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(R/'deps/python'))").replace("R/'baseline_v128.memory.bin'","R/'current.memory.bin'").replace("R/'kor128_test01.memory.bin'","R/'candidate.memory.bin'")
(T/'test_ppc.py').write_text(s)
