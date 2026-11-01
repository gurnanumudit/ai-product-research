from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen
import json,re,hashlib,argparse
class Audit(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.skip=0;self.stack=[];self.text=[];self.geom=[];self.cells=[];self.cell=None;self.inbody=False;self.encodings=[]
 def handle_starttag(self,t,attrs):
  a=dict(attrs);self.stack.append((t,self.skip,self.inbody))
  if 'data-article-body' in a:self.inbody=True
  if t in ['script','style','title','desc'] or 'data-appendix-navigation' in a:self.skip+=1
  if self.inbody and t in ['svg','path','line','circle','rect','polyline','polygon','ellipse']:
   keys=['viewbox','d','x','y','x1','x2','y1','y2','cx','cy','r','rx','ry','width','height','points','stroke','stroke-width','stroke-dasharray','fill','transform']
   self.geom.append((t,{k:v for k,v in a.items() if k in keys}))
  if self.inbody:
   values={k:v for k,v in a.items() if k=='style' or k.startswith('data-') and not k.startswith(('data-exhibit','data-article','data-appendix-navigation'))}
   if values:self.encodings.append((t,values))
  if self.inbody and t in ['td','th']:self.cell=[]
  if t in ['br','img','input','meta','link','hr','source','wbr']:self.stack.pop()
 def handle_startendtag(self,t,attrs):
  self.handle_starttag(t,attrs)
  if t not in ['br','img','input','meta','link','hr','source','wbr']:self.handle_endtag(t)
 def handle_data(self,s):
  if self.inbody and not self.skip:
   s=' '.join(s.split())
   if s:self.text.append(s)
   if self.cell is not None:self.cell.append(s)
 def handle_endtag(self,t):
  if self.cell is not None and t in ['td','th']:self.cells.append(' '.join(self.cell));self.cell=None
  for i in range(len(self.stack)-1,-1,-1):
   if self.stack[i][0]==t:
    _,self.skip,self.inbody=self.stack[i];del self.stack[i:];break

def fingerprint(html):
 a=Audit();a.feed(html)
 # Links and disclosure wrappers may split text nodes without changing the words.
 values={key:getattr(a,key) for key in ['text','geom','cells','encodings']}
 values['text']=re.sub(r'\s+','',''.join(a.text))
 return {key:{'count':len(value), 'sha256':hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()} for key,value in values.items()}

def main():
 parser=argparse.ArgumentParser(description='Verify presentation changes preserve the published research.')
 parser.add_argument('--origin',default='http://localhost:8772')
 args=parser.parse_args()
 baseline=json.loads(Path(__file__).with_name('exhibit-preservation-baseline.json').read_text())
 for slug,expected in baseline.items():
  actual=fingerprint(urlopen(args.origin.rstrip('/')+'/research/'+slug).read().decode())
  for field in expected:
   assert actual[field]==expected[field], f'{slug}: {field} changed. Preserve the published information.'
  print(f'PASS {slug}: research text, {actual["cells"]["count"]} cells, {actual["geom"]["count"]} geometry elements and encoded values unchanged')

if __name__=='__main__': main()
