import tempfile
#import os

def XValues(list1,list2):
    """Get a list of Values to compare against another one and delete values if not necessary to calculate again"""
    ###check for list1 to be a list of angles
    if isinstance(list1,list):
        temp=list1.copy()
    else:
        temp=[list1]
    temp2=temp.copy()
    ###check if list2 is not empty and remove all values already calculated from temp2
    if len(list2)>0:
        print(temp)
        for i in temp:
            if i in list2[:][0]:
                temp2.remove(i)
    return temp2

def Calcfile(aoalist,xfoutput=tempfile.gettempprefix()+'/xfoutput.dat',renum=200000):
    """Export Calculation command file"""
    temporarydict=tempfile.gettempprefix()
    print(temporarydict)
    cfile='/'+temporarydict+'/xfoilcommand.dat'

    xfcommand=open(cfile,'w')
    xfcommand.write('plop\ng\n\n')
    ##define Re-Num
    xfcommand.write('OPER\nRE\n'+str(renum)+'\n')
    xfcommand.write('VISC\n')
    xfcommand.write('PACC\n'+xfoutput+'\n'+xfoutput+'2.dat\n')
    if isinstance(aoalist,list):
        for aoa in aoalist:
            xfcommand.write('ALFA\n')
            xfcommand.write(str(aoa)+'\n')
    else:
        xfcommand.write('ALFA\n')
        xfcommand.write(str(aoalist)+'\n')
    xfcommand.write('\nquit')
    xfcommand.close()
    return cfile

def Impresults(resfile):
    xfile=open(resfile,"r")
    init=0
    erg={}
    index=temp=[]##due to pydev-error
    
    for line in xfile:
        line=line.strip()
        if len(line)>0:
            line=line.split(" ")
            ##remove leading zero-elements
            while "" in line:
                line.remove("")
            print(line)
            if init==1:
                erg[float(line[0])]={index[i]: float(line[i]) for i in range(1,len(line))}
            if line[0][0]=="-":
                print("ok")
                init=1
                index=temp
            temp=line
    print(index)
    return erg