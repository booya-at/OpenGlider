import numpy

def Point(profile,xval,h):
	if h==-1:
		return SinglePoint(profile,xval)
	else:
		p1=SinglePoint(profile,xval)[1]
		p2=SinglePoint(profile,-xval)[1]
		return p1+(h+1)/2*(p2-p1)


		
def SinglePoint(profile,xvalt):
	xval=float(xvalt)
	if abs(xval)>1:
		print("x zgros")
		
	#examine i-value
	if xval<0.:
		i=1
		xval=-xval
		while profile[i][0]>=xval and i<len(profile):
			i+=1
		i-=1
	else:
		i=len(profile)-2
		while profile[i][0]>xval and i>1:
			i-=1
	#examine r-value dx/rx=ds/rs->rs=ds*rx/dx
	r=-(profile[i][0]-xval)/(profile[i+1][0]-profile[i][0])
	(x,y)=profile[i]+r*(profile[i+1]-profile[i])
	return ((i,r),numpy.array([x,y]))
