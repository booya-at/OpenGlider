//#define EIGEN_USE_MKL_ALL
#include <omp.h>
#include <iostream>  //file/terminal i/o
#include <Eigen/Core>  //matrix calculations/linalg
#include <Eigen/Geometry>
#include <Eigen/Dense>
#include <Eigen/LU>
#include <map>
#include <string>
#include <cmath>
#include <fstream>
#include <pthread.h>
#include <boost/progress.hpp>

//double pi=3.14159265358979323846;
const int max_linelength=500;
const double pi=atan(1)*4;

typedef Eigen::Vector3d Vector;
std::map<std::string, std::string> config;  //config-dictionary
float faktor = 5.;

struct Panel {
		bool wake;
		//todo: should be array
		int p1;
		int p2;
		int p3;
		int p4;

		/*int neighbour_left;
		int neighbour_right;
		int neighbour_front;
		int neighbour_back;*/
		Panel *neighbours[4];
		Vector norm_vect; //normal-vector (nk)
		//todo: should be array
		Vector tang_vect_span; // tangential-vector (wingspan)(mk)
		Vector tang_vect_chord; // tangential-vector (chordwise)(lk)

		float area; //Panel-Area
		Vector r_center;  //centerpoint

		//todo: should be array
		Vector smp; //
		Vector smq; //

		//todo: should be array
		float smp_len; //half median length (l-direction)
		float smq_len; //half median length (m-direction)

		float sigma; //source-strength

		int position; //we do have those wake panels inbetween
};

struct Config
{
	float density;
	float pressure;
	float farfield_coeff;
	int casenum;
	Vector *vinf;
	int node_number;
	int panel_number;
	int panel_number_not_wake;
};
enum NEIGHBOUR_DIRECTIONS = {NEIGHBOUR_front, NEIGHBOUR_right, NEIGHBOUR_back, NEIGHBOUR_left}
enum CONFIG_ARGUMENTS {ARG_Airspeed, ARG_Density, ARG_Pressure, ARG_Casenum, ARG_Wingspan, ARG_Mac, ARG_Sufrace, ARG_Origin, ARG_Farfield, ARG_Error, ARG_Results, ARG_Nodes, ARG_Panels};
int ARGUMENT_NUMBERS = 13;
std::string ARGUMENT_WORDS[] = {"AIRSPEED", "DENSITY", "PRESSURE", "CASE_NUM", "WINGSPAN", "MAC", "SURFACE", "ORIGIN", "FARFIELD", "ERROR", "RESULTS", "NODES", "PANELS"};

int num = 0;



void farfield_calc(const float &pn, const float &area, const float &pjk, float &lhs_coeff, float &rhs_coeff){
	lhs_coeff = pn * area / pow(pjk,3);
	rhs_coeff = area/pjk;
}
//////////////FORWARD-DECLARATIONS////////////////////////////////
void nearfield_calc(Panel*, Vector*, Vector&, float&, float&);
void *calculate_rows(void*);
void usage();
//////////////////////////////////////////////////////////////////

