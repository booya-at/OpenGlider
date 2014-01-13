import openglider.Graphics

poly = [[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.]]
poly2 = [[0.,0.,1.],[1.,0.,1.],[1.,1.,1.],[0.,1.,1.]]
openglider.Graphics.Graphics([openglider.Graphics.Line([0,1,2,3]),openglider.Graphics.Line(poly2),
                              openglider.Graphics.Axes()], poly+poly2)

