import urllib.request, json, time, sys

base = 'http://localhost:8000'

print("=" * 60)
print("1. OpenAPI routes verification")
print("=" * 60)
r = urllib.request.urlopen(f'{base}/openapi.json', timeout=5)
doc = json.loads(r.read())
paths = sorted(doc.get('paths', {}).keys())
print(f'Total API routes: {len(paths)}')
for p in paths:
    methods = ','.join(doc['paths'][p].keys()).upper()
    tag = doc['paths'][p].get(list(doc['paths'][p].keys())[0], {}).get('tags', [''])[0]
    print(f'  {methods:12s} {p:65s} {tag}')

print()
print("=" * 60)
print("2. Commercial onboarding simulation")
print("=" * 60)
corp_tag = str(int(time.time()))[-4:]
data = json.dumps({
    'email': f'demo{corp_tag}@example.cn',
    'password': 'Demo@123456',
    'full_name': '王美业',
    'enterprise_name': f'肌肤美学（{corp_tag}）皮肤管理中心',
    'industry': 'beauty_local',
    'city': '上海市',
    'district': '静安区',
    'phone': '13800001234'
}).encode()
req = urllib.request.Request(f'{base}/api/v1/auth/register', data=data,
                             headers={'Content-Type': 'application/json'})
r = urllib.request.urlopen(req, timeout=10)
resp = json.loads(r.read())
ok = resp.get('code') == 0
print(f'REGISTER tenant -> OK: {ok} status={r.status}')
if not ok:
    print(f'  FAIL: {resp}')
    sys.exit(1)
token = resp['data']['access_token']
h = {'Authorization': f'Bearer {token}'}

def GET(path):
    req = urllib.request.Request(f'{base}{path}', headers=h)
    return json.loads(urllib.request.urlopen(req, timeout=10).read())

me = GET('/api/v1/auth/me')['data']
print(f'ME: role={me["role"]} enterprise={me.get("enterprise_id")}')

engs = GET('/api/v1/llm/engines')['data']
print(f'LLM engines: {len(engs)} -> {[e["name"] for e in engs]}')

kb = GET('/api/v1/user/kb/summary')['data']
print(f'KB summary: facts={kb["facts"]} signals={kb["signals"]} verified={kb["verified_facts"]}')

sc = GET('/api/v1/user/content/scenarios?page_size=10')['data']
print(f'Scenarios: total={sc["total"]} items={len(sc["items"])}')

dr = GET('/api/v1/user/content/drafts?page_size=10')['data']
print(f'Drafts: total={dr["total"]}')

pub = GET('/api/v1/user/publish?page_size=10')['data']
print(f'Publish tasks: total={pub["total"]}')

mon = GET('/api/v1/user/monitor/core?page_size=10')['data']
print(f'Monitor core: total={mon["total"]}')

trend = GET('/api/v1/user/monitor/trend?pool=core&days=7')['data']
print(f'Trend 7d: points={len(trend)}')

dash = GET('/api/v1/user/outcomes/dashboard?period=week')['data']
print(f'Dashboard: period={dash["period"]} alerts={len(dash["alerts"])} channels={len(dash["by_channel"])} engines={len(dash["by_engine"])}')
for a in dash['alerts'][:3]:
    print(f'  [{a["level"]:8s}] {a["msg"][:60]}')
kpi = dash['kpi']
print(f'  KPI: scenarios={kpi["total_scenarios"]} published={kpi["total_drafts_published"]} mention={kpi["avg_mention_rate"]} trust={kpi["avg_trust_score"]} kb={kpi["kb_facts_verified"]}')

ai_kpi = GET('/api/v1/user/outcomes/ai-kpi')['data']
print(f'AI KPI: keys={sorted(list(ai_kpi.keys()))}')

traffic = GET('/api/v1/user/outcomes/traffic')['data']
print(f'Traffic: channels={len(traffic["by_channel"])} engines={len(traffic["by_engine"])}')

mem = GET('/api/v1/user/enterprise/members')
items = mem.get('items', mem.get('data', []))
print(f'Members: count={len(items)} (code={mem.get("code")})')

sp = GET('/api/v1/user/strategy-pack/draft')
sp_d = sp.get('data', sp)
print(f'StrategyPack draft: id={sp_d.get("id")} status={sp_d.get("status")} version={sp_d.get("version")}')

d = GET('/api/v1/agent?page_size=5')['data']
print(f'Agent tasks: total={d["total"]}')

print()
print("=" * 60)
print("ALL COMMERCIAL PREVIEW CHECKS PASSED ✓")
print("=" * 60)