bool read_config(std::ifstream *inputfile, Config *config, bool &found_nodes) {
	using namespace std;
	char thisline[100];
	//string thisline;
	char *argument;
	int casenum;
	float airspeed;
	Vector *vinf;

	while(inputfile->getline(thisline, max_linelength)){
		if (thisline[0] == '#' or strlen(thisline) < 2) {
			//cout << "comment" << endl;  //comment or senseless
			continue;
		}
		//cout << "1" << endl;
		int number = -1;
		//cout << thisline << endl;
		argument = strtok(thisline, " ");
		//cout << "1.5" << endl;
		while (true) {
			number ++;
			//cout << number << "!" << endl;
			if (number >= ARGUMENT_NUMBERS) {
				cout << "Argument \""<< argument << "\"not known." << endl;
				break;
			}
			//cout << "n1" << endl;
			//cout << "n2" << endl;
			if (ARGUMENT_WORDS[number] == string(argument))
				break;
		}
		//cout << "2" <<endl;
//enum CONFIG_ARGUMENTS {ARG_Airspeed, ARG_Density, ARG_Pressure, ARG_Casenum, ARG_Wingspan, ARG_Mac, ARG_Sufrace, ARG_Origin, ARG_Farfield, ARG_Error, ARG_Results, ARG_Nodes, ARG_Panels};
		switch(number){
			case ARG_Airspeed:
				airspeed = atof(strtok(NULL, " "));
				cout << "Airspeed found: " << airspeed << endl;
				break;
			case ARG_Density:
				config->density = atof(strtok(NULL, " "));
				cout << "Density found: " << config->density << endl;
				break;
			case ARG_Pressure:
				config->pressure = atof(strtok(NULL, " "));
				cout << "Pressure found: " << config->pressure << endl;
				break;
			case ARG_Casenum:
				int casenum;
				casenum = atoi(strtok(NULL, " "));
				//cout << "casenum: " << casenum << endl;
				config->casenum = casenum;
				config->vinf = (Vector*)malloc(sizeof(Vector) * config->casenum);
				float *aoa;
				aoa = (float*)malloc(sizeof(float)*2*casenum);
				char *value;
				
				for(int j=0;j<2; j++){
					//cout << "no";
					inputfile->getline(thisline, max_linelength);
					value = strtok(thisline, " ");
					//cout << "jo";
					for(int i=0; i<casenum; i++){
						
						*(aoa + i + j*casenum) =atof(value);
						//cout << value << "/" << i+j*casenum << endl;
						value = strtok(NULL, " ");
						//cout << "ui" << endl;
					}
				}
				//cout << "p2" << endl;
				for(int i=0; i<casenum; i++){
					Vector *vect = config->vinf + i;
					//almost Spherical coordinates (aoa1[z]=90-theta, aoa2[y]=phi)
					(*vect)(0) = airspeed * cos(*(aoa + i)* pi / 180) * cos(*(aoa + i + casenum)* pi / 180);
					(*vect)(1) = airspeed * cos(*(aoa + i)* pi / 180) * sin(*(aoa + i + casenum)* pi / 180);
					(*vect)(2) = airspeed * sin(*(aoa + i)* pi / 180);					
				}
				cout << "Casenum found: " << config->casenum << endl;
				break;
			case ARG_Farfield:
				config->farfield_coeff = atof(strtok(NULL, " "));
				cout << "Farfield found: " << config->farfield_coeff << endl;
				break;
			case ARG_Nodes:
				config->node_number = atoi(strtok(NULL, " "));
				found_nodes = true;
				return true;
			case ARG_Panels:
				config->panel_number = atoi(strtok(NULL, " "));
				found_nodes = false;
				return true;
		}
		//cout << "3" << endl;
	}
	return false;
}


