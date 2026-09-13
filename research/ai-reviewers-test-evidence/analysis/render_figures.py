"""Portable SVG-only rendering of the three audited article figures.

Original drawing coordinates retained. No Pillow, OS fonts or network needed.
Browser font selection may change text appearance; numerical data are unchanged.
"""
from pathlib import Path
import hashlib, html, json

HERE=Path(__file__).resolve().parent.parent/'output'
MODELS=['openai/gpt-5.6-terra','anthropic/claude-sonnet-5','google/gemini-3.8-flash']
NAMES=['GPT 5.6 Terra','Claude Sonnet 5','Gemini 3.8 Flash']
COLORS=['#006D77','#A64B2A','#6654A3']
INK='#192D33';MUTED='#53676C';GRID='#DDE5E5';BG='#FFFFFF'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Chart:
    def __init__(self,w,h,title,desc):
        self.w=w;self.h=h;self.scale=2
        self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',f'<title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(desc)}</desc>',f'<rect width="{w}" height="{h}" fill="{BG}"/>']
    def text(self,x,y,s,size=20,color=INK,bold=False,anchor='start'):
        s=str(s)
        self.svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{html.escape(s)}</text>')
    def line(self,x1,y1,x2,y2,color=GRID,width=1,dashed=False):
        self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="5 5"' if dashed else '')+'/>')
    def rect(self,x,y,w,h,color):
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>')
    def dot(self,x,y,color,r=6,square=False):
        if square:return self.rect(x-r,y-r,r*2,r*2,color)
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')
    def save(self,name):
        (HERE/(name+'.svg')).write_text('\n'.join(self.svg+['</svg>'])+'\n')

def footer(c,y):
    c.line(40,y-22,c.w-40,y-22)
    c.text(40,y,'A  Issue + patch only     B  Factual summary     C  Full report, source unspecified',18)
    c.text(40,y+29,'D  Full report attributed to patch-producing system     E  Identical report attributed to a separate evaluator',18)
    c.text(40,y+64,'Source labels are hypothetical. Sonnet uses a native JSON constraint in the follow-up phase.',17,MUTED)

def approval(rows):
    title='Approval across five review scenarios'
    c=Chart(1440,770,title,'Three panels show follow-up approval divided by usable responses. Each bar has its exact numerator and denominator. Missing responses are excluded, not treated as rejection.')
    c.text(40,55,title,36,bold=True)
    c.text(40,93,'Follow-up: 40 task cases · all usable responses · two planned reviews per task and scenario',21,MUTED)
    for j,m in enumerate(MODELS):
        x=40+j*466; c.text(x,150,NAMES[j],25,bold=True)
        left=x+29;width=280
        for t in [0,25,50,75,100]:
            xx=left+width*t/100;c.line(xx,180,xx,513);c.text(xx,544,f'{t}%',16,MUTED,anchor='middle')
        for k,cond in enumerate('ABCDE'):
            row=next(r for r in rows if r['phase']==2 and r['model']==m and r['condition']==cond)
            y=207+k*65;c.text(x,y+6,cond,20,bold=True)
            c.rect(left,y-7,width,14,'#EDF1F1');c.rect(left,y-7,width*row['approval_rate'],14,COLORS[j])
            c.text(x+329,y+1,f"{row['approval_rate']*100:.1f}%",19,bold=True)
            c.text(x+329,y+22,f"{row['approvals']}/{row['usable']}",16,MUTED)
    c.text(40,580,'Bar labels: approvals / usable reviews. Varying denominators; not matched scenario-effect estimates.',18,MUTED)
    footer(c,633)
    c.text(40,731,'1,200 planned · 1,136 attempted · 1,129 usable · 7 invalid · 64 unattempted. No retries or missing-value imputation.',17,MUTED)
    c.save('figure-1-approval')

