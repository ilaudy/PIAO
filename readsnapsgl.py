import numpy as np
from struct import unpack
from time import time

def readsnapsgl(filename,block,endian=None,quiet=None,longid=None,met=None, fmt=None):
    #little endian : ">", big endian : "<", other/default : "=" or "@"
    #longid False or leave it empty for not using. =True if long id is needed
    # met, "z", if you need metal in z instead of elements.
    # fmt, default or 1 G3 format with blocks, 0 G2 format

    if endian == None:
        endian = "="
    if fmt == None:
        #try to get the format
        npf=open(filename,'r')
        bs1=unpack(endian+'i',npf.read(4))[0]
        if bs1==256:
            fmt = 0
        elif bs1 == 8:
            fmt =1
        else:
            print "Not knowing what is this value ", bs1, "still assuming format G3"
            print "This may have incorrect results, better have a check on endian."
            fmt=1
        npf.close()

    if longid == None:
        longid = False

    if block=='HEAD':
        npf=open(filename,'r')
        if fmt == 1:
            bname,bsize=read_bhead(npf)
        bs1=npf.read(4) #size of header
        npart=np.zeros(6,dtype='int32')
        npart[:]=unpack(endian+'i i i i i i',npf.read(4*6))
        masstbl=np.zeros(6,dtype='float64')
        masstbl[:]=unpack(endian+'d d d d d d',npf.read(8*6))
        time,red=unpack(endian+'d d',npf.read(2*8))
        F_sfr,F_fb=unpack(endian+'i i',npf.read(2*4))
        Totnum=np.zeros(6,dtype='int64')
        Totnum[:]=unpack(endian+'i i i i i i',npf.read(6*4))
        F_cool,Numfiles=unpack(endian+'i i',npf.read(2*4))
        Boxsize,Omega0,OmegaLambda,Hubbleparam=unpack(endian+'d d d d', npf.read(4*8))
        npf.close()
        return(npart,masstbl,time,red,Totnum,Boxsize,Omega0,OmegaLambda,Hubbleparam)
    else:
        npf=open(filename,'r')
        if fmt == 1:
            bname,bsize=read_bhead(npf)
        bs1=npf.read(4)
        npart=np.zeros(6,dtype='int32')
        npart[:]=unpack(endian+'i i i i i i',npf.read(4*6))
        masstbl=np.zeros(6,dtype='float64')
        masstbl[:]=unpack(endian+'d d d d d d',npf.read(8*6))
        if block=="MASS": 
            idg0=(npart>0) & (masstbl<=0)
            if len(npart[idg0])==0:
                idg1=(npart>0) & (masstbl>0)
                if len(npart[idg1])==1:
                    return masstbl[idg1]
                else:   #multi masstble
                    totmass=np.zeros(np.sum(npart,dtype=np.int64),dtype='float32')
                    countnm=0
                    for i in np.arange(6):
                        if npart[i]>0:
                            totmass[countnm:countnm+npart[i]]=masstbl[i]
                            countnm+=npart[i]
                    return totmass

        subdata=read_block(npf,block,endian,quiet,longid,fmt)
        if subdata is not None:
            npf.close()
            if block=="MASS":      #We fill the mass with the mass tbl value if needed
                idg0=(npart>0) & (masstbl>0)
                if len(npart[idg0])>0:
                    totmass=np.zeros(np.sum(npart,dtype=np.int64),dtype='float32')
                    bgc=0
                    subc=0
                    for k in np.arange(6):
                        if npart[k]>0:
                            if(masstbl[k]>0):
                                totmass[bgc:bgc+npart[k]]=np.zeros(npart[k],dtype='float32')+masstbl[k]
                            else:
                                totmass[bgc:bgc+npart[k]]=subdata[subc:subc+npart[k]]
                                subc+=npart[k]
                            bgc+=npart[k]
                    return totmass
                else:
                    return subdata
            elif (block=="Zs  ") & (met == 'z'):
                if masstbl[0]>0:
                    mass=np.zeros(npart[0],dtype=masstbl.dtype)+masstbl[0]
                else:
                    mass=read_block(npf,"MASS",endian,1,longid,fmt)
                zs=np.zeros(npart[0]+npart[4],dtype=subdata.dtype)
                zs[0:npart[0]]=np.sum(subdata[0:npart[0],1:],axis=1,dtype=np.float64)/ \
                    (mass[0:npart[0]]-np.sum(subdata[0:npart[0],:],axis=1,dtype=np.float64))
                mass=0
                im=read_block(npf,"iM  ",endian,1,longid,fmt)
                zs[npart[0]:] =np.sum(subdata[npart[0]:,1:],axis=1,dtype=np.float64)/ \
                    (im-np.sum(subdata[npart[0]:,:],axis=1,dtype=np.float64))
                im,subdata=0,0
                return zs
            else:
                return subdata
        else:
            print "No such blocks!!!", block
            npf.close()
            return(0)

