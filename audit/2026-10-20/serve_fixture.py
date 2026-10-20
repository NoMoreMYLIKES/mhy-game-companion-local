import copy
import json
import os
from pathlib import Path
import sys
import threading
import time

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'tests'))
from server import core, goals, mihoyo, scheduler, web
from test_gear import full_gear

home = Path(os.environ['GCL_HOME']).resolve()
assert core.DATA.resolve() == home and home != root/'data'
assert (home/'AUDIT_RUNTIME').read_text(encoding='utf-8').strip() == 'synthetic'
with core.db() as con:
    assert Path(con.execute('pragma database_list').fetchone()[2]).resolve() == home/'app.db'
core.save_settings({'server': {'port': 18891}, 'ui': {'lang': 'zh'},
                    'paths': {'bettergi': str(home/'missing-bgi'), 'onedragon': str(home/'missing-od')},
                    'schedule': {'enabled': False}, 'notify': {'channels': {'toast': {'enabled': False}}}})
goals.queue_sync = lambda *a, **k: None
mihoyo.roster = lambda *a: [{'id':'2','name':'Synthetic B','owned':True}]
g = {'id': 'audit-agent', 'character_id': '1', 'name':'Synthetic Agent', 'game':'zzz','enabled':True,'position':1,
     'current':{'level':60,'weapon':56,'attack':10,'special':12,'dodge':10,'chain':11,'assist':10,'core':6},
     'target':{'level':60,'weapon':60,'attack':12,'special':12,'dodge':10,'chain':12,'assist':10,'core':6},
     'category_order':['talents','level','weapon'], 'paused':[], 'materials':[], 'allowance':{},
     'calc_at':core.stamp(),'sync_at':core.stamp(),'observe_at':core.stamp(),'gear':full_gear(),
     'gear_target':{'farm':True,'score':100,'stage':'Synthetic Stage'}}
core.save_goal(g)
gate = threading.Event()
entered = threading.Event()
mode = {'gated': False}
def observed(goal, force=False):
    if not mode['gated']:
        raise ValueError('Synthetic observation failure')
    entered.set()
    if not gate.wait(30):
        raise ValueError('Synthetic gate timeout')
    return {'current': {'level': 60, 'weapon': 60}}
mihoyo.observe = observed
def calculate(goal):
    if not mode['gated']:
        raise ValueError('Synthetic calculation failure')
    return []
mihoyo.calculate = calculate
def autostart(enabled):
    raise ValueError('Synthetic task registration denied; no system task was touched')
scheduler.set_autostart = autostart
class AuditHandler(web.Handler):
    def route(self, path, body):
        if path == '/__audit/gate':
            if body.get('action') == 'arm':
                mode['gated'] = True
                gate.clear()
                entered.clear()
            elif body.get('action') == 'release':
                gate.set()
            return {'entered': entered.is_set()}
        return super().route(path, body)
web.IDENTITY.update(instance='isolated-audit', created=time.time())
httpd=web.Server(core.listen_address(), AuditHandler)
web.run_forever(httpd)
web.READY.set()
(home.parent/'ui-fixture.json').write_text(json.dumps({'pid':os.getpid(),'port':18891,'home':str(home)}),encoding='utf-8')
try:
    while not web.SHUTDOWN.wait(.5):
        pass
finally:
    httpd.shutdown()
