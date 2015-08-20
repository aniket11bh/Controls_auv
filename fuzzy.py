''' fuzzy.py
    --------

Implements fuzzy control in one degree of freedom.
'''


### Libraries
# Standard libraries
import numpy as np

# Third-party libraries
import skfuzzy as fuzz
import matplotlib.pyplot as plt

# Related libraries 
import pid
import visualize

class Fuzzy(pid.PID):

    """ Creates an object, to provide the pid gains corresponding to a particular error and delta_error 
        This class is compatible of receiving different type of membership function for each of the variables, and 
        receiving different no. of fuzzy_ subsets for each io variables each 
        with all possible different range.
    
        Attributes : 
            mf_types - List of type of membership function for i/o variables in fuzzy (format - string)
            f_ssets  - (Fuzzy subsets for each i/o variable) 3d list, each 2d list contains all the fuzzy subsets
                         and their range of a particular i/o variable
    """
         
    def __init__(self, mf_types, f_ssets):
        
        """
        Instance variables: 
            error , delta_e - Input variables of fuzzy control
            mf_types , f_ssets - Membership function and fuzzy subsets for each i/o variables
            io_ranges - Range of io variables i.e, error, delta_e and control_output [not values] 
        """     
        
        self.error    = 0
        self.delta_e  = 0
        self.mf_types = mf_types       
        self.f_ssets  = f_ssets     
        self.io_ranges = []    
        
    def run(self):

        """ 
        Finds appropriate value of pid gains

        NO arguments : 

        inputs : List to contain discrete values of io variables in their range (step size = 1) for plotting. i.e, x axis
            inputs[0] =  ERROR AXIS          ., so stores all possible error values
            inputs[1] =  DEL_ERROR AXIS      .,     ,,
            inputs[2] =  CONTROL_OUTPUT AXIS .,     ,,
                
        b : 3d list, each layer (i.e, 2d list) contains 1d lists of y-values (in x of step size 1) of a particular fuzzy 
            subset of a particular i/o variable 
        
        muval_de, muval_e: Stores membership value of error and delta_error for each fuzzy subsets

            ERROR                  DEL_ERROR               CONTROL_OUTPUT         m_value for crisp e and delta_e values

            b[0][0] -ve Medium  || b[1][0] -ve Medium  ||  b[2][0] -ve Medium   ..        muval[0] |  muval_d[0] 
            b[0][1] -ve small   || b[1][1] -ve small   ||  b[2][1] -ve small    ..        muval[1] |  muval_d[1]
            b[0][2] zero        || b[1][2] zero        ||  b[2][2] zero         ..        muval[2] |  muval_d[2]
            b[0][3] +ve small   || b[1][3] +ve small   ||  b[2][3] +ve small    ..        muval[3] |  muval_d[3]
            b[0][4] +ve Medium  || b[1][4] +ve Medium  ||  b[2][4] +_ve Medium  ..        muval[4] |  muval_d[4] 
            
        f_mat is a 2d matrix containing rule strengths
        """
        inputs = [ np.arange(var[0], var[1]+1, 1) for var in self.io_ranges]
        b  = []
        for i in range(3) :
                b.append( [membership_f(self.mf_types[i], inputs[i], a) for a in self.f_ssets[i] ])

        # visualize.visualize_mf(b,inputs)
        # fuzzify Error and delta error to obtain their membership values for corr. fuzzy subsets
        muval_e  = fuzzify(inputs[0], b[0], self.error)
        muval_de = fuzzify(inputs[1], b[1], self.delta_e) 

        # print 'muval_e:', muval_e
        # print 'muval_de:', muval_de
        # Obtain the rule strength matrix
        f_mat = fuzzy_matrix(muval_e, muval_de)
        #  obtian the y value clipped by output activation for output fuzzy subsets
        output = rule_base(b, f_mat)
        aggregated = np.fmax(output[0], np.fmax(output[1],np.fmax(output[2], np.fmax(output[3], output[4]))))
        out_final  = fuzz.defuzz(inputs[2], aggregated, 'centroid')
        print "output:",out_final
        # plotting final output
        visualize.visualize_output(b, inputs, output, out_final, aggregated)
        plt.show()

