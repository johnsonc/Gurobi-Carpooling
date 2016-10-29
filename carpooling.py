
# -*- coding: utf-8 -*-

from gurobipy import *

m = Model("carpooling")

# inputs

users = [["Alex", "Oostkamp", "Gent"]]
locations = ["Brugge", "Oostkamp", "Gent"]

# u ∈ U
# source(u)
# destination(u)

U = range(len(users))

source = [ locations.index(user[1]) for user in users ]

destination = [ locations.index(user[2]) for user in users ]

# i, j ∈ L
# distance(i, j)

L = range(len(locations))

distance = [[ 0, 30, 40],
            [30,  0, 10],
            [40, 10,  0]];

# route(u, i, j) ∈ {0, 1}

route = [[[ m.addVar(vtype = GRB.BINARY, name = user[0] + "_" + i + "_" + j)
            for j in locations ] for i in locations ] for user in users ]

m.update()

# fan_in(u, i) = ∑ j ∈ L: route(u, j, i)
# 
# fan_out(u, i) = ∑ j ∈ L: route(u, i, j)
# 
# fan_out(u, i) - fan_in(u, i) = 1 when i = source(u)
#                              = -1 when i = destination(u)
#                              = 0 otherwise

fan_in = [[ sum(route[u][j][i] for j in L)
            for i in L ]
            for u in U ]


fan_out = [[ sum(route[u][i][j] for j in L)
            for i in L ]
            for u in U ]

for u in U:
    for i in L:
        if i == source[u]:
            m.addConstr(fan_out[u][i] - fan_in[u][i] == 1)

        elif i == destination[u]:
            m.addConstr(fan_out[u][i] - fan_in[u][i] == -1)
            
        else:
            m.addConstr(fan_out[u][i] - fan_in[u][i] == 0)

m.update()

# minimize ∑ u ∈ U: ∑ i ∈ L: ∑ j ∈ L: route(u, i, j) * distance(i, j)

m.setObjective(sum(route[u][i][j]*distance[i][j] for u in U for i in L for j in L), GRB.MINIMIZE)