int main(int argc, char* argv[]){
	using namespace std;
	cout << "---------------------------------------------------------------------" << endl;
	cout << "--------------------------Booya-Panelmethod--------------------------" << endl;
	cout << "---------------------------------------------------------------------" << endl;


	float airspeed, density, pressure, farfield_coeff;
	int casenum, node_number, panel_number;
	int num_threads = 1;
	char* inpath;
    char* outpath;
    bool found_nodes = false;
	//Parse Command Line
	if (argc < 3) { // more than 2 arguments, or do nothing.
        usage(); // usage
        exit(1);
    }
    else{
    	int k = 1;
    	for (int i = 1; i < argc-1; i++) { //Iterate ober argv-elements
			if (string(argv[i]) == "-i") { //next->inputfile
                    inpath = argv[i + 1];
                    //cout << "JOJO" << inpath << endl;
                }
            else if (string(argv[i]) == "-o") { //next->outputfile
                    outpath = argv[i + 1];
                }
            else if (string(argv[i]) == "-threads"){
            	num_threads = atoi(argv[i+1]);
            }
            }
        //cout << outpath << endl;
        if (outpath == "") outpath = inpath; //TODO: Append or change ending


    	ifstream inputfile (inpath);

    	//Eigen::initParallel(); //Prevent synchronous writes
    	omp_set_num_threads(num_threads);
    	cout << "use " << num_threads << " cores" << endl;


    	char thisline[max_linelength];
    	char *value;
    	int i;
    	Vector *nodes;
    	Panel *panels;



		cout << "Loading File: " << inpath << endl << endl;
		Config config;
		while (read_config(&inputfile, &config, found_nodes)) {
			if (found_nodes) {
				////////////////////NODES SECTION//////////////////////////////
				//////////TODO: MOVE TO FUNCTION
				nodes = (Vector*)malloc(sizeof(Vector) * config.node_number);
				int i=0;
				while(inputfile.getline(thisline, max_linelength) && i < config.node_number) {
					if (thisline[0] == '#' or strlen(thisline) < 2)
						continue;

					value = strtok(thisline, " ");
					// if (string(value) == "PANELS") {
					// 	cout << "PANLS";
					// 	config.panel_number = atoi(strtok(NULL, " "));
					// 	break;
					// }
					for (int j=0; j<3; j++){
						nodes[i][j] = atof(value);
						value = strtok(NULL," ");
					}
					i++;
				}
			} else {
				////////////////////PANELS SECTION////////////////////////////
				panels = (Panel*)malloc(sizeof(Panel) * config.panel_number);
				Panel *thispanel;
				int i = 0;
				int num_not_wake = 0;
				while(inputfile.getline(thisline, max_linelength) && i<config.panel_number){
					if (thisline[0] == '#' or strlen(thisline) < 2)
						continue;

					thispanel = panels + i;
					value = strtok(thisline, " ");  //TYPE

					if (string(value)=="10") 
						thispanel->wake=true;
					else {
						thispanel->wake=false;
						thispanel->position=num_not_wake;
						num_not_wake++;
					}
					//////POINTS
					thispanel->p1 = atoi(strtok(NULL, " ")) - 1;
					thispanel->p2 = atoi(strtok(NULL, " ")) - 1;
					thispanel->p3 = atoi(strtok(NULL, " ")) - 1;
					if (value[0] == '2')
						thispanel->p4 = thispanel->p3; //3-node
					else
						thispanel->p4 = atoi(strtok(NULL, " ")) - 1; //4-node
					//////NEIGHBOURS

					for (int i = 0; i < 4; i++)
						if (i == 3 && value[0] == '2')
							//triangle
							thispanel -> neighbours[i] = NULL;
						else {
							thispanel -> neighbours[i] = panels + (atoi(strtok(NULL, " ")) - 1);
							if (thispanel->neighbours[i] == panels - 1)
								thispanel->neighbours[i] = NULL;
						}
					/*
					thispanel -> neighbours[NEIGHBOUR_front] = panels + (atoi(strtok(NULL, " ")) - 1);
					thispanel -> neighbours[NEIGHBOUR_back] = panels + (atoi(strtok(NULL, " ")) - 1);
					//thispanel->neighbour_front = atoi(strtok(NULL, " ")) - 1;
					//thispanel->neighbour_back = atoi(strtok(NULL, " ")) - 1;
					if(!thispanel->wake){
						//thispanel->neighbour_left = atoi(strtok(NULL, " ")) - 1;
						thispanel -> neighbours[NEIGHBOUR_left] = panels + (atoi(strtok(NULL, " ")) - 1);
						if (value[0] == '2') // triangle
							//thispanel->neighbour_right = thispanel->neighbour_left;
							thispanel -> neighbours[NEIGHBOUR_right] = NULL;
						else
							thispanel -> neighbours[NEIGHBOUR_right] = panels + (atoi(strtok(NULL, " ")) - 1);
							//thispanel->neighbour_right = atoi(strtok(NULL, " ")) - 1;
					}
					//if the neighbour is set to oneself (the value in the config file was zero), we set the pointer to NULL
					for (int i = 0; i < 4; i++)
						if (thispanel -> neighbours[i] == panels - 1)
							thispanel -> neighbours[i] = NULL; */
					i++;
					}
				config.panel_number_not_wake = num_not_wake;
				inputfile.close();
				break;
			}
		}


		
		int num_panels = config.panel_number;
		int num_not_wake = config.panel_number_not_wake;
		cout << "PANELS: " << num_panels;

		#pragma omp parallel
			{
			Panel* thispanel;
			Vector* p1;
			Vector* p2;
			Vector* p3;
			Vector* p4;
			#pragma omp for
			for(int i=0; i<config.panel_number; i++){
				thispanel = panels + i;
				p1 = nodes + thispanel->p1;
				p2 = nodes + thispanel->p2;
				p3 = nodes + thispanel->p3;
				p4 = nodes + thispanel->p4;

				thispanel->norm_vect = (*p3-*p1).cross(*p4-*p2);
				thispanel->area = thispanel->norm_vect.norm();
				thispanel->norm_vect.normalize();
				thispanel->r_center = (*p1+*p2+*p3+*p4)/4;
				thispanel->smp = (*p2+*p3)/2 - thispanel->r_center;
				thispanel->smp_len = thispanel->smp.norm();
				thispanel->smq = (*p3+*p4)/2 - thispanel->r_center;
				thispanel->smq_len = thispanel->smq.norm();
				thispanel->tang_vect_span = ((*p3+*p4)/2-thispanel->r_center);
				thispanel->tang_vect_span.normalize();
				thispanel->tang_vect_chord = thispanel->tang_vect_span.cross(thispanel->norm_vect);
				thispanel->sigma = thispanel->norm_vect.dot(*(config.vinf));
			}
		}
		

			
		cout << " (" << num_not_wake << ")" << endl;
		/////////////////////////////////////////////////////////////////////////
		////////////////////GENERATE MATRIX/(LHS+RHS)////////////////////////////
		Eigen::MatrixXf matrix(num_not_wake, num_not_wake);
		Eigen::VectorXf rhs(num_not_wake);
		cout << "CALCULATE MATRIX" << endl;
		//Vectors+Matrices already zeroed out
		boost::progress_display show_progress( num_panels );

		rhs.setZero();
		matrix.setZero();

		//CALCULATE PARALLELL

		//cout << "---------------------------------------------------" << endl;
		//int counter = 0;	



			int far;
			int near;

		#pragma omp parallel
			{
			Panel* panel_i;  //DECLARATION HERE! sonst, wirres zeug (wahn,...)
			Panel* panel_j;
			Vector r_diff;
			float pn, dist, cjk, bjk;
			#pragma omp for
			for (int i = 0; i<num_panels; i++){//ROWS
				//cout << "kern nr. " << omp_get_thread_num() << " (" << omp_get_num_threads() << ") erledigt panel nr. " << i << endl;
				panel_i = panels + i;
				// if (i%50 == 0){
				// cout << panel_i->position << endl;}
				//#pragma omp parallel for
				for(int j=0; j<num_panels; j++){//COLUMNS
					panel_j = panels + j;
					if (panel_j->wake)
						continue;

					r_diff = panel_j->r_center - panel_i->r_center;
					pn = r_diff.dot(panel_i->norm_vect);
					dist = r_diff.norm();
					//cout << "dist: " << dist << endl;
					

					if(dist>faktor*panel_i->smp_len*panel_i->smq_len){
						farfield_calc(pn, panel_i->area, dist, cjk, bjk);
						//cout << "far" << endl;
						far++;
					//else if(dist == 0)
					//	cjk = 2*pi;
					} else {
						nearfield_calc(panel_i, nodes, r_diff, cjk, bjk);
						//cout << "near" << endl;
						near++;
					} 
					if (panel_i->wake){ //wake -> two neighbours (CHECK SIGNS!! maybe sign(dot(normvecs))))
						//cout << panel_i->neighbour_front << "//" << panel_i->neighbour_back << endl;
						//the neighbours are out of range or are wake panels
						//matrix((panels + panel_i->neighbour_front)->position, panel_j->position)-=cjk;
						//matrix((panels + panel_i->neighbour_back)->position, panel_j->position)+=cjk;
						matrix(panel_i->neighbours[0]->position, panel_j->position) -= cjk;
						matrix(panel_i->neighbours[1]->position, panel_j->position) += cjk;
					} else if(!(panel_i->wake)) { //normal panel!
						if(panel_j->wake || panel_i->wake || panel_i->position < 0 || panel_j->position<0)
							cout << "wahn!!" << panel_j->wake << "/" << panel_i->wake << endl;
						//cout << "j: " << panel_j->position << endl;
						// if(panel_i->position > num_not_wake)
						// 	cout << "oops, i=" << panel_i->position << " / " << num_not_wake << endl;
						// if(panel_j->position > num_not_wake-10)
						// 	cout << "oops, j=" << panel_j->position << " / " << num_not_wake << endl;
						matrix(panel_i->position, panel_j->position) = cjk;
						//cout << panel->norm_vect.dot(*(config.vinf+0)) << endl;
						rhs(panel_j->position) += bjk*panel_j->norm_vect.dot(*(config.vinf+0))/4/pi;
					}
					

				}
			//progressbar
			//counter++;
			//if((counter*100)%num_panels == 0) cout << "*" << flush;
		
			++show_progress;
			}
		}


		//cout << rhs << endl;
		cout << "far: " << far << endl << "near: " << near << endl;
		cout << "area: " << panels->area << endl;
		cout << "mat: " << panels->r_center << endl;
		cout << "matrix: " << endl;
		int show = 10;
		for (int i=0;i<show;i++){
			for (int j=0; j<show;j++){
				cout << matrix(i,j) << "\t";
			}
			cout << endl;
		}

		cout << endl << "RHS:" <<endl;
		for (int i=0;i<show; i++)
			cout << rhs(i) << endl;





		cout << endl << "Solving System" << endl;
		cout << rhs(0) << endl;

		Eigen::VectorXf results(num_not_wake);
		results.setZero();
		//Eigen::LU<Eigen::MatrixXf> lumatrix(matrix);
		//lumatrix.solve(rhs, &results);
		//---->TODO:	more than one aoa
		//				keep rhs
		//				generate lu-matrix once only!
		results = matrix.lu().solve(rhs);
		cout << "SOLVED!!! :)" << endl;
		cout << results(2) << endl;

		for (int i=0; i<num_panels; i++){
			if (thispanel -> wake)
				continue;
			float gradient[4];  //sa1, sa2, sb1, sb2
			float gradient2[4]; //da1, da2, db1, db2
			float delta[2]; //delq, delp
			thispanel = panels + i;
			Panel *neighbours[4];
			/*for (int z = 0; z < 4; z++)
				if (thispanel->neighbours[z] == NULL) {
					//if it doesn't have a neighbour in one dir, go to times in the other
					int otherside = (z + 2) % 4;
					neighbours[z] = thispanel->neighbours[otherside]->neighbours[otherside]
				} else {
					neighbours[z] = thispanel->neighbours[z]
				}*/
			for (int z = 0; z < 4; z++) {
				if (thispanel->neighbours[z] == NULL) {  // no neighbour in this direction
					int z_o = (z + 2) % 4;
					gradient[z] = thispanel->smq_len + 2 * thispanel->neighbours[z_o] + thispanel->neighbours[z_o]->neighbours[z_o];
					gradient2[z] = results(thispanel->neighbours[z_o]->position)
				} else {
					gradient[z] = (z>1?-1:1) * (thispanel->smq_len + thispanel->neighbours[z]->smq_len);
					gradient2[z] = results(thispanel->neighbours[z]->position)
				}
				gradient2[z] -= results(thispanel->position)
				gradient2[z] /= gradient[z]
			}
			//delq
			delta[0] = (gradient2[0] * gradient[2] - gradient2[2] * gradient[0]) / (gradient[2] - gradient[0])
			//delp
			delta[1] = (gradient2[1] * gradient[3] - gradient2[3] * gradient[1]) / (gradient[3] - gradient[1])

			tm = ((thispanel->p3 - thispanel->p2)/2 - thispanel->r_center).dot(thispanel->mk)
			tl = ((thispanel->p3 - thispanel->p2)/2 - thispanel->r_center).dot(thispanel->lk)

			vm = -4*pi*delta[0]  //float
			vl = -4*pi*(thispanel->smp_len*delta[0]-tm*delta[1])/tl  //float
			vn = 4 * pi * thispanel->sigma  //float














		}










	}




}





