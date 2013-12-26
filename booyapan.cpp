#include <iostream>  //file/terminal i/o
#include <Eigen/Core>  //matrix calculations/linalg
#include <Eigen/Geometry>
#include <Eigen/Dense>
#include <map>
#include <string>
#include <cmath>
#include <fstream>


//double pi=3.14159265358979323846;
const int max_linelength=100;
double pi=atan(1)*4;

typedef Eigen::Vector3d Vector;
std::map<std::string, std::string> config;  //config-dictionary

class Panel {
	public:
		bool wake;
		int p1;
		int p2;
		int p3;
		int p4;
		int neighbour_left;
		int neighbour_right;
		int neighbour_front;
		int neighbour_back;
		Vector n; //normal-vector
		Vector m; // tangential-vector (wingspan)
		Vector l; // tangential-vector (chordwise)
		float area; //Panel-Area
		Vector r_center;  //centerpoint

		Vector smp;
		Vector smq;

		float smp_len; //half median length (l-direction)
		float smq_len; //half median length (m-direction)
		float sigma; //source-strength


};

int num = 0;




int main(int argc, char* argv[]){
	using namespace std;
	cout << "-------------------------" << endl;
	cout << "----Booya-Panelmethod----" << endl;
	cout << "-------------------------" << endl;
	//Parse Command Line
	if (argc < 3) { // more than 4 arguments, or do nothing.
        //usage(); // usage
        //cout << "jojo,mull!";
        exit(0);
    }
    else{
    	char* inpath;
    	char* outpath;
    	int k = 1;
    	for (int i = 1; i < argc-1; i++) { //Iterate ober argv-elements
			if (string(argv[i]) == "-i") { //next->inputfile
                    inpath = argv[i + 1];
                    //cout << "JOJO" << inpath << endl;
                }
            else if (string(argv[i]) == "-out") { //next->outputfile
                    outpath = argv[i + 1];
                }
            }
        if (outpath == "") outpath = inpath; //TODO: Append or change ending

    	ifstream inputfile (inpath);


		cout << "Loading File: " << inpath << endl << endl;
		
		char thisline[max_linelength];
		//char* thisline;
		char* value;
		char* argument;
		////////////////////////////////////////////CONFIG
		while(inputfile.getline(thisline, max_linelength)){
			//cout << "laenge: " << strlen(thisline) << " zeile: " << thisline <<endl;
			if (thisline[0] == '#' || strlen(thisline) < 2)	{
				continue; //Comment
			}
			value = strtok(thisline, " ");
			argument = strtok(NULL, " ");
			config[value] = argument;

			if (string(value) == "NODES")	{
				num = atoi(argument);
				break;
			}
			}
		//////////////////////Move down
		cout << "Airspeed:  " << config["AIRSPEED"] << endl;
		cout << "Density:  " << config["DENSITY"] << endl;
		cout << "Pressure [Pa]:  " << config["PRESSURE"] << endl;
		cout << "Number of cases:  " << config["CASENUM"] << endl;
		//casenum=3 -> anglesofattack: 0 0 0; sideslip_angles: 0 0 0
		cout << "WINGSPAN: " << config["WINGSPAN"] << endl;
		cout << "SURFACE: " << config["SURFACE"] << endl;
		//cout << "NODES: " << config["NODES"] << endl;
		// ERROR, COLLDIST, FARFIELD=5, 
		//Results: coefficients, forces, geometry, velocity, pressure, center points, doublet values, source values, velocity components, mesh caracteristics, static pressure, dynamic pressure, manometer pressure (1/0)
		
		////////////////////////////////////////////NODES
		cout << "NODES: " << num << endl;

		Vector nodes[num];
		int nump = 0;

		int i = 0;
		while(inputfile.getline(thisline, max_linelength)) {
			if (thisline[0] == '#' or strlen(thisline) < 2) {
				continue;
			}


			value = strtok(thisline, " ");  //END OF NODE-SECTION
			if (string(value) == "PANELS") {
				//cout << "PANLS";
				nump = atoi(strtok(NULL, " "));
				break;
			}
			for (int j=0; j<3; j++){
				nodes[i][j] = atof(value);
				value = strtok(NULL," ");
			}
			i++;

		}
		//cout << nodes[0] << endl;
		cout << "PANELS: " << nump <<endl;
		///////////////////////////////////////////PANELS/WAKE
		// -> struct panel -> p1(int), p2, p3, p4, normvekt,
		Panel panels[nump];
		Panel* panel;
		Vector* p1;
		Vector* p2;
		Vector* p3;
		Vector* p4;

		i = 0;
		while(inputfile.getline(thisline, max_linelength)) {
			if (thisline[0] == '#' or strlen(thisline) < 2) continue;

			value = strtok(thisline, " ");

			if (string(value)=="10") panels[i].wake=true;
			else panels[i].wake=false;

			panels[i].p1 = atoi(strtok(NULL, " "));
			panels[i].p2 = atoi(strtok(NULL, " "));
			panels[i].p3 = atoi(strtok(NULL, " "));
			if (value[0] == '2') panels[i].p4 = panels[i].p3; //3-node
			else panels[i].p4 = atoi(strtok(NULL, " ")); //4-node

			panels[i].neighbour_front = atoi(strtok(NULL, " "));
			panels[i].neighbour_back = atoi(strtok(NULL, " "));

			if(!panels[i].wake){
				panels[i].neighbour_left = atoi(strtok(NULL, " "));
				if (value[0] == '2') panels[i].neighbour_right = 0;
				else panels[i].neighbour_right = atoi(strtok(NULL, " "));
			}
			///////////////////////////////////////////////////////////////////////////
			///////////////////////CALCULATE PARAMETERS////////////////////////////////
			panel = &panels[i];
			p1 = &nodes[panel->p1];
			p2 = &nodes[panel->p2];
			p3 = &nodes[panel->p3];
			p4 = &nodes[panel->p4];

			panel->n = (*p3-*p1).cross(*p4-*p2);
			panel->area = panel->n.norm();
			panel->n.normalize();
			panel->r_center = (*p1+*p2+*p3+*p4)/4;
			panel->smp = (*p2+*p3)/2 - panel->r_center;
			panel->smp_len = panel->smp.norm();
			panel->smq = (*p3+*p4)/2 - panel->r_center;
			panel->smq_len = panel->smq.norm();
			panel->m = ((*p3+*p4)/2-panel->r_center);
			panel->m.normalize();
			panel->l = panel->m.cross(panel->n);


			//cout << panel->n.norm() << endl;


			//panels[i].n = nodes[panels[i]]


			i++;
			}
			

		

cout << "joj" <<endl;


		 

		inputfile.close();






		cout << "Calculating Matrix" << endl;



		cout << "Solving System" << endl;


	}




}

