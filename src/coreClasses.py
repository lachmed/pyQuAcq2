import operator 
from ortools.sat.python import cp_model
from itertools import permutations
from utils import projection, VarArraySolutionPrinter


class Constraint:
    # this class represents a constraint
    def __init__(self, scope_ids, rel, arity):      
      
      assert isinstance(scope_ids,list), "The scope must be a list of variable ids"      
      for x in scope_ids:
        assert isinstance(x,int), "The scope must be a list of variable ids" 
      
      self.scope_ids = scope_ids
      
      #The relation must be an operator
      assert callable(rel), "The relation must be an operator"
      self.rel = rel

      # the arity is the number of variables in the scope, an arity could be binary, ternary ...
      self.arity = arity
    def verify(self, assignement):      
      
      # this method checks whether the constraint accepts an assignement (True) or rejects it (False)
      
      # we project the assignement on the scope of the constraint
      p = projection(assignement, self.scope_ids)
      

      values = [pp[2] for pp in p]
      
      
      if(len(values) != self.arity): 
        # if the number of the values is different from the arity then just return True because
        # the constraint is not concerned, in general it is unlikely get here because we do the projection
        # but to avoid errors we keep it here
        return True

      return self.rel(*values) # we check if the relation accepts the values given to the variables

###############################################

class Conjunction():

  def __init__(self, constraints):
    # a conjunction is the AND of constraints
    self.scope_ids = [c.scope_ids for c in constraints]
    self.rel = [c.rel for c in constraints]
    self.constraints = constraints
    
  def verify(self, assignement,liste = []):
    # for a conjunction to accept an assignement, all constraints from which 
    # it is built must accept it (i.e there is an AND between these constraints )
    for c in self.constraints:
      if(isinstance(c,Constraint)):
        liste.append(c.verify(assignement))
      else: # if we get here, then c is itself a conjunction, so we recursevly call the method
        c.verify(assignement,liste)
        
    return all(liste) # if only one constraint doesn't accept the assignement this returns False. It returns True otherwise
  
  def prepareCpModelConstraint(self, vars_dict, model):
    
    # This method adds the constraints in this conjunction to the ortools model

    for scope, rel, c in zip(self.scope_ids, self.rel, self.constraints):      
      if(isinstance(scope, list) and all([isinstance(s,int) for s in scope])): # This is a constraints
        tmp1 = []
        sss = []
        for s in scope:
          tmp1.append(vars_dict[s])
          sss.append(s)
        
        model.Add(rel(*tmp1))  # add the constraint to the model specifying the variables
      else: # this is a conjunction of constraints, so recusively call the method
        c.prepareCpModelConstraint(vars_dict, model)
      
  def isScopeIncludedInY(self,Y, liste = []):
  # this method verifies if the scope is included in Y
  # the scope of a conjunction is all the variables in the scopes of the constraints from which it is built  
    for c in self.constraints:      
      if(isinstance(c, Constraint)): # This is a constraint        
        if set(c.scope_ids).issubset(set(Y)):
          liste.append(True)                    
      else: # this is a conjunction of constraints
        c.isScopeIncludedInY(Y,liste)
                  
    return all(liste)
  

  def isScopeIsExactlyY(self,Y, liste = []):

    # this method verifies if the scope is Exactly Y

    for c in self.constraints:      
      if(isinstance(c, Constraint)): # This is a constraint
        if set(c.scope_ids) == set(Y) :
          liste.append(True)        
      else: # this is a conjunction of constraints
        c.isScopeIsExactlyY(Y,liste)  
    
    return all(liste)
  
  #########################################################

