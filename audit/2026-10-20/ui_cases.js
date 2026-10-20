async (page) => {
  const base = 'http://127.0.0.1:18891';
  if (new URL(page.url()).origin !== base) throw Error('Isolated audit fixture only');
  const results = [];
  // A real HTTP state refresh must update read-only current values while keeping target drafts.
  await page.request.post(base + '/api/goals/update', {
    headers: {'X-GC':'1'}, data: {id:'audit-agent',patch:{current:{weapon:56}}}
  });
  await page.evaluate(() => refreshState(true));
  await page.getByRole('button',{name:'目标设置',exact:true}).click();
  await page.locator('#modal input[name="weapon"]').fill('59');
  await page.request.post(base + '/api/goals/update', {
    headers: {'X-GC':'1'}, data: {id:'audit-agent',patch:{current:{weapon:60}}}
  });
  await page.evaluate(() => refreshState(true));
  results.push(await page.evaluate(() => ({case:'modal-current-after-refresh',
    model:findGoal('audit-agent').current.weapon,
    card:document.querySelector('.goal .target-box:nth-child(2) tbody tr td').textContent,
    modal:document.querySelector('#modal .target-box:nth-child(2) tbody tr td').textContent,
    draft:document.querySelector('#modal input[name="weapon"]').value})));
  await page.locator('#modal [data-action="modal-close"]').click();
  results.push(await page.evaluate(() => ({case:'blocked-equipment-status',
    block:STATE.plans.zzz.equipment.why,
    shown:document.querySelector('.gear-state').textContent})));
  for (const width of [1440,390]) {
    await page.setViewportSize({width,height:1000});
    let release;
    const gate=new Promise(resolve=>release=resolve);
    let calls=0;
    await page.route(base+'/api/goals/sync',async route=>{
      calls++;
      await gate;
      await route.continue();
    });
    const btn=page.getByRole('button',{name:'同步',exact:true});
    await btn.click();
    await page.waitForTimeout(70);
    const geometry=await page.locator('[data-action="sync-goal"]').evaluate(b=>{
      const r=b.getBoundingClientRect();
      return {text:b.innerText,busy:b.getAttribute('aria-busy'),disabled:b.disabled,width:r.width,
        children:[...b.querySelectorAll('.txt,.spin,.ic')].map(n=>{
          const x=n.getBoundingClientRect();
          return {class:n.getAttribute('class'),width:x.width,height:x.height,
                  inside:!x.width || (x.left>=r.left&&x.right<=r.right&&x.top>=r.top&&x.bottom<=r.bottom)};
        })};
    });
    // Repeated activation while busy must not generate a second request.
    await page.locator('[data-action="sync-goal"]').evaluate(b=>b.click());
    const responsePromise=page.waitForResponse(r=>r.url()===base+'/api/goals/sync');
    release();
    const response=await responsePromise;
    const body=await response.json();
    await page.waitForFunction(()=>!document.querySelector('[data-action="sync-goal"]').disabled);
    results.push({case:'sync-result-and-busy',width,calls,geometry,status:response.status(),
      observeError:body.observe_error,calcError:body.calc_error,toasts:await page.locator('#toasts').innerText()});
    await page.unroute(base+'/api/goals/sync');
  }
  await page.setViewportSize({width:1440,height:1000});
  return results;
}
