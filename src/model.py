import pandas as pd
from typing import List
import math

class ProblemModel:
    def __init__(self, nodes, units, wind_speed):
        self.nodes: List[Node] = nodes
        self.units: List[SurveillanceUnit] = units
        self.wind_speed = wind_speed

    def from_excel(excelPath):
        xls = pd.ExcelFile(excelPath)
        node_df = pd.read_excel(xls, 'Nodes')
        unit_df = pd.read_excel(xls, 'Units')
        parameters_df = pd.read_excel(xls, 'Parameters')
        nodes = []
        units = []
        for index, row in node_df.iterrows():
            node = Node(row['id'], row['x_coord'], row['y_coord'], (row['risk_status']), row['is_buildable'], \
            row['forest_rate'], row['slope'], row['ymn'])
            nodes.append(node)
        for index, row in unit_df.iterrows():
            unit = SurveillanceUnit(row['observer_type'], row['inventory'], row['cost'], row['min_vision'], row['max_vision'])
            units.append(unit)
        wind_speed = 30
        for index, row in parameters_df.iterrows():
            if row['parameter'] == 'wind_speed':
                wind_speed = row['value']

        return ProblemModel(nodes, units, wind_speed)

    def covering_rate(self, source_node, target_node, surveillance_type):
        if type(source_node) is int:
            source_node = self.nodes[source_node]
        if type(target_node) is int:
            target_node = self.nodes[target_node]
        if type(surveillance_type) is int:
            surveillance_type: SurveillanceUnit = self.units[surveillance_type]
        distance = source_node.dist_to(target_node)
        if distance < surveillance_type.min_vision:
            return 1.0
        if distance > surveillance_type.max_vision:
            return 0.0
        return 1 - (distance-surveillance_type.min_vision)/(surveillance_type.max_vision-surveillance_type.min_vision)
        



class Node:
    def __init__(self, id, x_coord, y_coord, risk_status, is_buildable, forest_rate, slope, ymn):
        self.id = id-1
        self.x_coord = x_coord
        self.y_coord = y_coord
        self.risk_status = risk_status
        self.is_buildable = is_buildable
        self.forest_rate = forest_rate
        self.slope = slope
        self.ymn = ymn
        self.slope_coeff = math.e**(0.03*self.slope)
        self.ymn_coeff = 5.75*(math.e**(-0.13*self.ymn))
            
    def dist_to(self, other_node):
        return ((self.x_coord - other_node.x_coord)**2 + (self.y_coord-other_node.y_coord)**2)**(1/2)

class SurveillanceUnit:
    def __init__(self, name, inventory, cost, min_vision, max_vision):
        self.name = name
        self.inventory = inventory
        self.cost = cost
        self.min_vision = min_vision
        self.max_vision = max_vision