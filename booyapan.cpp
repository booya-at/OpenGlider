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

//double pi=3.14159265358979323846;
const int max_linelength=500;
const double pi=atan(1)*4;

typedef Eigen::Vector3d Vector;
std::map<std::string, std::string> config;  //config-dictionary
float faktor = 5.;

struct Panel {
		bool wake;
		int p1;
		int p2;
		int p3;
		int p4;
		int neighbour_left;
		int neighbour_right;
		int neighbour_front;
		int neighbour_back;
		Vector norm_vect; //normal-vector
		Vector tang_vect_span; // tangential-vector (wingspan)
		Vector tang_vect_chord; // tangential-vector (chordwise)
		float area; //Panel-Area
		Vector r_center;  //centerpoint

		Vector smp;
		Vector smq;

		float smp_len; //half median length (l-direction)
		float smq_len; //half median length (m-direction)
		float sigma; //source-strength

		int position; //we do have those wake panels inbetween
};

int num = 0;


struct thread_data //Shared data
{
	int num_threads;
	int thread_no;
	int num_panels; //len(panels+wake_panels)
	Panel *panels;
	Vector *points;
	Eigen::MatrixXf *matrix;
	Eigen::VectorXf *rhs;
};




void farfield_calc(const float &pn, const float &area, const float &pjk, float &lhs_coeff, float &rhs_coeff){
	lhs_coeff = pn * area / pow(pjk,3);
	rhs_coeff = area/pjk;
}
//////////////FORWARD-DECLARATIONS////////////////////////////////
void nearfield_calc(Panel*, Vector*, Vector*, float&, float&);
void *calculate_rows(void*);
void usage();
//////////////////////////////////////////////////////////////////


int main(int argc, char* argv[]){

	using namespace std;
	cout << "---------------------------------------------------------------------" << endl;
	cout << "--------------------------Booya-Panelmethod--------------------------" << endl;
	cout << "---------------------------------------------------------------------" << endl;



	int num_threads = 1;
	char* inpath;
    char* outpath;

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
        if (outpath == "") outpath = inpath; //TODO: Append or change ending

    	ifstream inputfile (inpath);

    	Eigen::initParallel(); //Prevent synchronous writes
    	Eigen::setNbThreads(num_threads);


		cout << "Loading File: " << inpath << endl << endl;
		
		char thisline[max_linelength];
		char* value;
		char* argument;
		////////////////////////////////////////////CONFIG TODO: PARSE DIRECTLY!!
		while(inputfile.getline(thisline, max_linelength)){
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
		int num_panels = 0;

		int i = 0;
		while(inputfile.getline(thisline, max_linelength)) {
			if (thisline[0] == '#' or strlen(thisline) < 2) {
				//cout << "comment" << endl;
				continue;
			}


			value = strtok(thisline, " ");  //END OF NODE-SECTION
			if (string(value) == "PANELS") {
				//cout << "PANLS";
				num_panels = atoi(strtok(NULL, " "));
				break;
			}
			for (int j=0; j<3; j++){
				nodes[i][j] = atof(value);
				value = strtok(NULL," ");
			}
			i++;

		}
		//cout << nodes[0] << endl;
		cout << "PANELS: " << num_panels;
		///////////////////////////////////////////PANELS/WAKE
		// -> struct panel -> p1(int), p2, p3, p4, normvekt,
		Panel panels[num_panels];
		//local references
		Panel* panel;
		Vector* p1;
		Vector* p2;
		Vector* p3;
		Vector* p4;

		i = 0;
		int num_not_wake = 0;
		while(inputfile.getline(thisline, max_linelength)) {
			if (thisline[0] == '#' or strlen(thisline) < 2) {
				continue;
			}
			panel = panels + i;
			i++;
			value = strtok(thisline, " ");

			if (string(value)=="10") {
				panel->wake=true;
			}
			else {
				panel->wake=false;
				panel->position=num_not_wake;
				num_not_wake++;
			}
			panel->p1 = atoi(strtok(NULL, " "));
			panel->p2 = atoi(strtok(NULL, " "));
			panel->p3 = atoi(strtok(NULL, " "));
			if (value[0] == '2')
				panel->p4 = panel->p3; //3-node
			else
				panel->p4 = atoi(strtok(NULL, " ")); //4-node

			panel->neighbour_front = atoi(strtok(NULL, " "));
			panel->neighbour_back = atoi(strtok(NULL, " "));

			if(!panel->wake){
				panel->neighbour_left = atoi(strtok(NULL, " "));
				if (value[0] == '2')
					panel->neighbour_right = panel->neighbour_left;
				else
					panel->neighbour_right = atoi(strtok(NULL, " "));
			}
			///////////////////////////////////////////////////////////////////////////
			///////////////////////CALCULATE PARAMETERS////////////////////////////////
			//Could be multithreaded aswell?
			//subtract one because the pointnrs. start at 1
			p1 = nodes + panel->p1 -1;
			p2 = nodes + panel->p2 -1;
			p3 = nodes + panel->p3 -1;
			p4 = nodes + panel->p4 -1;

			panel->norm_vect = (*p3-*p1).cross(*p4-*p2);
			panel->area = panel->norm_vect.norm();
			panel->norm_vect.normalize();
			panel->r_center = (*p1+*p2+*p3+*p4)/4;
			panel->smp = (*p2+*p3)/2 - panel->r_center;
			panel->smp_len = panel->smp.norm();
			panel->smq = (*p3+*p4)/2 - panel->r_center;
			panel->smq_len = panel->smq.norm();
			panel->tang_vect_span = ((*p3+*p4)/2-panel->r_center);
			panel->tang_vect_span.normalize();
			panel->tang_vect_chord = panel->tang_vect_span.cross(panel->norm_vect);

		}
		inputfile.close();

			
		cout << " (" << num_not_wake << ")" << endl;
		/////////////////////////////////////////////////////////////////////////
		////////////////////GENERATE MATRIX/(LHS+RHS)////////////////////////////
		Eigen::MatrixXf matrix(num_not_wake, num_not_wake);
		Eigen::VectorXf rhs(num_not_wake);
		cout << "CALCULATE MATRIX" << endl;
		//Vectors+Matrices already zeroed out

		//CALCULATE PARALLELL	
		int thread_status[num_threads];
		pthread_t threads[num_threads];
		thread_data data[num_threads];

		for (int thread_no = 0; thread_no<num_threads; thread_no++){
			//FILL Thread-data-struct
			data[thread_no].num_threads = num_threads;
			data[thread_no].panels = panels;
			data[thread_no].points = nodes;
			data[thread_no].num_panels = num_panels;
			data[thread_no].thread_no = thread_no;
			data[thread_no].matrix = &matrix;
			data[thread_no].rhs = &rhs;
			//START THREAD
			thread_status[thread_no] = pthread_create(&threads[thread_no], NULL, 
                          calculate_rows,
                          (void *)&data[thread_no]);
      		if (thread_status[thread_no]){
         		cout << "Error:unable to create thread," << thread_status[thread_no] << endl;
         		exit(-1);
      			}
		}

		//WAIT FOR ALL THREADS TO FINISH (END OF CALCULATION)
		for (int thread_no=0; thread_no<num_threads; thread_no++){
			pthread_join(threads[thread_no], NULL);
			cout << "core no. " << thread_no << "exited with code: " << thread_status[thread_no] << endl;
		}
		cout << "Solving System" << endl;

		Eigen::VectorXf results(num_not_wake);
		//Eigen::LU<Eigen::MatrixXf> lumatrix(matrix);
		//lumatrix.solve(rhs, &results);
		matrix.lu().solve(rhs, &results);
		cout << results[0] << endl;

	}




}



