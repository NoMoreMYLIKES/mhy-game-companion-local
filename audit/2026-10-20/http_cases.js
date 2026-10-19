async (page) => {
  const base='http://127.0.0.1:18891';
  if(new URL(page.url()).origin!==base) throw Error('Isolated audit fixture only');
  const post=(p,data)=>page.request.post(base+p,{headers:{'X-GC':'1'},data});
  await post('/__audit/gate',{action:'arm'});
  const pending=post('/api/goals/sync',{id:'audit-agent',observe:true});
  let entered=false;
  for(let i=0;i<30;i++) {
    entered=(await(await post('/__audit/gate',{action:'status'})).json()).entered;
    if(entered) break;
    await page.waitForTimeout(20);
  }
  if(!entered) throw Error('Synthetic observation gate was not entered');
  await post('/api/goals/update',{id:'audit-agent',patch:{enabled:false}});
  await page.evaluate(()=>refreshState(true));
  const before=await page.evaluate(()=>({enabled:findGoal('audit-agent').enabled,cards:document.querySelectorAll('.goal').length}));
  await post('/__audit/gate',{action:'release'});
  await pending;
  await page.evaluate(()=>refreshState(true));
  const after=await page.evaluate(()=>({enabled:findGoal('audit-agent').enabled,cards:document.querySelectorAll('.goal').length}));
  await post('/api/settings',{settings:{schedule:{enabled:false}},secrets:{password:''}});
  const failed=await post('/api/settings',{settings:{schedule:{enabled:true,autostart:true}}});
  const s=await(await page.request.get(base+'/api/state')).json();
  const bad=await post('/api/settings',{settings:{schedule:{times:['invalid']}},secrets:{password:'synthetic-only'}});
  const ss=await(await page.request.get(base+'/api/state')).json();
  return {cancelWhileSync:{before,after},
    failedSettings:{http:failed.status(),enabled:s.settings.schedule.enabled,autostart:s.settings.schedule.autostart},
    invalidSettings:{http:bad.status(),passwordStored:ss.settings.secrets_set.password}};
}
