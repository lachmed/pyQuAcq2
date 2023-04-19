from coreClasses import Network, Conjunction, Constraint

############################################################
def projection(e,vars_ids):
  # this is a projection of Vars on assignement: return the part of the assignement 
  # including only Vars
  
  ids = [ee[0] for ee in e]
  els = { ee[0]: ee for ee in e}
  p = []
  
  # for id,name,val in e :
  #   if(id in vars_ids):
  #     p.append((id,name,val))

  for id in vars_ids:
    if id in ids:
      p.append(els[id])
  
  return p

##############################################################
from ortools.sat.python import cp_model
from constants import VariableNames
# This was borrowed from ortools official documentation, it catches all the solutions
class VarArraySolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, variables):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__variables = variables
        self.__solution_count = 0
        self.__solutions = []

    def on_solution_callback(self):
        self.__solution_count += 1
        
        e = []
        self.__solution_count+=1
        for v in self.__variables.keys():
          e.append(
              (v, VariableNames[v], self.Value(self.__variables[v]))
          )            
        #print(f"Solution {self.__solution_count}: ",e)
        
        self.__solutions.append(e)

    def solution_count(self):
        return self.__solution_count

    def allSolutions(self):
      return self.__solutions


################################################################

def ask(e, Target):
  
  if set([ee[0] for ee in e]) == set(Target.vars_ids):
    # This is a membership query
    if e in Target.getAllSolutions():
      print("a membership query was sent, the answer was YES")
      return True
    else:
      print("a membership query was sent, the answer was NO")
      return False
    
  else:
    # This is a partial query
    if Target.isAccepted(e):
      print("a partial query was sent, the answer was YES")
      return True
    else:
      print("a partial query was sent, the answer was NO")
      return False

####################################################################

from random import random
from copy import deepcopy

def generateExample(X,L,B):
  # We generate an assignenemt from the solution of L that doesn't verify all constraints in B
  C = deepcopy(L)

  sols = C.getAllSolutions()

  for s in sols:
    if not B.isAccepted(s):
      return projection(s,X)
  
  return []

####################################################################

def areIncompatible(c1,c2):
  # TODO: test if two constraints are incompatible
  # for now it doesn't cause a problem, but if you find an error later this may be the cause
  pass


def joinConstraints(listOfConstraints):   
  return Conjunction(listOfConstraints)

def joinNetworks(N1,N2):

  res = []

  
  for nc2 in N2.constraints:
    res.append(nc2)
  

  for nc1 in N1.constraints:
    for nc2 in N2.constraints:
    #TODO: if( nc1 and nc2 != False) if not areIncompatible(nc1,nc2)
      if(nc1 != nc2):
        res.append(joinConstraints([nc1,nc2]))
  
  return Network(N1.vars_ids,N1.var_domains,res)

####################################################################

def findEPrime(L,Y,delta):

  sol = L.ConstraintsIncludedInY(Y).getAllSolutions()
  
  for s in sol:
    if(len(delta.constraints)>=1):
      if( delta.networkOfConstraintsThatRejectE(s).constraints!=[] 
         and set(delta.networkOfConstraintsThatRejectE(s).constraints).issubset(set(delta.constraints))
         and len(delta.networkOfConstraintsThatRejectE(s).constraints)!= len(delta.constraints)
          ):
        return s
  return []

####################################################################

####################################################################