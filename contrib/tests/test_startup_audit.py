#!/usr/bin/env python3
"""Meaningful failure/acceptance and SmartAI topology regressions."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'contrib/tools'))
from worldserver_log_audit import audit,normalize
from smartai_graph_audit import validate
from script_binding_audit import build,uncomment
from worldserver_bootstrap_probe import check_config


class StartupAuditTest(unittest.TestCase):
    def test_ready_is_not_success(self):
        report=audit('(worldserver-daemon) ready...\nserver shutdown 1\nHalting process...\nSegmentation fault (core dumped)',exit_code=139)
        self.assertEqual(report['acceptance'],'FAIL');self.assertFalse(report['normal_exit_verified'])

    def test_process_exit_evidence_required(self):
        log='(worldserver-daemon) ready...\nserver shutdown 1\nHalting process...'
        self.assertEqual(audit(log)['acceptance'],'INCOMPLETE_EXIT_EVIDENCE')
        self.assertEqual(audit(log,exit_code=0)['acceptance'],'PASS')
        self.assertEqual(audit(log,exit_code=1)['acceptance'],'FAIL')

    def test_cannot_allowlist_p1(self):
        line="ScriptName 'npc_missing' exists in database, but no core script found!"
        with self.assertRaises(ValueError):audit(line,[{'line_sha256':hashlib.sha256(line.encode()).hexdigest(),'reason':'legacy'}])

    def test_allowlist_exactness(self):
        line='Table `character_template` is empty'
        # Native message includes DB prefix; an unrelated empty-table phrase must not be hidden.
        line='DB table `character_template` is empty.'
        rule={'line_sha256':hashlib.sha256(line.encode()).hexdigest(),'reason':'Optional fresh character templates'}
        log='(worldserver-daemon) ready...\nserver shutdown 1\nHalting process...\n'+line
        self.assertEqual(audit(log,[rule],0)['acceptance'],'PASS')
        self.assertEqual(audit(log.replace('character_template','different_table'),[rule],0)['acceptance'],'FAIL')

    def test_unknown_errors_fail_closed(self):
        self.assertEqual(audit('Unexpected subsystem: dependency missing')['severity_counts']['P1'],1)

    def test_root_cluster_keeps_counts(self):
        lines=["Table 'reference_loot_template' Entry 13003 does not exist but it is used by Reference 13003"]*4
        lines += ["Table 'reference_loot_template' Entry 13004 does not exist but it is used by Reference 13004"]
        finding=audit('\n'.join(lines))['findings'][0]
        self.assertEqual(finding['count'],5);self.assertEqual(finding['object_counts'],{'13003':4,'13004':1})
        self.assertEqual((finding['first_line'],finding['last_line']),(1,5))

    def test_source_offsets_and_disabled_loaders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'src/server/scripts/BrokenIsles/test.cpp';path.parent.mkdir(parents=True)
            path.write_text('''// void AddSC_fake() { }
class npc_valid : public CreatureScript { npc_valid() : CreatureScript("npc_valid") {} };
void AddSC_valid() { new npc_valid(); }
void AddSC_unused() {}
void AddBrokenIslesScripts() { /* AddSC_unused(); */ AddSC_valid(); }
''',encoding='utf8')
            report=build(root,"TrinityCore rev. abc123\nScript named 'npc_valid' does not have a script name assigned in database.")
            self.assertEqual(report['uncalled_AddSC_definitions'],['AddSC_unused'])
            occurrence=report['scripts'][0]['source_occurrences'][0]
            self.assertTrue(occurrence['static_loader_reachable']);self.assertFalse(occurrence['binary_registration_verified'])


def row(event,link=0,kind=0,entry=1,source=0):
    return dict(id=event,link=link,event_type=kind,entryorguid=entry,source_type=source)


class SmartGraphTest(unittest.TestCase):
    def categories(self,rows):return validate(rows)['category_counts']

    def test_valid_chain(self):self.assertEqual(self.categories([row(0,1),row(1,2,61),row(2,0,61)]),{})
    def test_missing_and_wrong_event_type(self):
        self.assertIn('MISSING_DESTINATION',self.categories([row(0,1)]))
        self.assertIn('DESTINATION_NOT_LINK_EVENT',self.categories([row(0,1),row(1)]))
    def test_duplicate_and_self(self):
        self.assertIn('DUPLICATE_EVENT_ID',self.categories([row(1),row(1)]))
        self.assertIn('SELF_LINK',self.categories([row(1,1,61)]))
    def test_cycle_orphan_unreachable(self):
        cats=self.categories([row(1,2,61),row(2,1,61),row(3,0,61)])
        self.assertEqual(cats['MULTI_NODE_CYCLE'],1);self.assertEqual(cats['UNREACHABLE_LINK_EVENT'],3)
        self.assertEqual(cats['ORPHAN_LINK_EVENT'],1)
    def test_no_cross_entry_or_source_link(self):
        cats=self.categories([row(0,1),row(1,0,61,entry=2),row(1,0,61,source=1)])
        self.assertEqual(cats['MISSING_DESTINATION'],1)
    def test_long_graph_iterative(self):
        rows=[row(i,i+1,61 if i else 0) for i in range(5000)]+[row(5000,0,61)]
        self.assertEqual(self.categories(rows),{})


def isolated_config():
    return '\n'.join([f'{key} = "127.0.0.1;3306;test;test;1kycore_audit_{db}"' for key,db in [('LoginDatabaseInfo','auth'),('WorldDatabaseInfo','world'),('CharacterDatabaseInfo','characters'),('HotfixDatabaseInfo','hotfixes'),('ShopDatabaseInfo','shop')]])+'\nBindIP = "127.0.0.1"\nConsole.Enable = 1\nRa.Enable = 0\nSOAP.Enabled = 0\nWorldREST.Enabled = 0\nWorldServerPort = 18085\nInstanceServerPort = 18086\n'


class ProbeTest(unittest.TestCase):
    def test_isolation_guards(self):
        config=isolated_config();self.assertEqual(len(check_config(config)),5)
        for bad in [config.replace('1kycore_audit_world','world'),config.replace('127.0.0.1','192.0.2.2'),config.replace('18085','8085'),config.replace('18086','8086'),config.replace('WorldREST.Enabled = 0','WorldREST.Enabled = 1'),config+'\nBindIP = "0.0.0.0"',config+'\n[include]\n']:
            with self.subTest(bad=bad),self.assertRaises(ValueError):check_config(bad)

    @unittest.skipUnless(sys.platform.startswith('linux'),'Linux-only probe')
    def test_real_pipe_handshake_and_failure(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);config=d/'audit.conf';config.write_text(isolated_config(),encoding='utf8')
            server=d/'fake-worldserver'
            for crash in (False,True):
                server.write_text('#!/usr/bin/env python3\nimport sys\nprint("(worldserver-daemon) ready...",flush=True)\nassert input()=="server shutdown 1"\nprint("Halting process...",flush=True)\n'+('print("Segmentation fault (core dumped)",flush=True)\nsys.exit(139)\n' if crash else ''),encoding='utf8');server.chmod(0o700)
                output=d/str(crash)
                result=subprocess.run([sys.executable,str(ROOT/'contrib/tools/worldserver_bootstrap_probe.py'),'--server',str(server),'--config',str(config),'--output-dir',str(output),'--startup-timeout','5','--shutdown-timeout','5'],capture_output=True,text=True,timeout=15)
                self.assertEqual(result.returncode,int(crash),result.stderr)
                report=json.loads((output/'audit.json').read_text('utf8'));self.assertEqual(report['acceptance'],'FAIL' if crash else 'PASS')
                self.assertFalse(report['empty_database_bootstrap_verified'])


class BaselineTest(unittest.TestCase):
    def test_measured_baseline_and_unique_root_counts(self):
        report=json.loads((ROOT/'docs/audit-data/worldserver-startup-audit.json').read_text('utf8'))
        expected={'PROCESS_CRASH':1,'LOCALE_ORPHAN':5724,'SCRIPT_CPP_NO_DB':1574,'SCRIPT_DB_NO_CPP':222,'REFERENCE_LOOT_MISSING':709,'GO_LOOT_MISSING':538,'TRAINER_FLAG':651,'SMARTAI_MISSING_SPELL':344,'SPAWN_UNSUPPORTED_DIFFICULTY':283,'GO_ZERO_DISPLAY':222,'SPELL_HOOK_MISMATCH':198,'SMARTAI_LINK_DESTINATION':180,'SMARTAI_LINK_SOURCE':89,'SMARTAI_SELF_LINK':12}
        for key,value in expected.items():self.assertEqual(report['category_counts'][key],value,key)
        self.assertEqual(report['acceptance'],'FAIL');self.assertFalse(report['normal_exit_verified'])
        groups=[x for x in report['findings'] if x['category']=='TRAINER_FLAG']
        self.assertEqual(sum(len(x['unique_objects']) for x in groups),7)
        for finding in report['findings']:
            self.assertEqual(audit(finding['example_lines'][0])['findings'][0]['category'],finding['category'])
        matrix=json.loads((ROOT/'docs/audit-data/script-binding-matrix.json').read_text('utf8'))
        self.assertEqual(matrix['counts'],{'SCRIPT_CPP_NO_DB':1573,'SCRIPT_DB_NO_CPP':222})


if __name__=='__main__':unittest.main()
