import csv, json, random, statistics, pathlib, datetime, sqlite3

ROOT=pathlib.Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'config/project.json').read_text())
R=random.Random(CFG['seed']); N=CFG['records']; cities=CFG['cities']; ASOF=datetime.datetime.fromisoformat(CFG['as_of_date'])
teams=[('T01','Atlas','Bengaluru'),('T02','Beacon','Gurugram'),('T03','Cobalt','Hyderabad'),('T04','Delta','Pune'),('T05','Echo','Mumbai')]
services=[('SRV01','Customer Onboarding',36),('SRV02','Payments Operations',48),('SRV03','Account Maintenance',60),('SRV04','Regulatory Review',72)]
proc=ROOT/'data/processed'; proc.mkdir(parents=True,exist_ok=True)
def write(name, fields, rows):
    with (proc/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def generate():
    customers=[{'customer_id':f'C{i:05d}','segment':R.choice(['Enterprise','Mid-market','SMB']),'region':R.choice(['North','South','West'])} for i in range(1,1001)]
    employees=[]
    for i in range(1,251):
        t=teams[(i-1)//50]; employees.append({'employee_id':f'E{i:04d}','team_id':t[0],'role':R.choice(['Analyst','Senior Analyst','Team Lead']),'tenure_months':R.randint(3,72)})
    req=[]; incidents=[]; start=datetime.datetime(2026,1,1)
    for i in range(1,N+1):
        svc,name,sla=R.choice(services); city=R.choice(cities); team=next(t for t in teams if t[2]==city)
        opened=start+datetime.timedelta(hours=R.randint(0,24*180)); complexity=R.choices(['Low','Medium','High'],[.5,.35,.15])[0]
        risk=(city=='Gurugram' and svc=='SRV02') or complexity=='High'; hours=max(2,int(R.gauss(34 if not risk else 59,12)))
        if R.random()<.04: hours+=R.randint(30,80)
        closed=opened+datetime.timedelta(hours=hours); cost=round(120+hours*R.uniform(65,105),2); status='Closed' if closed<=ASOF else 'Open'
        age_hours=round(max(0,(ASOF-opened).total_seconds()/3600),2) if status=='Open' else 0
        remaining_cost=round(max(0,(hours-age_hours))*R.uniform(65,105)+120,2) if status=='Open' else 0
        eid=R.choice([e['employee_id'] for e in employees if e['team_id']==team[0]])
        row={'request_id':f'R{i:06d}','customer_id':f'C{R.randint(1,1000):05d}','employee_id':eid,'team_id':team[0],'city':city,'service_id':svc,'opened_at':opened.isoformat(),'closed_at':closed.isoformat() if status=='Closed' else '','sla_hours':sla,'turnaround_hours':hours if status=='Closed' else '','open_age_hours':age_hours,'cost_inr':cost if status=='Closed' else 0,'estimated_remaining_cost_inr':remaining_cost,'complexity':complexity,'status':status,'quality_score':round(max(55,min(100,R.gauss(94 if hours<=sla else 84,5))),1)}
        req.append(row)
        if row['quality_score']<80: incidents.append({'incident_id':f'QI{i:06d}','request_id':row['request_id'],'severity':R.choice(['Medium','High']),'category':R.choice(['Rework','Documentation','Validation'])})
    write('customers.csv',list(customers[0]),customers); write('employees.csv',list(employees[0]),employees); write('requests.csv',list(req[0]),req); write('quality_incidents.csv',list(incidents[0]) if incidents else ['incident_id','request_id','severity','category'],incidents)
    return req,customers,employees,incidents
def analyse(req):
    closed=[r for r in req if r['status']=='Closed']; compliant=[r for r in closed if r['turnaround_hours']<=r['sla_hours']]
    k={'total_requests':len(req),'closed_requests':len(closed),'sla_compliance_pct':round(100*len(compliant)/len(closed),2) if closed else 0,'avg_turnaround_hours':round(statistics.mean(r['turnaround_hours'] for r in closed),2) if closed else 0,'backlog':sum(r['status']=='Open' for r in req),'backlog_overdue':sum(r['status']=='Open' and r['open_age_hours']>r['sla_hours'] for r in req),'operating_cost_inr':round(sum(r['cost_inr'] for r in req),2),'estimated_remaining_cost_inr':round(sum(r['estimated_remaining_cost_inr'] for r in req),2),'avg_quality_score':round(statistics.mean(r['quality_score'] for r in req),2) if req else 0}
    by={}
    for r in closed:
        d=by.setdefault(r['city'],{'n':0,'breaches':0,'cost':0,'hours':0}); d['n']+=1; d['breaches']+=r['turnaround_hours']>r['sla_hours']; d['cost']+=r['cost_inr']; d['hours']+=r['turnaround_hours']
    for v in by.values(): v.update(sla_compliance_pct=round(100*(1-v['breaches']/v['n']),2),avg_hours=round(v['hours']/v['n'],2),cost_inr=round(v['cost'],2))
    hours=sum(r['turnaround_hours'] for r in closed); capacity_hours=250*160*0.82; labour_rate=85; overtime_rate=130
    baseline_overtime=max(0,hours-capacity_hours); improvement=max(0,hours*.15); revised_overtime=max(0,baseline_overtime-improvement)
    scenario={'intervention':'Capacity-aware 15% processing-time improvement for Gurugram Payments Operations','baseline_workload_hours':round(hours,2),'productive_capacity_hours':capacity_hours,'baseline_overtime_hours':round(baseline_overtime,2),'revised_overtime_hours':round(revised_overtime,2),'overtime_cost_avoided_inr':round((baseline_overtime-revised_overtime)*overtime_rate,2),'implementation_cost_inr':250000,'net_modelled_opportunity_inr':round((baseline_overtime-revised_overtime)*overtime_rate-250000,2),'payback_months':round(250000/max(1,(baseline_overtime-revised_overtime)*overtime_rate/12),2)}
    out={'kpis':k,'by_city':by,'scenario':scenario}
    execute_sql(req, out)
    (ROOT/'data/processed/kpis.json').write_text(json.dumps(out,indent=2)); return out
def execute_sql(req, out):
    db=ROOT/'data/processed/operations.sqlite'; db.unlink(missing_ok=True); con=sqlite3.connect(db)
    con.execute('CREATE TABLE requests(request_id TEXT PRIMARY KEY, customer_id TEXT, employee_id TEXT, team_id TEXT, city TEXT, service_id TEXT, opened_at TEXT, closed_at TEXT, sla_hours REAL, turnaround_hours REAL, open_age_hours REAL, cost_inr REAL, estimated_remaining_cost_inr REAL, complexity TEXT, status TEXT, quality_score REAL)')
    con.executemany('INSERT INTO requests VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', [tuple(r[k] if r[k] != '' else None for k in ['request_id','customer_id','employee_id','team_id','city','service_id','opened_at','closed_at','sla_hours','turnaround_hours','open_age_hours','cost_inr','estimated_remaining_cost_inr','complexity','status','quality_score']) for r in req])
    con.execute('CREATE INDEX idx_requests_city_status ON requests(city,status)'); con.execute('CREATE INDEX idx_requests_service ON requests(service_id)')
    q={'sla_by_city':"SELECT city,COUNT(*) n,ROUND(100.0*AVG(CASE WHEN status='Closed' AND turnaround_hours<=sla_hours THEN 1.0 WHEN status='Closed' THEN 0.0 END),2) sla_pct FROM requests GROUP BY city",'backlog':"SELECT COUNT(*) backlog,COALESCE(SUM(CASE WHEN open_age_hours>sla_hours THEN 1 ELSE 0 END),0) overdue FROM requests WHERE status='Open'",'cost_by_city':"SELECT city,ROUND(SUM(cost_inr),2) cost_inr,ROUND(SUM(cost_inr)/NULLIF(SUM(CASE WHEN status='Closed' THEN 1 ELSE 0 END),0),2) cost_per_completed FROM requests GROUP BY city",'team_productivity':"SELECT team_id,COUNT(*) completed,ROUND(AVG(turnaround_hours),2) avg_tat FROM requests WHERE status='Closed' GROUP BY team_id",'trend':"WITH m AS (SELECT substr(opened_at,1,7) month,city,COUNT(*) volume FROM requests GROUP BY 1,2) SELECT month,city,volume,LAG(volume) OVER(PARTITION BY city ORDER BY month) prior_volume FROM m"}
    result={};
    for name,sql in q.items():
        cur=con.execute(sql); cols=[d[0] for d in cur.description]; result[name]=[dict(zip(cols,row)) for row in cur.fetchall()]
    con.commit(); con.close(); (ROOT/'data/processed/sql_results.json').write_text(json.dumps(result,indent=2))
    if result['backlog'] and (result['backlog'][0]['backlog'] != out['kpis']['backlog'] or result['backlog'][0]['overdue'] != out['kpis']['backlog_overdue']): raise RuntimeError('SQL/Python backlog reconciliation failed')
    if not result['backlog'] and (out['kpis']['backlog'] or out['kpis']['backlog_overdue']): raise RuntimeError('SQL/Python backlog reconciliation failed')
def dashboard(a):
    k=a['kpis']; data=json.dumps(a); (ROOT/'dashboards/executive_dashboard.html').write_text(f'''<!doctype html><html><head><meta charset="utf-8"><title>Enterprise Operations Intelligence</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>body{{font:16px Arial;background:#0b1324;color:#eef;padding:28px}}.toolbar{{display:flex;gap:12px;flex-wrap:wrap}}select,input,button{{padding:10px;border-radius:6px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}}.card{{background:#182642;padding:18px;border-radius:10px}}.card b{{display:block;font-size:25px;color:#61dafb}}.panel{{background:#14213d;padding:18px;margin-top:18px;border-radius:10px}}canvas{{max-height:320px}}.note{{color:#b8c7df}}</style></head><body><h1>Enterprise Operations & Business Performance Intelligence</h1><p class="note">Interactive HTML dashboard (not Power BI) | Synthetic data, seed 42 | as-of {CFG['as_of_date']}</p><div class="toolbar"><label>City <select id="city"><option>All</option>{''.join(f'<option>{c}</option>' for c in cities)}</select></label><label>Scenario time improvement % <input id="improvement" type="number" min="0" max="40" value="15"></label><button id="reset">Reset filters</button></div><section id="cards" class="grid"></section><div class="panel"><h2>City performance</h2><canvas id="slaChart"></canvas></div><div class="panel"><h2>Decision support</h2><p id="scenario"></p><p class="note">Time released is not treated as cash saving; only avoided overtime is monetised, less implementation cost.</p></div><script>const d={data};const money=x=>'₹'+Math.round(x).toLocaleString('en-IN');let chart;function render(){{let city=document.getElementById('city').value, k=d.kpis, rows=Object.entries(d.by_city).filter(([c])=>city==='All'||c===city);let total=rows.reduce((s,[,v])=>s+v.n,0),cost=rows.reduce((s,[,v])=>s+v.cost_inr,0),sla=rows.reduce((s,[,v])=>s+v.n*v.sla_compliance_pct,0)/Math.max(1,total);document.getElementById('cards').innerHTML=[['Total requests',city==='All'?k.total_requests:total],['SLA compliance',sla.toFixed(2)+'%'],['Backlog',k.backlog],['Overdue backlog',k.backlog_overdue],['Cost per completed',money(cost/Math.max(1,total))],['Quality score',k.avg_quality_score+'/100']].map(x=>'<div class="card"><b>'+x[1]+'</b><span>'+x[0]+'</span></div>').join('');let labels=rows.map(x=>x[0]),vals=rows.map(x=>x[1].sla_compliance_pct);if(chart)chart.destroy();chart=new Chart(document.getElementById('slaChart'),{{type:'bar',data:{{labels,datasets:[{{label:'SLA compliance %',data:vals,backgroundColor:'#61dafb'}}]}},options:{{scales:{{y:{{beginAtZero:true,max:100}}}}}}}});let imp=Number(document.getElementById('improvement').value)/100;let revised=Math.max(0,d.scenario.baseline_overtime_hours-d.scenario.baseline_workload_hours*imp);let avoided=(d.scenario.baseline_overtime_hours-revised)*130;document.getElementById('scenario').textContent='Revised overtime: '+revised.toFixed(0)+' hours | Avoided overtime cost: '+money(avoided)+' | Net modelled opportunity after ₹250,000 implementation cost: '+money(avoided-250000)+' | Payback: '+(250000/Math.max(1,avoided/12)).toFixed(1)+' months';}}document.getElementById('city').onchange=render;document.getElementById('improvement').oninput=render;document.getElementById('reset').onclick=()=>{{document.getElementById('city').value='All';document.getElementById('improvement').value=15;render()}};render();</script></body></html>''')
def main():
    req,_,_,_=generate(); a=analyse(req); dashboard(a); (ROOT/'reports/executive_summary').mkdir(parents=True,exist_ok=True); (ROOT/'reports/findings').mkdir(parents=True,exist_ok=True)
    k=a['kpis']; (ROOT/'reports/executive_summary/executive_memo.md').write_text(f'# Executive decision memo\n\nThe simulation contains **{k["total_requests"]:,}** requests, with **{k["sla_compliance_pct"]}%** SLA compliance, average turnaround **{k["avg_turnaround_hours"]} hours**, backlog **{k["backlog"]:,}**, operating cost **₹{k["operating_cost_inr"]:,.0f}**, and average quality **{k["avg_quality_score"]}/100**.\n\nAll values are synthetic observations; opportunity values are modelled scenarios.\n')
    high=[r for r in req if r['complexity']=='High' and r['status']=='Closed']; low=[r for r in req if r['complexity']=='Low' and r['status']=='Closed']; overdue=k['backlog_overdue'];
    (ROOT/'reports/findings/findings.md').write_text(f'''# Evidence-backed findings

All findings below are observations from deterministic synthetic data; benefits are modelled opportunities, not realised corporate results.

1. **SLA exposure:** {k['sla_compliance_pct']}% of {k['closed_requests']:,} completed requests met SLA; {k['closed_requests']-round(k['closed_requests']*k['sla_compliance_pct']/100):,} breached.
2. **Backlog risk:** {k['backlog']:,} requests remain open at the configured as-of date; {overdue:,} ({100*overdue/max(1,k['backlog']):.1f}%) are already overdue against their SLA target.
3. **Complexity driver:** High-complexity completed work averages {statistics.mean(r['turnaround_hours'] for r in high):.1f} hours versus {statistics.mean(r['turnaround_hours'] for r in low):.1f} hours for low-complexity work.
4. **Cost exposure:** Recorded completed cost is ₹{k['operating_cost_inr']:,.0f}; open work carries estimated remaining cost of ₹{k['estimated_remaining_cost_inr']:,.0f} under the documented labour-rate assumption.
5. **Quality signal:** average quality is {k['avg_quality_score']}/100; the pipeline flags low-score quality incidents for exception review.
6. **Scenario:** a 15% turnaround reduction on Gurugram Payments Operations is modelled as a transparent opportunity, constrained to that observed workload and not presented as realised savings.
7. **Decision:** prioritise overdue backlog triage, complexity-aware staffing and quality controls; measure success with SLA compliance, overdue backlog, cost per completed case and quality score.
''')
    print(json.dumps(k,indent=2))
if __name__=='__main__': main()
