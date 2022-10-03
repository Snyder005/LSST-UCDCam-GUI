
import pyfits,glob,time,scipy,re,time
import scipy.interpolate
from numpy import *
from matplotlib.pyplot import *
from subprocess import call
from IPython import parallel
global thedir,configfile,paramfile
from itertools import cycle

configfile='/sandbox/lsst/lsst/GUI/sextractor/default-array_dither.sex'
paramfile='/sandbox/lsst/lsst/GUI/sextractor/default-array_dither.param'
maskdir='/sandbox/lsst/lsst/GUI/sextractor/masks/'
thedir='/sandbox/lsst/lsst/GUI/testdata/'


segdict=dict(zip(arange(1,17),['10','11','12','13','14','15','16','17','07','06','05','04','03','02','01','00']))
#get_ipython().magic(u'matplotlib inline')
#get_ipython().magic(u'cd $thedir')


# ### Define what pattern to look for in the directory listed above. The firstnum and date in pattern should be changed

pattern=str(sys.argv[1])
firstnum = pattern.split('_')[3].strip('??')

zfilelist=sort(glob.glob(thedir+pattern))[:]

print "Running %d files"%len(zfilelist)


# ## Read in a region file produced by making rectangle regions on individual segments of a mosaic iraf image in DS9. Save the region file as whatever name you like (enter below), making sure to save in the "ds9" format and "image" coords when it asks

regfilename='/sandbox/lsst/lsst/GUI/notebooks/focuscurveareas_small.reg'
f=open(regfilename)
lines=f.readlines()

regions=[]
for line in lines[3:]:
    if line[:6]=='# tile':
        tilenum=int(line.split()[2])
        #print "Tile number: "+str(tilenum)
    if line[:3]=='box':
        regnums,regend=re.split('#',line)
        yc,xc,ys,xs=[int(float(val)) for val in re.split(',',regnums[4:-4])]
        regtxt=re.split('}',re.split('{',regend)[1])[0]
        regions.append([tilenum,xc,yc,xs/2,ys/2,regtxt])
        print tilenum,segdict[tilenum],xc,yc,xs,ys,regtxt


# ## Gather the imaging data inside the region file, write it out to fits images for SExtractor to process, and read in the catalogs output

tilenum_all=[]
expnum_all=[]
zpos_all=[]
xsize_all=[]
ysize_all=[]
regtxt_all=[]

time_start=time.time()
for fitsfilename in zfilelist[:]:
    expnumber=fitsfilename.split('_')[3]
    print "Exposure #: "+str(expnumber)
    zpos=pyfits.open(fitsfilename)[17].header['Z_POS']
    for reg in regions:
        tilenum,xc,yc,xs,ys,regtxt=reg
        img=pyfits.getdata(fitsfilename,"SEGMENT"+segdict[tilenum])
        imsnip=img[xc-xs/2:xc+xs/2,yc-ys/2:yc+ys/2]
        outname=fitsfilename[:-5]+"SEGMENT"+segdict[tilenum]+"snip.fits"
        pyfits.writeto(outname,imsnip,clobber=True)
        test=call(["sex",outname,"-c",configfile,"-CATALOG_NAME",outname+'.cat'])
        cat=pyfits.getdata(outname+'.cat','LDAC_OBJECTS')
        xsize_med=median(cat['X2WIN_IMAGE'])
        ysize_med=median(cat['Y2WIN_IMAGE'])
        call(["rm",outname,outname+'.cat'])
        tilenum_all.append(tilenum)
        expnum_all.append(expnumber)
        zpos_all.append(zpos)
        xsize_all.append(xsize_med)
        ysize_all.append(ysize_med)
        regtxt_all.append(regtxt)

print "All done, took "+str(time.time()-time_start)+" seconds"
tilenum_all=array(tilenum_all)
expnum_all=array(expnum_all,dtype='int16')
zpos_all=array(zpos_all)
xsize_all=array(xsize_all)
ysize_all=array(ysize_all)

regtxt_all=array(regtxt_all)


# ## Plot all the statistics from the region and fit a polynomial to find the best focus


colors = ['b','g','r','c','m']
lines = ["-","--","-.",":"]
colorcycler = cycle(colors)

if fitsfilename.split('_')[1]=='spot-3um':
    maxsig=.9
if fitsfilename.split('_')[1]=='spot-30um':
    maxsig=1.4


figure(figsize=(10,10))
for loc in unique(regtxt_all):
    plotcolor=next(colorcycler)
    g=where((regtxt_all==loc) & (xsize_all<maxsig)& (xsize_all!='nan'))[0]
    #xvals,yvals=zpos_all[g],a_img_med_all[g]
    xvals,yvals=zpos_all[g],xsize_all[g]
    
    #fit the xvals and yvals with a polynomial to find best focus
    #  could use interpolation to find it, but the coefficients might be useful
    coeffs=polyfit(xvals,yvals,6)
    polynom=poly1d(coeffs)
    xlin=linspace(min(xvals),max(xvals),100)
    yfit=polynom(xlin)
    best_foc=xlin[where(yfit==min(yfit))]
    
    plot(xvals,yvals,color=plotcolor,marker='o',linestyle='None',markersize=10,
        label=loc+', z$_{foc}$='+str(float(best_foc))[:6]+", min$_{foc}$="+str(float(min(yfit)))[:5])
    plot([best_foc,best_foc],[.6,min(yfit)],color=plotcolor)
    plot(xlin,yfit,color=plotcolor,linewidth=5,alpha=.4)
xlabel('Z_POS [microns]',fontsize=20)
ylabel('Pinhole x moment [pixels]',fontsize=20)
legend(loc='upper center')
title('X-Focus curve for locations around CCD\n'+time.strftime("%Y-%m-%d %H:%M")+'    '+firstnum+'00_series',fontsize=24)
savefigname='/home/lsst/Desktop/plots/focuscurves/'+time.strftime("%Y-%m-%d %H:%M")+'-X_focus_curve_'+firstnum+'00_series.png'

savefig(savefigname)

figure(figsize=(10,10))
for loc in unique(regtxt_all):
    plotcolor=next(colorcycler)
    g=where((regtxt_all==loc) & (ysize_all<maxsig))[0]
    #xvals,yvals=zpos_all[g],a_img_med_all[g]
    xvals,yvals=zpos_all[g],ysize_all[g]
    
    #fit the xvals and yvals with a polynomial to find best focus
    #  could use interpolation to find it, but the coefficients might be useful
    coeffs=polyfit(xvals,yvals,6)
    polynom=poly1d(coeffs)
    xlin=linspace(min(xvals),max(xvals),100)
    yfit=polynom(xlin)
    best_foc=xlin[where(yfit==min(yfit))]
    
    plot(xvals,yvals,color=plotcolor,marker='o',linestyle='None',markersize=10,
        label=loc+', z$_{foc}$='+str(float(best_foc))[:6]+", min$_{foc}$="+str(float(min(yfit)))[:5])
    plot([best_foc,best_foc],[.6,min(yfit)],color=plotcolor)
    plot(xlin,yfit,color=plotcolor,linewidth=5,alpha=.4)
xlabel('Z_POS [microns]',fontsize=20)
ylabel('Pinhole y moment [pixels]',fontsize=20)
legend(loc='upper center')
title('Y-Focus curve for locations around CCD\n'+time.strftime("%Y-%m-%d %H:%M")+'    '+firstnum+'00_series',fontsize=24)
savefigname='/home/lsst/Desktop/plots/focuscurves/'+time.strftime("%Y-%m-%d %H:%M")+'-Y_focus_curve_'+firstnum+'00_series.png'
savefig(savefigname)