#Read Block
def read_block(npf, block,endian,quiet,longid,fmt):
    bname='BLOCK_NAME'
    if fmt == 1:
        npf.seek(16+264)        #skip block(16) + header (264)
    else:
        npf.seek(264)        #skip header (264)
    loopnum=0
    while bname!='INFO' :   #Ending block
        if fmt == 1:
            bname,bsize=read_bhead(npf)
            bsize=unpack(endian+'i',bsize)[0]
        else:
            bsize=npf.read(4)
            bsize=unpack(endian+'i',bsize)[0]
	    npf.seek(npf.tell()-4)

            if (block=='POS ') & (loopnum==0):
                return read_bdata(npf,3,np.dtype('float32'),endian)
                
            elif (block=='VEL ') & (loopnum==1):
                return read_bdata(npf,3,np.dtype('float32'),endian)

            elif (block=='ID  ') & (loopnum==2):
                if longid:
                    return read_bdata(npf,1,np.dtype('uint64'),endian)
                else:
                    return read_bdata(npf,1,np.dtype('uint32'),endian)

            elif (block=='MASS') & (loopnum==3):
                return read_bdata(npf,1,np.dtype('float32'),endian)
            
            elif loopnum>3:
                return None

            loopnum += 1 

        if quiet == None:
	    print bname,bsize

        if bname==block=='POS ':
            return read_bdata(npf,3,np.dtype('float32'),endian)

        elif bname==block=='VEL ':
            return read_bdata(npf,3,np.dtype('float32'),endian)

        elif bname==block=='ID  ':
            if longid:
                return read_bdata(npf,1,np.dtype('uint64'),endian)
            else:
                return read_bdata(npf,1,np.dtype('uint32'),endian)

        elif bname==block=='MASS':
            return read_bdata(npf,1,np.dtype('float32'),endian)

        elif bname==block=='RHO ':
            return read_bdata(npf,1,np.dtype('float32'),endian)

        elif bname==block=='SFR ':
            return read_bdata(npf,1,np.dtype('float32'),endian)

        elif bname==block=='AGE ':
            return read_bdata(npf,1,np.dtype('float32'),endian)

        elif bname==block=='POT ':
            return read_bdata(npf,1,np.dtype('float32'),endian)

        elif bname==block=='iM  ':
            return read_bdata(npf,1,np.dtype('float32'),endian)

        elif bname==block=='Zs  ':
            return read_bdata(npf,11,np.dtype('float32'),endian)

        elif bname==block=='HOTT':
            return read_bdata(npf,1,np.dtype('float32'),endian)

        elif bname==block=='CLDX':
            return read_bdata(npf,1,np.dtype('float32'),endian)

        elif bname==block=='TEMP':
            return read_bdata(npf,1,np.dtype('float32'),endian)

        else:
            if fmt == 1:
                npf.seek(bsize+npf.tell())
            else:
                npf.seek(bsize+8+npf.tell())

    return None


#Read Block Head
def read_bhead(npf):
    dummy=npf.read(4) #dummy
    bname=npf.read(4)                    #label
    bsize=npf.read(4) #size
    dummy=npf.read(4) #dummy
    return bname,bsize
#Read Block data
def read_bdata(npf,column,dt,endian):
    bs1=unpack(endian+'i',npf.read(4))[0]
    buf=npf.read(bs1)
    if column ==1:
        arr=np.ndarray(shape=bs1/dt.itemsize,dtype=dt,buffer=buf)
    else:
        arr=np.ndarray(shape=(bs1/dt.itemsize/column,column),dtype=dt,buffer=buf)

    if endian=='=':
        return arr
    else:
        return arr.byteswap()

