from random import random
from utils import projection, ask, findEPrime, joinNetworks, generateExample
from coreClasses import Network

def FindScope(e, R ,Y , B):
  global calls
  global Target
  
  print("\n\nFind scope call ", calls)
  calls+=1

  print("R: ", [r for r in R])
  print("Y: ", [y for y in Y])

  # if(calls > 20):
  #   print("Possible Recusion Error ") # For test purpose, to be removed later
  #   return 
    
  if B.networkOfConstraintsThatRejectE(projection(e,R)).constraints != [] :
    if(ask(projection(e,R), Target)):
      #print("Here")      
      B = B.removeConstraintsThatRejectE(projection(e,R))
    else:
      #print("Here 2")
      return []

  if len(Y) == 1:
    return Y
  
  l = len(Y)

  l2 = l//2

  if l ==2 :
    Y1 = Y[:l2]
    Y2 = Y[l2:]
  else:
    Y1 = Y[:l2+1]
    Y2 = Y[l2+1:]

  
  if( B.networkOfConstraintsThatRejectE(projection( e,list(set(R).union(set(Y1))))).constraints == B.networkOfConstraintsThatRejectE(projection( e,list(set(R).union(set(Y))))).constraints ) :        
    S1 = []
  else:    
    S1 = FindScope(e, list(set(R).union(set(Y1))), Y2, B )

  if( B.networkOfConstraintsThatRejectE(projection( e,list(set(R).union(set(S1))))).constraints == B.networkOfConstraintsThatRejectE(projection( e,list(set(R).union(set(Y))))).constraints ):    
    S2 = []
  else:
    S2 = FindScope(e, list(set(R).union(set(S1))), Y1, B )
  
  return list( set(S1).union(set(S2)) )

###########################################################################################
def FindC(e,Y,L,B):
  tmp1 = B.ConstraintsIsExactlyY(Y)
  delta = joinNetworks( tmp1 , tmp1.networkOfConstraintsThatRejectE(e))

  while(True):
    ep = findEPrime(L,Y,delta)
    if ep == []:
      index = int(random()*len(delta.constraints))      
      c = delta.constraints[index]

      L = L.addConstraint(c)
      B = B.removeListOfConstraints(tmp1.constraints)
      return L,B,delta
    else:
      if(ask(ep,Target)):
        #print("Before delta = delta.removeConstraintsThatRejectE(ep): ", len(delta.constraints))
        delta = delta.removeConstraintsThatRejectE(ep)
        #print("After delta = delta.removeConstraintsThatRejectE(ep): ", len(delta.constraints))
        #print("-------------------------\n")
        #print("Before B = B.networkOfConstraintsThatRejectE(ep) ", len(B.constraints))
        B = B.networkOfConstraintsThatRejectE(ep)
        #print("After B = B.networkOfConstraintsThatRejectE(ep) ", len(B.constraints))
      else:
        S = FindScope(ep,[],Y,B)        
        if set(S).issubset(set(Y)) and set(S)!=set(Y) and S!=[]:
          FindC(ep,S,L,B)
        else:
          delta = joinNetworks(delta, delta.networkOfConstraintsThatRejectE(ep))


#############################################################################################

# main
def QuAcq2(B):
  global Target
  global vars_ids
  global vars_domains
  print("In QuAcq2: len of constraints in B is: ", len(B.constraints))
  L = Network(vars_ids,vars_domains,[])
  
  while(True):
    e = generateExample(vars_ids,L, B)
    if(e==[]):
      return True, L # convergence
    
    if(ask(e, Target)):
      B = B.removeConstraintsThatRejectE(e)
    else:
      FindC(e, FindScope(e , [] , vars_ids, B ), L, B)


  
  return L