void *calculate_rows(void *thread_arg){
	using namespace std;
	struct thread_data *data;
	data = (struct thread_data *) thread_arg;
	usleep(data->thread_no*20000);
	cout << "core_no: " << data->thread_no << " started" << endl;

	
	//sleep(500);
	Panel* panel_i;
	Panel* panel_j;
	Vector r_diff;
	float pn, dist, cjk, bjk;
	for (int i = data->thread_no; i<data->num_panels; i+=data->num_threads){//ROWSdata->
		panel_i = data->panels + i;
		// if (i%50 == 0){
		// cout << panel_i->position << endl;}
		for(int j=0; j<data->num_panels; j++){//COLUMNS
			panel_j = data->panels + j;
			if (panel_j->wake)
				continue;

			r_diff = panel_j->r_center - panel_i->r_center;
			pn = r_diff.dot(panel_i->norm_vect);
			dist = r_diff.norm();

			if(dist>faktor*panel_i->smp_len*panel_i->smq_len){
				farfield_calc(pn, panel_i->area, dist, cjk, bjk);
				}
			else {
				nearfield_calc(panel_i, data->points, &(panel_j->r_center), cjk, bjk);
				}

			if (panel_i->wake){ //wake -> two neighbours (CHECK SIGNS!! maybe sign(dot(normvecs))))
				//cout << panel_i->neighbour_front << "//" << panel_i->neighbour_back << endl;
				//the neighbours are out of range or are wake panels
				if (panel_i->neighbour_front < 1 || panel_i->neighbour_front > data->num_panels || (data->panels + panel_i->neighbour_front - 1)->wake)
					cout << "Error in panel " << i << ": neighbour front not right!" << endl;
				if (panel_i->neighbour_back < 1 || panel_i->neighbour_back > data->num_panels || (data->panels + panel_i->neighbour_back - 1)->wake)
					cout << "Error in panel " << i << ": neighbour back not right!" << endl;
				(*data->matrix)((data->panels + panel_i->neighbour_front -1)->position, panel_j->position)+=cjk;
				(*data->matrix)((data->panels + panel_i->neighbour_back -1)->position, panel_j->position)-=cjk;
				}
			else{ //normal panel!
				(*data->matrix)(panel_i->position, panel_j->position) = cjk;
				(*data->rhs)(panel_j->position) += bjk;
				}
			

			}
	
			
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


void nearfield_calc(Panel *panel, Vector *points, Vector *r_diff, float &lhs_coeff, float &rhs_coeff){
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

	double norm_dist = panel->norm_vect.dot(*r_diff); //pn
	double norm_dist_sq = pow(norm_dist,2);

	double coresize=0.00000000000000000001;
	//double bjk=0.; //LHS-coeff
	//double cjk=0.; //RHS-coeff
	//double panelpunkte[5][3];
	Vector *panelpunkte[5];
		panelpunkte[0] = points + panel->p1;
		panelpunkte[1] = points + panel->p2;
		panelpunkte[2] = points + panel->p3;
		panelpunkte[3] = points + panel->p4;
		panelpunkte[4] = points + panel->p1;

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

			if (norm_dist*(norm_dist<0?-1.:1.) < coresize){
				int sign = panel->norm_vect.dot(h)>0?1.:-1.;
				if (dnom<0.)
					lhs_temp = (norm_dist>0?1.:-1.)*pi*sign;
				else if (dnom == 0.)
					lhs_temp = (norm_dist>0?1.:-1.)*pi*sign/2.;
				else
					lhs_temp = 0.;
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