void usage(){
	std::cout << "Booya-Panel-Solver\n";
	std::cout << "Usage is -in <infile> -out <outdir>\n";
}


// double norm2d (double *vektor){
// 	return(sqrt(pow(vektor[0],2)+pow(vektor[1],2)));}

// double norm3d (double *vektor){
// 	return(sqrt(pow(vektor[0],2)+pow(vektor[1],2)+pow(vektor[2],2)));}

// void normalize2d (double *vektor){
// 	double faktor = norm2d(vektor);
// 	if(faktor!=0){
// 	vektor[0]=vektor[0]/faktor;
// 	vektor[1]=vektor[1]/faktor;}}

// void normalize3d (double *vektor){
// 	double faktor = norm3d(vektor);
// 	if(faktor!=0){
// 		vektor[0]=vektor[0]/faktor;
// 		vektor[1]=vektor[1]/faktor;
// 		vektor[2]=vektor[2]/faktor;}}

// double dot_3d (double *vektor1, double *vektor2){  //return double-value of dot-product
// 	return vektor1[0]*vektor2[0]+vektor1[1]*vektor2[1]+vektor1[2]*vektor2[2];}

// // void* cross_3d (double *vektor1, double *vektor2){  //Return cross-product-array
// // 	double temp[3];
// // 	temp[0]=vektor1[1]*vektor2[2]-vektor1[2]*vektor2[1];
// // 	temp[1]=-vektor1[0]*vektor2[2]+vektor1[2]*vektor2[0];
// // 	temp[2]=vektor1[0]*vektor2[1]-vektor1[1]*vektor2[0];
// // 	return temp;}