class Network():

  def __init__(self, vars_ids, var_domains ,constraints):
    self.vars_ids = vars_ids
    self.var_domains = var_domains # domains are like this : (start , end)
    self.constraints = constraints
    self.all_solutions = None

  def isAccepted(self, e):
    # An assignement e is accepted by a network if it doesn't violate any constraints of the network
    return all( [c.verify(e) for c in self.constraints] )
  

  def isSolution(self,e):
    # e is a solution if it is complete and accepted
    ids = [ee[0] for ee in e]
    return self.isAccepted(e) and set(ids) == set(self.vars_ids)
  
  def ConstraintsIncludedInY(self,Y):
    # This method constructs a network from the constraints
    # that have scope included in Y
    res = []

    for c in self.constraints:
      if(isinstance(c,Constraint)):
        if set(c.scope_ids).issubset(set(Y)):
          res.append(c)
      else:
        if(c.isScopeIncludedInY(Y)):
          res.append(c)
    
    doms = []
    for var,dom in zip(self.vars_ids, self.var_domains):
      for y in Y:
        if y == var:
          doms.append(dom)

    return Network(Y,doms,res)

  def ConstraintsIsExactlyY(self,Y):
    # This method constructs a network from the constraints
    # that have scope is Exactly Y
    res = []

    for c in self.constraints:
      if(isinstance(c,Constraint)):
        if set(c.scope_ids) == set(Y) :
          res.append(c)
      else:
        if(c.isScopeIsExactlyY(Y)):
          res.append(c)
    
    doms = []
    for var,dom in zip(self.vars_ids, self.var_domains):
      for y in Y:
        if y == var:
          doms.append(dom)


    return Network(Y,doms,res)
  
  def solve(self):

    # Solving Using ortools, just one solution.
    

    model = cp_model.CpModel()    
    vars = { id: model.NewIntVar(dom[0], dom[1] , str(id) )  for id,dom in zip(self.vars_ids, self.var_domains) }
    
    for c in self.constraints:
      tmp = []
      if(isinstance(c,Constraint)):
        for  i in c.scope_ids:
          tmp.append(vars[i])
        
        model.Add(c.rel(*tmp))

      elif(isinstance(c,Conjunction)):
        c.prepareCpModelConstraint(vars,model)  
    
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
      e = []
      for v in vars.keys():
        e.append(
            (v, "X"+str(v), solver.Value(vars[v]))
        )
      return e 
    else:
      print('No solution found.')
      return []

  def allSolutions(self):
    # Here, We search for all solutions using ortools solver.
    model = cp_model.CpModel()    
    vars = { id: model.NewIntVar(dom[0], dom[1] , str(id) )  for id,dom in zip(self.vars_ids, self.var_domains) }
    
    for c in self.constraints:
      tmp = []
      if(isinstance(c,Constraint)):
        for  i in c.scope_ids:
          tmp.append(vars[i])
        
        model.Add(c.rel(*tmp))

      elif(isinstance(c,Conjunction)):
        c.prepareCpModelConstraint(vars,model)                
        
        
          

    solver = cp_model.CpSolver()
    sols = []
    solution_printer = VarArraySolutionPrinter(vars)
    
    # Enumerate all solutions.
    solver.parameters.enumerate_all_solutions = True
    
    # Solve.
    
    status = solver.Solve(model, solution_printer)    
    
    self.all_solutions = solution_printer.allSolutions()
    #return solution_printer.allSolutions()
  
  def getAllSolutions(self):
    # this is the function which will be used in other places.
    self.allSolutions()

    return self.all_solutions
    #return self.allSolutions()


  def isEquivalentTo(self, N):
    # If the sets of solutions of two networks T and T2 are equal, then these two networks are equivalent
    selfsols = self.getAllSolutions()
    nsols  = N.getAllSolutions()
    for solution in selfsols:
      if solution not in nsols:
        return False
      
    return True

  
  def networkOfConstraintsThatRejectE(self,e):
    # Here we construct a network containing constraints that reject e
    tmp = []
    
    for c in self.constraints:
      if not c.verify(e):
        tmp.append(c)
    
    return Network(self.vars_ids, self.var_domains, tmp)
  
  def removeConstraintsThatRejectE(self,e):
    # we remove the constraints that reject e from the current network
    tmp = []    
    
    for c in self.constraints:
      if c.verify(e):        
        tmp.append(c)

    self.constraints = tmp
    return self
  
  def addConstraint(self,c):
    # we add  the constraint c to the network
    self.constraints.append(c)
    return self

  def removeListOfConstraints(self, l):
    # we remove a list l of constraints from the current network
    tmp = []
    for c in self.constraints:
      if(c not in l):
        tmp.append(c)
    
    self.constraints = tmp
    return self
    

      
#language = [(rel,arity)]

class Basis(Network):
  # A Basis is also a network, but it's constraints are built from a language 
  def __init__(self, vars_ids, var_domains, language):
    super().__init__(vars_ids, var_domains,[])
    self.language = language

  def build(self):    
    # we build the set of constraints using permutations of variables of length == arity of relation (operator)
    for l in self.language:
      for p in permutations(self.vars_ids,l[1]):
        self.constraints.append(Constraint(list(p),l[0],l[1]))