def source_effect(rows):
    title='The initial source-attribution signal weakened in the follow-up'
    c=Chart(1440,830,title,'Paired E minus D approval effects in the original 20-task phase and 40-task follow-up, with task-resampling intervals and complete-task counts. No cross-phase pooling.')
    c.text(40,55,title,34,bold=True)
    c.text(40,94,'Change only the assigned source of the identical full report: separate evaluator (E) − patch producer (D)',20,MUTED)
    old='#A64B2A';new='#006D77'
    for x,color,square,text in [(40,old,False,'Initial 20-task phase'),(385,new,True,'40-task follow-up')]:
        c.dot(x+7,134,color,6,square);c.text(x+25,141,text,20)
    left=370;width=750;lo=-20;hi=35
    fx=lambda v:left+width*(v-lo)/(hi-lo)
    for tick in [-20,-10,0,10,20,30]:
        c.line(fx(tick),181,fx(tick),598,INK if tick==0 else GRID,2 if tick==0 else 1,dashed=tick==0)
        c.text(fx(tick),635,f'{tick:+d}' if tick else '0',18,MUTED,anchor='middle')
    for j,model in enumerate(MODELS+['pooled']):
        y=222+j*111
        c.text(40,y+5,(NAMES+['Three-model mean'])[j],23,bold=True)
        if model=='pooled':c.text(40,y+31,'Common complete tasks only',17,MUTED)
        for phase,color,offset,square in [(1,old,-15,False),(2,new,20,True)]:
            r=next(z for z in rows if z['phase']==phase and z['model']==model)
            low,high=[v*100 for v in r['bootstrap_95_interval']];mean=r['mean']*100;yy=y+offset
            c.line(fx(low),yy,fx(high),yy,color,3)
            c.line(fx(low),yy-6,fx(low),yy+6,color,2);c.line(fx(high),yy-6,fx(high),yy+6,color,2)
            c.dot(fx(mean),yy,color,7,square)
            c.text(1170,yy+6,f"{mean:+.1f} pp · {r['n_tasks']} tasks",19,color)
    c.text((left+1120)/2,674,'E − D approval difference (percentage points)',21,anchor='middle')
    c.text(40,718,'Whiskers: 95% task-bootstrap stability intervals on complete paired blocks; not population confidence intervals.',18,MUTED)
    c.text(40,746,'Both repeats of D and E are required. Source labels are hypothetical; the full report body is unchanged.',18,MUTED)
    c.text(40,774,'Phases differ in tasks; Sonnet also gained a native JSON constraint. Full-roster missingness bounds accompany the data.',18,MUTED)
    c.text(40,802,'Phase 1: 37 invalid / 0 unattempted. Follow-up: 7 invalid / 64 unattempted. No pooled cross-phase effect is shown.',18,MUTED)
    c.save('figure-3-source-effect')

def benchmark_approval(rows):
    title='Acceptance differs despite few benchmark-failing approvals'
    c=Chart(1440,920,title,'Two panels show approval of benchmark-passing and benchmark-failing patches in follow-up common-task sets. Three colored points per scenario include task-level conservative intervals; zero observed approvals do not imply zero risk.')
    c.text(40,55,title,35,bold=True)
    c.text(40,94,'Follow-up · same tasks across all three models within each scenario · two usable repeats required',20,MUTED)
    for j in range(3):
        xx=40+j*360;c.dot(xx+6,133,COLORS[j],6);c.text(xx+24,140,NAMES[j],20)
    for panel,label in enumerate(['correct','incorrect']):
        left=98+panel*710;width=560;top=226;height=328;bottom=top+height
        c.text(left-58,196,'Benchmark-passing patches' if label=='correct' else 'Benchmark-failing patches',25,bold=True)
        for tick in [0,25,50,75,100]:
            y=bottom-height*tick/100;c.line(left,y,left+width,y)
            c.text(left-16,y+6,f'{tick}%',17,MUTED,anchor='end')
        for k,cond in enumerate('ABCDE'):
            xx=left+40+k*120
            group=[r for r in rows if r['phase']==2 and r['condition']==cond and r['label']==label]
            assert len(group)==3 and len({r['n_tasks'] for r in group})==1
            for j,m in enumerate(MODELS):
                r=next(z for z in group if z['model']==m);x=xx+(j-1)*18
                low,high=r['interval95'];y=bottom-height*r['estimate'];yl=bottom-height*low;yh=bottom-height*high
                c.line(x,yh,x,yl,COLORS[j],2);c.line(x-4,yh,x+4,yh,COLORS[j],2);c.line(x-4,yl,x+4,yl,COLORS[j],2);c.dot(x,y,COLORS[j],5)
            c.text(xx,588,cond,21,bold=True,anchor='middle')
            c.text(xx,617,f"{group[0]['n_tasks']} tasks",16,MUTED,anchor='middle')
            c.text(xx,639,f"{group[0]['n_reviews']} reviews",16,MUTED,anchor='middle')
    c.text(40,683,'Whiskers: conservative 95% task-level sensitivity intervals; not independent-review or population intervals.',18,MUTED)
    c.text(40,713,'Matched within each scenario; denominators are per model. The task set can differ between scenarios.',18,MUTED)
    footer(c,762)
    c.text(40,860,'Post-hoc benchmark scoring. B–E use evidence from the same evaluation defining the labels, not independent verification.',17,MUTED)
    c.text(40,890,'40 planned tasks · 7 invalid responses · 64 unattempted. Common-task subsets omit missing blocks; no imputation.',17,MUTED)
    c.save('figure-2-benchmark-approval')

def main():
    data=read(HERE/'figure-data.json')
    approval(data['approval'])
    benchmark_approval(data['benchmark_approval'])
    source_effect(data['source_effect'])

if __name__=='__main__':main()
