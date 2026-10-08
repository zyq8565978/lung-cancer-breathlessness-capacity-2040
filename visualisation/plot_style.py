from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb, LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, FancyArrowPatch
from PIL import Image, ImageOps

LAVENDER='#b6b3d6';PEACH='#f6b3a0';ROSE='#eb687b';WARM='#d6d1d1'
COLORS=dict(zip(STRATEGIES,[LAVENDER,PEACH,ROSE]))
ACT_COLORS=[LAVENDER,PEACH,WARM]
CONTACT_COLORS=[LAVENDER,PEACH,ROSE]
STYLES=['-','--','-.'];MARKERS=['o','s','D'];HATCHES=['','///','xx']
REGION_COLORS=dict(zip(REGIONS,[ROSE,'#d0cce5',PEACH,WARM,'#f1837b',LAVENDER]))
REGION_STYLES=['-',(0,(5,2)),(0,(3,1,1,1)),(0,(1,1)),(0,(7,2,1,2)),(0,(3,2))]
AUDIT=[]
plt.rcParams.update({'font.family':'Arial','font.size':8.5,'axes.titlesize':10,'axes.labelsize':9,
    'xtick.labelsize':8.5,'ytick.labelsize':8.5,'axes.spines.top':False,'axes.spines.right':False,
    'axes.linewidth':.65,'lines.linewidth':1.6,'pdf.fonttype':42,'ps.fonttype':42,
    'svg.fonttype':'none','figure.facecolor':'white','savefig.facecolor':'white',
    'hatch.linewidth':.35,'text.color':'#252525','axes.labelcolor':'#252525'})
def dark(color):return tuple(.72*np.array(to_rgb(color)))
def axis(fig,rect,letter,title):
    ax=fig.add_axes(rect)
    ax.set_title(title,loc='left',pad=12,fontweight='semibold')
    ax.text(-.16,1.08,letter,transform=ax.transAxes,fontsize=12,fontweight='bold',va='bottom')
    ax.tick_params(length=3,width=.65)
    return ax
def grid(ax):
    ax.grid(axis='x',color='#e5e5e5',lw=.5);ax.set_axisbelow(True)
def legends(fig,items,y,ncol):
    fig.legend(handles=items,loc='lower center',bbox_to_anchor=(.5,y),ncol=ncol,frameon=False,handlelength=1.7,columnspacing=1.2)
def patch(color,label,hatch=''):
    return Rectangle((0,0),1,1,facecolor=color,edgecolor=dark(color),lw=.6,hatch=hatch,label=label)
def strategies(fig,y=.02):
    legends(fig,[patch(COLORS[s],NAMES[s],HATCHES[j]) for j,s in enumerate(STRATEGIES)],y,3)
def export(fig,name,folder):
    fig.canvas.draw();ren=fig.canvas.get_renderer();fw,fh=fig.canvas.get_width_height()
    outside=[]
    for t in fig.findobj(matplotlib.text.Text):
        if not t.get_visible() or not t.get_text():continue
        b=t.get_window_extent(ren)
        if b.x0 < -1 or b.y0 < -1 or b.x1>fw+1 or b.y1>fh+1:outside.append(t.get_text())
    AUDIT.append({'figure':name,'text_outside_canvas':outside,'width_mm':fig.get_figwidth()*25.4,'height_mm':fig.get_figheight()*25.4})
    out=ROOT/folder/name
    for ext in ['pdf','svg']:fig.savefig(str(out)+'.'+ext)
    fig.savefig(str(out)+'.png',dpi=600)
    path=ROOT/'author_records/qa'/f'{name}_preview.png'
    fig.savefig(path,dpi=170)
    im=Image.open(path).convert('RGB')
    ImageOps.grayscale(im).save(path.with_name(f'{name}_greyscale.png'))
    a=np.asarray(im,dtype=float)/255
    mat=np.array([[.152286,1.052583,-.204868],[.114503,.786281,.099216],[-.003882,-.048116,1.051998]])
    Image.fromarray((np.clip(a@mat.T,0,1)*255).astype('uint8')).save(path.with_name(f'{name}_protanopia.png'))
    plt.close(fig)