void usage(){
	std::cout << "Booya-Panel-Solver\n";
	std::cout << "Usage is -in <infile> -out <outdir>\n";
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

// void* cross_3d (double *vektor1, double *vektor2){  //Return cross-product-array
// 	double temp[3];
// 	temp[0]=vektor1[1]*vektor2[2]-vektor1[2]*vektor2[1];
// 	temp[1]=-vektor1[0]*vektor2[2]+vektor1[2]*vektor2[0];
// 	temp[2]=vektor1[0]*vektor2[1]-vektor1[1]*vektor2[0];
// 	return temp;}

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

// void NearFieldCalc (double *panelliste, double *nk, double *mk, double *lk, double *mj, double pn){
// 	//
// 	//panelpoints (4 punkte), nk vekt,mk vekt,lk vekt,mj vekt3d, pn double
// 	//


// 	long i,j;

	
// 	double bjk=0.;
// 	double cjk=0.;
// 	double panelpunkte[5][3];
// 	double schleife[4];

// 	for(i=-1;i<4;i++){
// 		for(j=0;j<3;j++)
// 		panelpunkte[i+1][j]=panelliste[i==-1?9+j:3*i+j];
// 	}//panelpunkte gesetzt

// 	double s[3],a[3],b[3],h[3];
// 	double abss,am,bm,sl,sm,al,al2,pa,pb,norm_a,norm_b,norm_s,cjki,bjki,gl,dnom,rnum,side;
// 	gl=0.;
// 	int sign;

// 	//total table
// 	for(i=0;i<4;i++){
// 		/*
// 		vektor s,a,b,h
// 		double abss,am,bm,sl,sm,al,al2,pa,pb,norm_a,norm_b,norm_s,cjki,bjki,gl,dnom,rnum,side
// 		int sign
// 		*/
		
// 		setvekt(s,panelpunkte[i+1]);
// 		vektsub(s,panelpunkte[i]);

// 		abss=norm3d(s);  //panelpunkte[i+1]-panelpunkte[i] -> eigen

// 		setvekt(a,mj);
// 		vektsub(a,panelpunkte[i]);

// 		setvekt(b,a);
// 		vektsub(b,s);

// 		//alles double, alles nach if-abfrage!!
// 		am=dot_3d(a,mk);
// 		bm=dot_3d(b,mk);
// 		sl=dot_3d(s,lk);
// 		sm=dot_3d(s,mk);
// 		al=dot_3d(a,lk);
// 		al2=am*sl-al*sm;
// 		pa=pow(pn,2)*sl+al2*am;
// 		pb=pow(pn,2)*sl+al2*bm;
// 		norm_a=norm3d(a);
// 		norm_b=norm3d(b);
// 		norm_s=norm3d(s);  //WOFÜR?

// 		//vektor
// 		setvekt(h,a);
// 		cross_3d(h,s);

// 		if(compare_vectors(panelpunkte[i],panelpunkte[i+1]) || (norm3d(h)/norm3d(s) <= coresize && dot_3d(a,s) >= 0. && dot_3d(b,s) <= 0.) || norm_a<=coresize || norm_b<=coresize){
// 			cjki=0.;
// 			bjki=0.;/*case1*/
// 			schleife[i]=0;}
// 		else{
// 			gl=log((norm_a+norm_b+abss)/(norm_a+norm_b-abss))/abss;
// 			dnom=pa*pb+pow(pn,2)*norm_a*norm_b*pow(sm,2);
// 			rnum=sm*pn*(norm_b*pa-norm_a*pb);
// 			schleife[i]=1;

// 			if(sqrt(pow(pn,2))<coresize){
// 				side=dot_3d(nk,h);
// 				sign=side>0?-1.0:1.0;
// 				schleife[i]=2;
// 				if(dnom<0.0){
// 					if(pn>0.)	{cjki=pi*sign;schleife[i]=3;}
// 					else 		{cjki=-pi*s;}
// 			}}}}}