def membership_f(mf, x, abc = [0,0,0], a = 1, b = 2, c = 3, d = 4, abcd = [0,0,0,0]):
    """
    Returns y values corresponding to type of type of Membership fn.
    arguments:
        mf - string containing type of Membership function
        x  - x axis values
        abc - list containing triangular edge point x-values
    """
    return {
        'trimf'   : fuzz.trimf(x, abc),                                 # trimf(x, abc)
        'dsigmf'  : fuzz.dsigmf(x, a, b, c, d),                         # dsigmf(x, b1, c1, b2, c2)
        'gauss2mf': fuzz.gauss2mf(x, a, b, c, d),                       # gauss2mf(x, mean1, sigma1, mean2, sigma2)
        'gaussmf' : fuzz.gaussmf(x, a, b),                              # gaussmf(x, mean, sigma)
        'gbellmf' : fuzz.gbellmf(x, a, b, c),                           # gbellmf(x, a, b, c)
        'piecemf' : fuzz.piecemf(x, abc),                               # piecemf(x, abc)
        'pimf'    : fuzz.pimf(x, a, b, c, d),                           # pimf(x, a, b, c, d)
        'psigmf'  : fuzz.psigmf(x, a, b, c, d),                         # psigmf(x, b1, c1, b2, c2)
        'sigmf'   : fuzz.sigmf(x, a, b),                                # sigmf(x, b, c)
        'smf'     : fuzz.smf(x, a, b),                                  # smf(x, a, b)
        'trapmf'  : fuzz.trapmf(x, abcd),                               # trapmf(x, abcd)
        'zmf'     : fuzz.zmf(x, a, b),                                  # zmf(x, a, b)
            }[mf]

def fuzzify(Input, y, crisp_val):
    """
    Fuzzifies crisp value to obtain their membership values for corr. fuzzy subsets.
    arguments:
        Input - Range of crisp_val i.e, list of x values discrete values which crisp_val can take
        y     - 2d list containing y values of each fuzzy subsets of an i/o variable
        crisp_val - value to be fuzzified
    """
    f = [fuzz.interp_membership(Input, fuzzy_sset_y, crisp_val) for fuzzy_sset_y in y ]
    return f

def fuzzy_matrix(muval_e, muval_de): 
    """
    Returns 2d array of rule strengths
    arguments:
        muval_e, muval_de - 1d list of membership values to their corresponding fuzzy subsets
    """
    return np.array([ [min(a,b) for a in muval_e] for b in muval_de])

#b= y-values of trimf corresponding to each input and output variables in range var.ranges[]
def rule_base(b, f_mat):
    """
    Returns y values of output by clipping by an amount of output activations for output fuzzy subsets
    arguments:
    f_mat - rule_strength matrix
    b     - b[2] , y values of output fuzzy subsets

E / DEL_E|         NM      ||       NS        ||        Z         ||       PS        ||       PM         
----------------------------------------------------------------------------------------------------------
    NM   | f_mat[0][0] NM  || f_mat[0][1] NM  ||  f_mat[0][2] NS  || f_mat[0][3] Z   || f_mat[0][4] PS   
    NS   | f_mat[1][0] NM  || f_mat[1][1] NM  ||  f_mat[1][2] NS  || f_mat[1][3] PS  || f_mat[1][4] PM  
    Z    | f_mat[2][0] NM  || f_mat[2][1] NS  ||  f_mat[2][2] Z   || f_mat[2][3] PS  || f_mat[2][4] PM         
    PS   | f_mat[3][0] NM  || f_mat[3][1] NS  ||  f_mat[3][2] PS  || f_mat[3][3] PM  || f_mat[3][4] PM   
    PM   | f_mat[4][0] NS  || f_mat[4][1] Z   ||  f_mat[4][2] PS  || f_mat[4][3] PM  || f_mat[4][4] PM

    """
    NM = max(f_mat[0][0], f_mat[0][1], f_mat[1][0], f_mat[1][1], f_mat[2][0], f_mat[3][0])
    b[2][0] = np.fmin(NM,b[2][0])
    NS = max(f_mat[0][2], f_mat[1][2], f_mat[2][1], f_mat[3][1], f_mat[4][0])
    b[2][1] = np.fmin(NS, b[2][1])
    Z  = max(f_mat[0][3], f_mat[2][2], f_mat[4][1])
    b[2][2] = np.fmin(Z, b[2][2])
    PS = max(f_mat[0][4], f_mat[1][3], f_mat[2][3], f_mat[3][2], f_mat[4][2])
    b[2][3] = np.fmin(PS, b[2][3])
    PM = max(f_mat[1][4], f_mat[2][4], f_mat[3][4], f_mat[3][3], f_mat[4][3], f_mat[4][4])
    b[2][4] = np.fmin(PM, b[2][4])

    return b[2]