// void vektadd (double *vektor1, double *vektor2){
// 	vektor1[0]=vektor1[0]+vektor2[0];
// 	vektor1[1]=vektor1[1]+vektor2[1];
// 	vektor1[2]=vektor1[2]+vektor2[2];
// }

// void setvekt (double *vektor1, double *vektor2){
// 	vektor1[0]=vektor2[0];
// 	vektor1[1]=vektor2[1];
// 	vektor1[2]=vektor2[2];
// }

// void vektsub (double *vektor1, double *vektor2){
// 	vektor1[0]=vektor1[0]-vektor2[0];
// 	vektor1[1]=vektor1[1]-vektor2[1];
// 	vektor1[2]=vektor1[2]-vektor2[2];
// }

// bool compare_vectors(double *vektor1, double *vektor2){
// 	if(vektor1[0]==vektor2[0] && vektor1[1]==vektor2[1] && vektor1[2]==vektor2[2]) return true;
// 	else return false;}


double coresize=0.00000000000000000001;


void nearfield_calc(Panel *panel, Vector *points, Vector &r_diff, float &lhs_coeff, float &rhs_coeff){
	//ALT:  panel,->panel(nk->norm_vect1,mk->r_center,lk->chordwise, mk->spanwise), MJ=r_center2, M=r_diff
	//mk =
	
	//panelpoints (4 punkte), nk vekt,mk vekt,lk vekt,mj vekt3d, pn double
	//double pi;
	//pi=3.14159265358979323846;
	lhs_coeff = 0.;
	rhs_coeff = 0.;

	//double *panelliste;// 9 KOOORD
	//double *nk; //panel->normvector
	//double *mk; //panel->spanwise
	//double *lk; //panel->chordwise
	//double *mj; //panel->center
	//double *mmath; //r_diff

	long i,j;

	// double pn;
	// pn=imp3d(mmath,nk);

	double norm_dist = panel->norm_vect.dot(r_diff); //pn
	double norm_dist_sq = pow(norm_dist,2);

	//double coresize=0.000001;
	//double bjk=0.; //LHS-coeff
	//double cjk=0.; //RHS-coeff
	//double panelpunkte[5][3];
	Vector *panelpunkte[5];
		panelpunkte[0] = points + panel->p4;
		panelpunkte[1] = points + panel->p3;
		panelpunkte[2] = points + panel->p2;
		panelpunkte[3] = points + panel->p1;
		panelpunkte[4] = points + panel->p4;

	//double schleife[4];

	// for(i=-1;i<4;i++){
	// 	for(j=0;j<3;j++)
	// 	panelpunkte[i+1][j]=panelliste[i<0?9+j:3*i+j];
	// }

	//double s[3],a[3],b[3],h[3]; //??
	//double abss,am,bm,sl,sm,al,al2,pa,pb,norma,normb,norms,cjki,bjki,gl,dnom,rnum,side; //??
	//gl=0.;
	int sign;

	//total table
	for(i=0;i<4;i++){
		
		//vektor s,a,b,h
		double lhs_temp, rhs_temp;
		int sign;
		
		
		//setvekt(s,panelpunkte[i+1]);
		//vektsub(s,panelpunkte[i]);
		//abss=norm3d(s);

		Vector side = (*panelpunkte[i+1] - *panelpunkte[i]); //s
		float side_len = side.norm(); //abss

		Vector diagonal_this = panel->r_center - *panelpunkte[i]; //a
		Vector diagonal_next = panel->r_center - *panelpunkte[i+1]; //b

		// setvekt(a,mj);
		// vektsub(a,panelpunkte[i]);

		// setvekt(b,a);
		// vektsub(b,s);

		//todo: spanwise vs cordwise -> array
		//alles double
		double diagonal_this_spanwise = diagonal_this.dot(panel->tang_vect_span); //am
		//am=imp3d(a,mk);
		double diagonal_next_spanwise = diagonal_next.dot(panel->tang_vect_span); //bm
		//bm=imp3d(b,mk);
		double side_chordwise = side.dot(panel->tang_vect_chord); //sl
		//sl=imp3d(s,lk);
		double side_spanwise = side.dot(panel->tang_vect_span); //sm
		//sm=imp3d(s,mk);
		double diagonal_this_chordwise = diagonal_this.dot(panel->tang_vect_span); //al
		//al=imp3d(a,lk);
		double blabla = diagonal_this_spanwise*side_chordwise - diagonal_this_chordwise*side_spanwise; //al2
		//al2=am*sl-al*sm;
		double pa = norm_dist_sq*side_chordwise+blabla*diagonal_this_spanwise;
		//pa=pow(pn,2)*sl+al2*am;
		double pb = norm_dist_sq*side_chordwise+blabla*diagonal_this_chordwise;
		//pb=pow(pn,2)*sl+al2*bm;
		double diagonal_this_len = diagonal_this.norm(); //norma
		//norma=norm3d(a);
		double diagonal_next_len = diagonal_next.norm(); //normb
		//normb=norm3d(b);
		//norms=norm3d(s);

		Vector h = diagonal_this.cross(side);

		//vektor
		// setvekt(h,a);
		// cross3d(h,s);
		if(*panelpunkte[i]==*panelpunkte[i+1] ||
			h.norm()/side.norm() <=coresize && diagonal_this.dot(side) >=0. && diagonal_next.dot(side)<=0. || 
			diagonal_this_len<=coresize ||
			diagonal_next_len<=coresize ){

			lhs_temp = 0.;
			rhs_temp = 0.;
		} else{
			double gl = log((diagonal_this_len+diagonal_next_len+side_len)/(diagonal_this_len+diagonal_next_len-side_len))/side_len;
			double dnom = pa*pb + norm_dist_sq*diagonal_this_len*diagonal_next_len*pow(side_spanwise,2);
			double rnum = side_spanwise*norm_dist*(diagonal_next_len*pa - diagonal_this_len*pb);

			//std::cout << norm_dist*(norm_dist<0?-1.:1.) << std::endl;

			if (norm_dist*(norm_dist<0?-1.:1.) < coresize){
				
				int sign = panel->norm_vect.dot(h)>0?1.:-1.;
				//std::cout << "dnom: " << dnom << std::endl;
				//std::cout << "dnorm: " << norm_dist_sq << std::endl;
				//std::cout << "pa: " << pa << std::endl;
				//std::cout << "pb: " << pb << std::endl;
				lhs_temp = (norm_dist>0?1.:-1.)*pi*sign;
				if (coresize > dnom > -coresize)
					lhs_temp /= 2;
				else if (dnom > coresize)
					lhs_temp = 0
				//else if (dnom > 0)
				//	lhs_temp = 0;
				//else
				//	lhs_temp = (norm_dist>0?1.:-1.)*pi*sign/2.;
			} else
				lhs_temp = atan2(rnum, dnom);

			rhs_temp=blabla*gl-norm_dist*lhs_temp;
		}
		lhs_coeff += lhs_temp;
		rhs_coeff += rhs_temp;
	}

		// if(vergleich(panelpunkte[i],panelpunkte[i+1])||(norm3d(h)/norm3d(s)<=coresize&&imp3d(a,s)>=0.&&imp3d(b,s)<=0.)||norma<=coresize||normb<=coresize){
		// 	cjki=0.;
		// 	bjki=0.;//case1
		// 	//schleife[i]=0;}
		// else{
		// 	gl=log((norma+normb+side_len)/(norma+normb-side_len))/side_len;
		// 	dnom=pa*pb+pow(pn,2)*norma*normb*pow(sm,2);
		// 	rnum=sm*pn*(normb*pa-norma*pb);
		// 	//schleife[i]=1;

		// 	if(sqrt(pow(pn,2))<coresize){
		// 		side=imp3d(nk,h);
		// 		sign=side>0?-1.0:1.0;
		// 		//chleife[i]=2;
		// 		if(dnom<0.0){
		// 			if(pn>0.)
		// 				cjki=pi*sign;//schleife[i]=3;
		// 			else 		
		// 				cjki=-pi*sign;//schleife[i]=4;
		// 		}
		// 		else {
		// 			if(dnom==0){
		// 				if(pn>0.) 
		// 					cjki=pi*sign/2;//schleife[i]=5;
		// 				else 
		// 					cjki=-pi*sign/2;//schleife[i]=6;
		// 			}
		// 		else
		// 			cjki=0.;//schleife[i]=7;
		// 		}
		// 	} else
		// 		cjki=atan2(rnum,dnom);//schleife[i]=cjki;

		// 	bjki=al2*gl-pn*cjki;
		// 	}


		// cjk=cjk+cjki;	//RETURN1
		// bjk=bjk+bjki;	//RETURN2
		// }


}