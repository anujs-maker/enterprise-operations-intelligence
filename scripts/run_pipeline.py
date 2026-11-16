import csv, json, random, statistics, pathlib, datetime

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
    k={'total_requests':len(req),'closed_requests':len(closed),'sla_compliance_pct':round(100*len(compliant)/len(closed),2),'avg_turnaround_hours':round(statistics.mean(r['turnaround_hours'] for r in closed),2),'backlog':sum(r['status']=='Open' for r in req),'backlog_overdue':sum(r['status']=='Open' and r['open_age_hours']>r['sla_hours'] for r in req),'operating_cost_inr':round(sum(r['cost_inr'] for r in req),2),'estimated_remaining_cost_inr':round(sum(r['estimated_remaining_cost_inr'] for r in req),2),'avg_quality_score':round(statistics.mean(r['quality_score'] for r in req),2)}
    by={}
    for r in closed:
        d=by.setdefault(r['city'],{'n':0,'breaches':0,'cost':0,'hours':0}); d['n']+=1; d['breaches']+=r['turnaround_hours']>r['sla_hours']; d['cost']+=r['cost_inr']; d['hours']+=r['turnaround_hours']
    for v in by.values(): v.update(sla_compliance_pct=round(100*(1-v['breaches']/v['n']),2),avg_hours=round(v['hours']/v['n'],2),cost_inr=round(v['cost'],2))
    out={'kpis':k,'by_city':by,'scenario':{'intervention':'Reduce Gurugram Payments Operations turnaround by 15%','modelled_cost_avoidance_inr':round(sum(r['cost_inr']*.15 for r in closed if r['city']=='Gurugram' and r['service_id']=='SRV02'),2)}}
    (ROOT/'data/processed/kpis.json').write_text(json.dumps(out,indent=2)); return out
def dashboard(a):
    k=a['kpis']; cards=''.join(f'<div class="card"><b>{v}</b><span>{key.replace("_"," ").title()}</span></div>' for key,v in k.items()); rows=''.join(f'<tr><td>{c}</td><td>{v["n"]}</td><td>{v["sla_compliance_pct"]}%</td><td>₹{v["cost_inr"]:,.0f}</td></tr>' for c,v in a['by_city'].items())
    (ROOT/'dashboards/executive_dashboard.html').write_text(f'''<!doctype html><html><head><meta charset="utf-8"><title>Enterprise Operations Intelligence</title><style>body{{font:16px Arial;background:#0b1324;color:#eef;padding:28px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.card{{background:#182642;padding:18px;border-radius:10px}}.card b{{display:block;font-size:25px;color:#61dafb}}table{{width:100%;margin-top:25px;background:#182642;border-collapse:collapse}}td,th{{padding:12px;border-bottom:1px solid #344}}.note{{color:#b8c7df}}</style></head><body><h1>Enterprise Operations & Business Performance Intelligence</h1><p class="note">Synthetic data, seed 42 | HTML dashboard (not PBIX)</p><section class="grid">{cards}</section><h2>City performance</h2><table><tr><th>City</th><th>Closed volume</th><th>SLA compliance</th><th>Cost</th></tr>{rows}</table><h2>Decision support</h2><p>Modelled opportunity: ₹{a['scenario']['modelled_cost_avoidance_inr']:,.0f} cost avoidance under the stated intervention. This is a scenario, not realised savings.</p></body></html>''')
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
