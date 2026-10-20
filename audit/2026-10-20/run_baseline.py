import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

audit = Path(os.environ['GCL_HOME']).resolve().parent
source = Path(sys.argv[1]).resolve()
assert (Path(os.environ['GCL_HOME'])/'AUDIT_RUNTIME').read_text(encoding='utf-8').strip() == 'synthetic'
bootstrap = '''
import os, pathlib, sys, unittest
sys.path.insert(0, sys.argv[1])
from server import core
expected=pathlib.Path(os.environ['GCL_HOME']).resolve()
assert core.DATA.resolve() == expected
assert expected != core.APP / 'data'
with core.db() as con:
 assert pathlib.Path(con.execute('pragma database_list').fetchone()[2]).resolve() == expected / 'app.db'
suite=unittest.defaultTestLoader.discover(str(pathlib.Path(sys.argv[1])/'tests'), pattern=sys.argv[2])
result=unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
'''
results=[]
for file in sorted((source/'tests').glob('test_*.py')):
    home = audit / ('baseline-' + file.stem + '-' + uuid.uuid4().hex[:8])
    home.mkdir()
    env=dict(os.environ, GCL_HOME=str(home), PYTHONIOENCODING='utf-8', PYTHONPATH=str(source))
    with (audit/(file.stem+'.log')).open('w',encoding='utf-8') as out:
        result=subprocess.run([sys.executable,'-c',bootstrap,str(source),file.name],cwd=source,
                              env=env,stdout=out,stderr=subprocess.STDOUT,timeout=400)
    results.append({'module':file.name,'exit':result.returncode,'runtime':str(home)})
    (audit/'baseline-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results[-1]),flush=True)
sys.exit(any(r['exit'] for r in results))
