import av,sys
from PIL import Image, ImageDraw
src,out,step=sys.argv[1],sys.argv[2],float(sys.argv[3])
c=av.open(src); frames=[]; nxt=0.0
for f in c.decode(video=0):
    if f.time>=nxt:
        im=f.to_image().resize((640,360)); ImageDraw.Draw(im).text((10,330),"%.1fs"%f.time,fill=(255,255,0)); frames.append(im); nxt+=step
cols=3; rows=(len(frames)+cols-1)//cols
M=Image.new("RGB",(640*cols,360*rows))
for i,im in enumerate(frames): M.paste(im,((i%cols)*640,(i//cols)*360))
M.save(out)
