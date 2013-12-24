#include <iostream>  //file/terminal i/o
#include <Eigen/Dense>  //matrix calculations/linalg
#include <map>
#include <cmath>

double pi=3.14159265358979323846;



std::std::map<string, string> config;  //config-dictionary






void main(int argc, char* argv[]){
	//Parse Command Line
	if (argc < 3) { // more than 4 arguments, or do nothing.
        usage(); // usage
        exit(0);
    }
    else{
    	char* inpath = "";
    	char* outpath = "";
    	for (int i = 1; i < argc-1; i++) { //Iterate ober argv-elements
			if (argv[i] == "-in") { //next->inputfile
                    inpath = argv[i + 1];
                }
            else if (argv[i] == "-out") { //next->outputfile
                    outpath = argv[i + 1];
                }
            }
        if (outpath == "") outpath = inpath; //TODO: Append or change ending

		ofstream inputfile;
		inputfile.open("afile.dat");
		
		//bool passed = false;
		char* thisline;

		while( !passed && readline(inputfile, thisline)){
			if (thisline == "BLABALLALALLLLALLALA->panels")
				break;
			//Read Variables

		}

		//Read Points

		//Read Panels+Wake

		// -> struct panel -> p1(int), p2, p3, p4, normvekt, 

		inputfile.close();


		cout "etwas, " << "nowas" << endl;

		cout "Loading File" << endl << endl;

		cout "Airspeed:  " << config["AIRSPEED"] << endl;
		cout "Density:  " << config["DENSITY"] << endl;
		cout "Pressure [Pa]:  " << config["PRESSURE"] << endl;
		cout "Number of cases:  " << config["CASENUM"] << endl;
		//casenum=3 -> anglesofattack: 0 0 0; sideslip_angles: 0 0 0
		cout "WINGSPAN: " << config["WINGSPAN"] << endl;
		cout "SURFACE: " << config["SURFACE"] << endl;
		// ERROR, COLLDIST, FARFIELD=5, 
		//Results: coefficients, forces, geometry, velocity, pressure, center points, doublet values, source values, velocity components, mesh caracteristics, static pressure, dynamic pressure, manometer pressure (1/0)



		cout "Calculating Matrix" << endl;



		cout "Solving System" << endl;


	}




}

void usage(){
	cout << "Booya-Panel-Solver\n";
	cout << "Usage is -in <infile> -out <outdir>\n";
}


double norm2d (double *vektor){
	return(sqrt(pow(vektor[0],2)+pow(vektor[1],2)));}

double norm3d (double *vektor){
	return(sqrt(pow(vektor[0],2)+pow(vektor[1],2)+pow(vektor[2],2)));}

void normalize2d (double *vektor){
	double faktor = norm2d(vektor);
	if(faktor!=0){
	vektor[0]=vektor[0]/faktor;
	vektor[1]=vektor[1]/faktor;}}

void normalize3d (double *vektor){
	double faktor = norm3d(vektor);
	if(faktor!=0){
		vektor[0]=vektor[0]/faktor;
		vektor[1]=vektor[1]/faktor;
		vektor[2]=vektor[2]/faktor;}}

double dot_3d (double *vektor1, double *vektor2){  //return double-value of dot-product
	return vektor1[0]*vektor2[0]+vektor1[1]*vektor2[1]+vektor1[2]*vektor2[2];}

void* cross_3d (double *vektor1, double *vektor2){  //Return cross-product-array
	double temp[3];
	temp[0]=vektor1[1]*vektor2[2]-vektor1[2]*vektor2[1];
	temp[1]=-vektor1[0]*vektor2[2]+vektor1[2]*vektor2[0];
	temp[2]=vektor1[0]*vektor2[1]-vektor1[1]*vektor2[0];
	return temp}

void vektadd (double *vektor1, double *vektor2){
	vektor1[0]=vektor1[0]+vektor2[0];
	vektor1[1]=vektor1[1]+vektor2[1];
	vektor1[2]=vektor1[2]+vektor2[2];
}

void setvekt (double *vektor1, double *vektor2){
	vektor1[0]=vektor2[0];
	vektor1[1]=vektor2[1];
	vektor1[2]=vektor2[2];
}

void vektsub (double *vektor1, double *vektor2){
	vektor1[0]=vektor1[0]-vektor2[0];
	vektor1[1]=vektor1[1]-vektor2[1];
	vektor1[2]=vektor1[2]-vektor2[2];
}

bool compare_vectors(double *vektor1, double *vektor2){
	if(vektor1[0]==vektor2[0] && vektor1[1]==vektor2[1] && vektor1[2]==vektor2[2]) return true;
	else return false;}


double coresize=0.00000000000000000001;

void NearFieldCalc (double *panelliste, double *nk, double *mk, double *lk, double *mj, double pn){
	//
	//panelpoints (4 punkte), nk vekt,mk vekt,lk vekt,mj vekt3d, pn double
	//


	long i,j;

	
	double bjk=0.;
	double cjk=0.;
	double panelpunkte[5][3];
	double schleife[4];

	for(i=-1;i<4;i++){
		for(j=0;j<3;j++)
		panelpunkte[i+1][j]=panelliste[i==-1?9+j:3*i+j];
	}//panelpunkte gesetzt

	double s[3],a[3],b[3],h[3];
	double abss,am,bm,sl,sm,al,al2,pa,pb,norm_a,norm_b,norm_s,cjki,bjki,gl,dnom,rnum,side;
	gl=0.;
	int sign;

	//total table
	for(i=0;i<4;i++){
		/*
		vektor s,a,b,h
		double abss,am,bm,sl,sm,al,al2,pa,pb,norm_a,norm_b,norm_s,cjki,bjki,gl,dnom,rnum,side
		int sign
		*/
		
		setvekt(s,panelpunkte[i+1]);
		vektsub(s,panelpunkte[i]);

		abss=norm3d(s);  //panelpunkte[i+1]-panelpunkte[i] -> eigen

		setvekt(a,mj);
		vektsub(a,panelpunkte[i]);

		setvekt(b,a);
		vektsub(b,s);

		//alles double, alles nach if-abfrage!!
		am=imp3d(a,mk);
		bm=imp3d(b,mk);
		sl=imp3d(s,lk);
		sm=imp3d(s,mk);
		al=imp3d(a,lk);
		al2=am*sl-al*sm;
		pa=pow(pn,2)*sl+al2*am;
		pb=pow(pn,2)*sl+al2*bm;
		norm_a=norm3d(a);
		norm_b=norm3d(b);
		norm_s=norm3d(s);  //WOFÜR?

		//vektor
		setvekt(h,a);
		cross3d(h,s);

		if(compare_vectors(panelpunkte[i],panelpunkte[i+1]) || (norm3d(h)/norm3d(s) <= coresize && imp3d(a,s) >= 0. && imp3d(b,s) <= 0.) || norm_a<=coresize || norm_b<=coresize){
			cjki=0.;
			bjki=0.;/*case1*/
			schleife[i]=0;}
		else{
			gl=log((norm_a+norm_b+abss)/(norm_a+norm_b-abss))/abss;
			dnom=pa*pb+pow(pn,2)*norm_a*norm_b*pow(sm,2);
			rnum=sm*pn*(norm_b*pa-norm_a*pb);
			schleife[i]=1;

			if(sqrt(pow(pn,2))<coresize){
				side=imp3d(nk,h);
				sign=side>0?-1.0:1.0;
				schleife[i]=2;
				if(dnom<0.0){
					if(pn>0.)	{cjki=pi*sign;schleife[i]=3;}
					else 		{cjki=-pi*s