
# -*- coding: utf-8 -*-

from gurobipy import *

m = Model("carpooling")

# inputs

users = [["Alex",  "Oostkamp", "Gent", "flex", 5, 3],
         ["Simon", "Brugge",   "Gent", "flex", 5, 2]]

locations = ["Brugge", "Oostkamp", "Gent"]

# u ∈ U
# source(u)
# destination(u)

U = range(len(users))

source = [ locations.index(user[1]) for user in users ]

destination = [ locations.index(user[2]) for user in users ]

# wants_to_drive(u) [yes/no/flex]
# available_seats(u)
# walking_distance(u)

wants_to_drive = [ user[3] for user in users ]
available_seats = [ user[4] for user in users ]
walking_distance = [ user[5] for user in users ]

# no_driver_penalty

no_driver_penalty = 200

# i, j ∈ L
# distance(i, j)

L = range(len(locations))

distance = [[ 0, 10, 40],
            [10,  0, 30],
            [40, 30,  0]];

# route(u, i, j) ∈ {0, 1}

route = [[[ m.addVar(vtype = GRB.BINARY, name = u[0] + "_" + i + "_" + j)
            for j in locations ] for i in locations ] for u in users ]

# fan_in(u, i) = ∑ j ∈ L: route(u, j, i)
# 
# fan_out(u, i) = ∑ j ∈ L: route(u, i, j)
# 
# fan_out(u, i) - fan_in(u, i) = 1 when i = source(u)
#                              = -1 when i = destination(u)
#                              = 0 otherwise
#
# fan_in(u, i) <= 1
# 
# fan_out(u, i) <= 1

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

for u in U:
    for i in L:
        m.addConstr(fan_in[u][i] <= 1)

        m.addConstr(fan_out[u][i] <= 1)

# d, u ∈ U
# 
# driver(u) ∈ {0, 1}
# 
# driver(u) = 0 when wants_to_drive(u) = "no"
#           = 1 when wants_to_drive(u) = "yes"

driver = [ m.addVar(vtype = GRB.BINARY, name = "driver_" + u[0])
            for u in users ]

for u in U:
    if wants_to_drive[u] == "no":
        m.addConstr(driver[u] == 0)

    elif wants_to_drive[u] == "yes":
        m.addConstr(driver[u] == 1)

# drives(d, u) ∈ {0, 1}
# 
# drives(d, u) == driver(d) when d = u
#              <= driver(d) otherwise
# 
# ∑ d ∈ U: drives(d, u) <= 1
# 
# ∑ u ∈ U: drives(d, u) <= available_seats(d)

drives = [[ m.addVar(vtype = GRB.BINARY, name = d[0] + "_drives_" + u[0])
            for u in users ] for d in users ]

for d in U:
    for u in U:
        if d == u:
            m.addConstr(drives[d][u] == driver[d]);
        else:
            m.addConstr(drives[d][u] <= driver[d]);

for u in U:
    m.addConstr(sum(drives[d][u] for d in U) <= 1)

for d in U:
    m.addConstr(sum(drives[d][u] for u in U) <= available_seats[d])

# has_driver(u) = ∑ d ∈ U: drives(d, u)

has_driver = [ sum(drives[d][u] for d in U) for u in U ]

# route_as_driver(u, i, j) ∈ {0, 1}
# 
# route_as_driver(u, i, j) = 1 when route(u, i, j) and driver(u)
#                          = 0 otherwise
# 
#   route_as_driver(u, i, j) >= -1 + route(u, i, j) + driver(u)
#   
#   route_as_driver(u, i, j) <= route(u, i, j)
#   
#   route_as_driver(u, i, j) <= driver(u)

route_as_driver = [[[ m.addVar(vtype = GRB.BINARY, name = u[0] + "_" + i + "_" + j + "_as_driver")
                    for j in locations ] for i in locations ] for u in users ]

for u in U:
    for i in L:
        for j in L:
            m.addConstr(route_as_driver[u][i][j] >= -1 + route[u][i][j] + driver[u])

            m.addConstr(route_as_driver[u][i][j] <= route[u][i][j])

            m.addConstr(route_as_driver[u][i][j] <= driver[u])

# distance_by_car = ∑ u ∈ U: ∑ i ∈ L: ∑ j ∈ L: route_as_driver(u, i, j) * distance(i, j)

distance_by_car = sum(route_as_driver[u][i][j]*distance[i][j] for u in U for i in L for j in L)

# route_by_car(u, i, j) ∈ {0, 1}
# 
# route_by_car(u, i, j) = 1 when route(u, i, j) and route(d, i, j) and drives(d, u)
#                       = 0 otherwise
# 
#   route_by_car(u, i, j) >= -2 + route(u, i, j) + route(d, i, j) + drives(d, u)
# 
#   route_by_car(u, i, j) <= route(d, i, j) + (1 - drives(d, u))
# 
#   route_by_car(u, i, j) <= route(u, i, j)
# 
#   route_by_car(u, i, j) <= has_driver(u)

route_by_car = [[[ m.addVar(vtype = GRB.BINARY, name = u[0] + "_" + i + "_" + j + "_by_car")
                    for j in locations ] for i in locations ] for u in users ]

for d in U:
    for u in U:
        for i in L:
            for j in L:
                m.addConstr(route_by_car[u][i][j] >= -2 + route[u][i][j] + route[d][i][j] + drives[d][u])

                m.addConstr(route_by_car[u][i][j] <= route[d][i][j] + (1 - drives[d][u]))

for u in U:
    for i in L:
        for j in L:
            m.addConstr(route_by_car[u][i][j] <= route[u][i][j])

            m.addConstr(route_by_car[u][i][j] <= has_driver[u])

# route_by_walk(u, i, j) ∈ {0, 1}
# 
# route_by_walk(u, i, j) = route(u, i, j) - route_by_car(u, i, j)
# 
# ∑ i, j ∈ L: route_by_walk(u, i, j) * distance(i, j) <= walking_distance(u)

route_by_walk = [[[ m.addVar(vtype = GRB.BINARY, name = u[0] + "_" + i + "_" + j + "_by_walk")
                    for j in locations ] for i in locations ] for u in users ]

for u in U:
    for i in L:
        for j in L:
            m.addConstr(route_by_walk[u][i][j] == route[u][i][j] - route_by_car[u][i][j])

for u in U:
    m.addConstr(sum(route_by_walk[u][i][j] * distance[i][j] for i in L for j in L) <= walking_distance[u])

# penalty = ∑ u ∈ U: (1 - has_driver(u)) * no_driver_penalty

penalty = sum((1 - has_driver[u]) * no_driver_penalty for u in U)

# minimize(distance_by_car + penalty)

m.setObjective(distance_by_car + penalty, GRB.MINIMIZE)

m.optimize()

