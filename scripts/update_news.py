import json, urllib.request, xml.etree.ElementTree as ET, email.utils, datetime, pathlib, html, re
ROOT=pathlib.Path(__file__).resolve().parents[1]
FEEDS=[
 ('uae','UAE headlines','https://news.google.com/rss/search?q=site%3Akhaleejtimes.com+OR+site%3Agulfnews.com+when%3A2d&hl=en-AE&gl=AE&ceid=AE:en'),
 ('adx','ADX & APEX','https://news.google.com/rss/search?q=%22APEX+Investments%22+OR+%22Abu+Dhabi+Securities+Exchange%22+OR+%22IHC%22+ADX+when%3A7d&hl=en-AE&gl=AE&ceid=AE:en'),
 ('world','World','https://feeds.bbci.co.uk/news/world/rss.xml'),
 ('business','Business','https://feeds.bbci.co.uk/news/business/rss.xml'),
 ('tech','Technology','https://feeds.bbci.co.uk/news/technology/rss.xml'),
]
def clean(s): return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]*>',' ',s or ''))).strip()
def fetch(cat,label,url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; PersonalNewsDashboard/1.0)'})
 with urllib.request.urlopen(req,timeout=20) as r: raw=r.read(1500000)
 root=ET.fromstring(raw)
 results=[]
 for item in root.findall('.//channel/item')[:16]:
  title=clean(item.findtext('title')); link=(item.findtext('link') or '').strip()
  source=clean(item.findtext('source')) or ('BBC News' if 'bbc' in url else 'Google News')
  date=(item.findtext('pubDate') or '').strip()
  if not title or not link.startswith('https://'):continue
  try: published=email.utils.parsedate_to_datetime(date).astimezone(datetime.timezone.utc).isoformat()
  except Exception: published=None
  results.append(dict(cat=cat,source=source,title=title,url=link,published=published))
 return results
old=[]
try: old=json.loads((ROOT/'news.json').read_text(encoding='utf8')).get('stories',[])
except Exception:pass
stories=[]; errors=[]
for cat,label,url in FEEDS:
 try:
  rows=fetch(cat,label,url)
  if not rows:raise ValueError('empty feed')
  stories.extend(rows)
 except Exception as e:
  errors.append(f'{label}: {type(e).__name__}: {e}')
  stories.extend(x for x in old if x.get('cat')==cat)
seen=set(); unique=[]
for s in stories:
 key=s['url']
 if key not in seen:seen.add(key);unique.append(s)
if not unique:raise SystemExit('No headlines retrieved; keeping existing news.json unchanged. '+str(errors))
payload={'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stories':unique[:100],'notes':'News headlines are aggregated from publisher feeds and Google News search results; links open original or aggregator pages. Not real-time stock data.'}
(ROOT/'news.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(f'Wrote {len(unique)} headlines; feed issues: {errors}')
