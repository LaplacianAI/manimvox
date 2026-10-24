import av,sys
src,out,*ts=sys.argv[1:]
c=av.open(src)
want=sorted(float(t) for t in ts); i=0
for f in c.decode(video=0):
    if i<len(want) and f.time>=want[i]:
        f.to_image().save(f"{out}_{i}.png"); i+=1
