#!/usr/bin/env python3
# Copyright (C) 2018 Stefan Großhauser
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from boxes import *

class ConsoleEnclosureCase(Boxes):
    """console enclosure case, for a PC power supply, supports bedbolts, flex joints and arbitrary holes."""

    webinterface = True

    ui_group = "Box"

    SHARP_CORNERS = "sharp corners"
    FLEX_CORNERS = "flex corners"

    TOP_EDGE_FINGER = "finger edge"
    TOP_EDGE_STRAIGHT_BOLTS = "straight edge with bolts"
    
    def __init__(self):
        Boxes.__init__(self)

        self.addSettingsArgs(edges.FingerJointSettings)
        self.addSettingsArgs(edges.FlexSettings)
        self.buildArgParser()
        self.argparser.add_argument(
                    "--width", action="store", type=float, default=87,
                    help="inner width in mm")
        self.argparser.add_argument(
                    "--depth", action="store", type=float, default=210,
                    help="inner depth in mm")
        self.argparser.add_argument(
                    "--height", action="store", type=float, default=210,
                    help="inner height in mm")

        self.argparser.add_argument(
            "--angle",  action="store", type=float, default=50.0,
            help="the angle at the upper kink, between horizon and panel  (in degrees)")

        self.argparser.add_argument(
            "--middle_angle",  action="store", type=float, default=0.0,
            help="the angle at the middle kink, between the two panel parts (in degrees). Using the value of the other angle parameter (above), try e.g. 180-angle+15")

        top_edge_types = [self.TOP_EDGE_FINGER, self.TOP_EDGE_STRAIGHT_BOLTS]
        self.argparser.add_argument(
            "--top_edge",  action="store", type=str, default=top_edge_types[0],
            choices=top_edge_types,
            help="")

        self.argparser.add_argument(
            "--top_sidelength",  action="store", type=float, default=50.0,
            help="inner side length of the top part in mm. This is only relevant if middle_angle is nonzero")
        
        corner_types = [self.SHARP_CORNERS, self.FLEX_CORNERS]
        self.argparser.add_argument(
            "--style",  action="store", type=str, default=corner_types[-1],
            choices=corner_types,
            help="choose between "+",".join(corner_types))

        self.argparser.add_argument(
            "--front_height",  action="store", type=float, default=100.0,
            help="inner height of the front wall in mm")
        #
        self.argparser.add_argument(
            "--bedbolts_number",  action="store", type=str, default="(1)",
            help="the number of bedbolts. For %s, this is just one integer. For %s this is a tuple of integers (front, panels,..., top). If middle angle is zero, this should have 3 elements, otherwise 4. If there are too few elements, the last value will be repeated." % (self.SHARP_CORNERS, self. FLEX_CORNERS))

        m3_22mm_screw_settings = (3,5.5,1.8,22, None)
        self.argparser.add_argument(
            "--bedbolts_settings", action="store", type=str, default=str(m3_22mm_screw_settings),
            help="pass a tuple numbers: screw_diameter, nut_sidelength, nut_thickness, screw_length, nut_position. You may pass None for nut_position to calculate a reasonable value based on screw_length, material and nut thickness. All values in mm.")
        
        self.argparser.add_argument(
            "--holes", action="store", type=str, default="(('left', 119,119,15,15,5),('back',55,120,20,20,5), ('right', 100,100,15,15,50))",
            help="To specify parameters for holes for ventilation, buttons, displays, connectors, etc. . Pass a tuple of tuples of the form (partname, width, height, dist_from_left, dist_from_bottom, radius). Partname is a string and one of 'left','right','bottom','back','panel','upper_panel', 'top','front'. All lengths are in mm.")

        self.argparser.add_argument(
            "--radius",  action="store", type=float, default=20,
            help="radius of the rounding at the flex joint, in mm. This is only relevant when style='%s'" % self.FLEX_CORNERS)


    def render(self):
        import ast
        import numpy.linalg

        # Initialize canvas
        self.open()

        # safely evaluate the python tuple code passed via a parameter
        self.holes = ast.literal_eval(self.holes)
        self.bedbolts_settings = ast.literal_eval(self.bedbolts_settings)
        self.bedbolts_number = ast.literal_eval(self.bedbolts_number)
        if(not isinstance(self.bedbolts_number, tuple)):
            self.bedbolts_number = (self.bedbolts_number,)

        # check angles for consistency
        if(self.angle <= 0):
            raise ValueError("angle must be > 0")

        if(self.middle_angle > 0):
            if(self.middle_angle < self.angle):
                raise ValueError("middle_angle must be >= angle")
            if(self.top_sidelength <= 0):
                raise ValueError("top_sidelength must be nonzero if middle_angle is nonzero.")

        if(self.bedbolts_settings[-1] is None):
            self.bedbolts_settings = self.bedbolts_settings[0:-1] + (self.bedbolts_settings[3] - self.thickness - self.bedbolts_settings[2] - 1.5,)

        # put the tuple into a list, because getEntry() likes that
        self.bedbolts_settings = [self.bedbolts_settings,]# * (self.bedbolts_number*2 +4)

        if(self.style == self.SHARP_CORNERS):
            self.radius = 0
        
        # render your parts here


        if(self.middle_angle > 0):
            lower_panel_slope_angle = self.middle_angle - 90 - (90 - self.angle)
            
            top_sidelength = self.top_sidelength
            # to find the coordinate of the kink, solve these 5 equations for the 5 unknowns (in uppercase)...
            #KINK_Y = height - math.sin(math.radians(self.angle)) * UPPER_PANEL_SIDELENGTH
            #KINK_X = top_sidelength + math.cos(math.radians(self.angle)) * UPPER_PANEL_SIDELENGTH
            #LOWER_PANEL_PROJ_X = depth - KINK_X
            #LOWER_PANEL_PROJ_Y = KINK_Y - front_height
            #tan(lower_panel_slope_angle) = LOWER_PANEL_PROJ_Y / LOWER_PANEL_PROJ_X
            
            # bring this into matrix-vector form:
            #0  = height - math.sin(math.radians(self.angle)) * UPPER_PANEL_SIDELENGTH - KINK_Y
            #0 = top_sidelength + math.cos(math.radians(self.angle)) * UPPER_PANEL_SIDELENGTH - KINK_X
            #0 = depth - KINK_X - LOWER_PANEL_PROJ_X
            #0 = KINK_Y - front_height - LOWER_PANEL_PROJ_Y
            #0 = - tan(lower_panel_slope_angle)*LOWER_PANEL_PROJ_X + LOWER_PANEL_PROJ_Y
            
            # thus...
            
            #
            # 0    (0,-1,0,0,-math.sin(math.radians(self.angle)))    ( KINK_X                 )    ( height )
            # 0    (-1,0,0,0,math.cos(math.radians(self.angle)) )    ( KINK_Y                 )    ( top_sidelength )
            # 0  = (-1,0,-1,0,0                                 )  * ( LOWER_PANEL_PROJ_X     )  + ( depth )
            # 0    (0,1,0,-1,0                                  )    ( LOWER_PANEL_PROJ_Y     )    ( -front_height )
            # 0    (0,0,- tan(lower_panel_slope_angle),1,0      )    ( UPPER_PANEL_SIDELENGTH )    ( 0 )
            #
            
            # and solve...
            matrixA = numpy.array([[0,-1,0,0,-math.sin(math.radians(self.angle))],
                                   [-1,0,0,0,math.cos(math.radians(self.angle))],
                                   [-1,0,-1,0,0],
                                   [0,1,0,-1,0],
                                   [0,0,- math.tan(math.radians(lower_panel_slope_angle)),1,0],
            ])
            vectorb = - numpy.array([self.height, top_sidelength, self.depth, -self.front_height, 0])
            vectorx = numpy.linalg.solve(matrixA, vectorb)
            
            # now we have the solution:
            kink_x = vectorx[0]
            kink_y = vectorx[1]
            lower_panel_proj_x = vectorx[2]
            lower_panel_proj_y = vectorx[3]
            upper_panel_sidelength = vectorx[4]

            print("kink x coordinate: %f" % kink_x)
            print("kink y coordinate: %f" % kink_y)
            
            
            lower_panel_sidelength = math.sqrt(lower_panel_proj_x**2 + lower_panel_proj_y**2)
            panel_sidelength = lower_panel_sidelength
            
            polygon_x =     (0,  self.depth, self.depth,        kink_x,           top_sidelength, 0)
            polygon_y =     (0,  0,          self.front_height, kink_y,           self.height,    self.height)
            corner_radius = [0.0,0.0,        self.radius,       self.radius,      self.radius,    0.0]

            n_panels = 2
            
        else:
            #tan(angle) = (height-self.front_height) / panel_sidelength_proj
            # ->
            panel_sidelength_proj = (self.height-self.front_height) / math.tan(math.radians(self.angle))
            panel_sidelength = math.sqrt((self.height-self.front_height)**2 + panel_sidelength_proj**2)
            
            top_sidelength = self.depth - panel_sidelength_proj
            top_sidelength = max(top_sidelength, 0)
            
            polygon_x =     (0,  self.depth, self.depth,             top_sidelength, 0)
            polygon_y =     (0,  0,          self.front_height,      self.height,    self.height)
            corner_radius = [0.0,0.0,        self.radius,            self.radius,    0.0]

            n_panels = 1

        bedBolts = [None,] *len(polygon_x)

        #right
        if(self.style == self.FLEX_CORNERS):
            edge_string = 'hee' + ('e'*n_panels) + 'h'
            # bedBolts[1] = edges.Bolts(1)
            # bedBolts[2:2+n_panels] = [edges.Bolts(self.bedbolts_number),]*n_panels
            # bedBolts[2+n_panels] = edges.Bolts(1)
            # bedBoltsPanel = bedBolts[1:2+n_panels + 1]
            bedBolts[1:1+n_panels+2] = [edges.Bolts(self.getEntry(self.bedbolts_number,i,self.bedbolts_number[-1]))
                                        for i in range(0,n_panels+2)]

            bedBoltsPanel = bedBolts[1:2+n_panels + 1]
        else:
            side_edge = self.top_edge == self.TOP_EDGE_FINGER and "F" or "E"

            edge_string = 'hfe' + ('f'*n_panels) + 'h'
            bedBolts[2] = edges.Bolts(self.getEntry(self.bedbolts_number,0))

        self.drawHoles('right')
        line_lengths = self.polygonWall(polygon_x, polygon_y, edge_string, corner_radius=corner_radius,
                                        bedBolts=bedBolts, bedBoltSettings=self.bedbolts_settings,
                                        move="right")

        #left
        self.drawHoles('left')
        self.polygonWall(polygon_x, polygon_y, edge_string, corner_radius=corner_radius,
                         bedBolts=bedBolts, bedBoltSettings=self.bedbolts_settings,
                         move="right")

        # bottom
        self.drawHoles('bottom')
        edge_string = self.style == self.FLEX_CORNERS and "ffef" or "ffff"
        self.rectangularWall(self.width, self.depth, edge_string, bedBolts=None, move="right")

        #back
        self.drawHoles('back')
        edge_string = self.style == self.FLEX_CORNERS and "hfef" or "hfff"
        self.rectangularWall(self.width, self.height, edge_string, bedBolts=None, move="right")

        #panel
        
        if(self.style == self.FLEX_CORNERS):
            self.drawHoles('panel')
            self.panelFlexWall(line_lengths[2:2+(2+n_panels)*2],
                               bedBolts=bedBoltsPanel, bedBoltSettings=self.bedbolts_settings,
                               extra_thickness_outset=True, move='right')
        else:
            bedBolts = [None,] *4
            bedBolts[1] = bedBolts[3] = edges.Bolts(self.getEntry(self.bedbolts_number,0))
            self.drawHoles('panel')
            edge_string = self.middle_angle > 0 and 'EEeE' or 'EEEE'
            self.rectangularWall(self.width, panel_sidelength,
                                 edge_string,
                                 bedBolts=bedBolts, bedBoltSettings=self.bedbolts_settings,
                                 move="right")

            #front
            self.drawHoles("front")
            self.rectangularWall(self.width, self.front_height, "hFeF", bedBolts=None, move="right")

            #top
            self.drawHoles("top")
            # FIXME schiefe winkel finger sind nicht korrekt
            side_edge = self.top_edge == self.TOP_EDGE_FINGER and "F" or "E"
            edge_string = self.middle_angle > 0 and ("f"+side_edge+"h"+side_edge) or "e"+side_edge+"h"+side_edge 
            self.rectangularWall(self.width, top_sidelength, edge_string, bedBolts=None, move="right")

            if(self.middle_angle > 0):
                #upper_panel
                self.drawHoles("upper_panel")
                self.rectangularWall(self.width, upper_panel_sidelength, "eFFF", bedBolts=None, move="right")

        self.close()


    def drawHoles(self, partname):
        PARTNAME=0
        WIDTH=1
        HEIGHT=2
        DIST_FROM_LEFT=3
        DIST_FROM_BOTTOM=4
        RADIUS=5
        for i in range(len(self.holes)):
            if(partname == self.holes[i][PARTNAME]):
                try:
                    self.drawRectHole(self.holes[i][WIDTH],
                                      self.holes[i][HEIGHT],
                                      self.holes[i][DIST_FROM_LEFT],
                                      self.holes[i][DIST_FROM_BOTTOM],
                                      self.holes[i][RADIUS])
                except:
                    pass
                    
    def drawRectHole(self, width, height, dist_from_left, dist_from_bottom, radius):
        if(width > 0 and height > 0):
            self.rectangularHole(width*0.5 + self.thickness + dist_from_left,
                                 height*0.5+2*self.thickness + dist_from_bottom,
                                 width, height,
                                 r=radius)

    def polygonWall(self, points_x, points_y,
                    edges='e',
                    corner_radius=[0],
                    bedBolts=None, bedBoltSettings=None,
                    callback=None, move=None):
        """Create regular polygone as a wall

        returns a list of corresponding line lengths, alternating with rounded corner line length:
        [length line, length of corner rounding, length of next line, length of next rounding,...]
        
        :param points_x: list of x coordinates
        :param points_y: list of y coordinates
        :param edges:  (Default value = "e", may be string/list of length corners)
        :param corner_radius: Radius of the rounding at each corner (Default value = [0])
        :param callback:  (Default value = None, middle=0, then sides=1..)
        :param move:  (Default value = None)
        """

        # copy 2 points, to be able to compute the corner angle also
        # for the last point.
        px = points_x + (points_x[0],points_x[1])
        py = points_y + (points_y[0],points_y[1])

        total_w = max(px) - min(px) + 3*self.thickness
        total_h = max(py) - min(py) + 3*self.thickness

        if self.move(total_w, total_h, move, before=True):
            return

        i = 0

        self.moveTo(px[i], py[i])

        # duplicate the last character, to match the number of points
        if not hasattr(edges, "__getitem__") or len(edges) < len(points_x):
            edges += edges[-1] * len(points_x)
        # copy one object, for drawing the proper edge corner at the last point
        edges += edges[0]
        # obtain corresponding edge objects
        edges = [self.edges.get(e, e) for e in edges]

        if not hasattr(corner_radius, "__getitem__") or len(corner_radius) < len(points_x):
            corner_radius += [corner_radius[-1],] * len(points_x)
        # copy one object, for drawing the proper edge corner at the last point
        corner_radius += [corner_radius[0],]

        line_lengths = []

        # not sure what this callback stuff does exactly and if I really need it here
        #self.cc(callback, 0, side/2., h+edges[0].startwidth() + self.burn)

        last_delta_distance = 0
        if(corner_radius[0] != 0):
            raise NotImplementedError("The corner_radius at point 0 must be 0!")
        
        for i in range(len(points_x)):
            self.cc(callback, i+1, 0, edges[i].startwidth() + self.burn)
            distance_vector = (px[i+1] - px[i], (py[i+1] - py[i]))
            distance = math.sqrt(distance_vector[0]**2 + distance_vector[1]**2)

            next_distance_vector = (px[i+2] - px[i+1], (py[i+2] - py[i+1]))
            next_distance = math.sqrt(next_distance_vector[0]**2 + next_distance_vector[1]**2)
            scalar_product = distance_vector[0]*next_distance_vector[0] + distance_vector[1]*next_distance_vector[1]
            # unfortunately this method does not yield the sign of the angle
            angle_at_that_corner = math.degrees(math.acos(scalar_product/(distance * next_distance)))

            complement_angle = 180-angle_at_that_corner
            # to obtain the sign of the angle, compute the cross product and take the sign of the z component.
            angle_at_that_corner *= (distance_vector[0]*next_distance_vector[1] - distance_vector[1]*next_distance_vector[0] >= 0 and 1 or -1)
            # tan(90 - complement_angle/2) = delta_distance / radius
            # -> 
            delta_distance_end = corner_radius[i+1] * math.tan(math.radians(90 - complement_angle/2))

            line_length = distance - delta_distance_end - last_delta_distance
            line_lengths += [line_length,]

            edges[i](line_length,
                     bedBolts=self.getEntry(bedBolts, i),
                     bedBoltSettings=self.getEntry(bedBoltSettings, i))
            if(corner_radius[i+1] == 0):
                self.edgeCorner(edges[i], edges[i+1], angle_at_that_corner)
            else:
                #the next line is untested, just a guess, maybe it
                #happens to do the job for more complicate edge type
                #transitions:
                self.edgeCorner(edges[i], edges[i+1], 0)
                # draw a rounding
                self.corner(angle_at_that_corner, corner_radius[i+1])
            line_lengths += [abs(math.radians(angle_at_that_corner) * corner_radius[i+1]),]
            last_delta_distance = delta_distance_end

        self.ctx.stroke()
        self.move(total_w, total_h, move)
        return line_lengths
        
    def panelFlexWall(self, line_lengths, bedBolts=None, bedBoltSettings=None, extra_thickness_outset=False, move=None):
        """
        Create part with alternating straight and flex elements, to fit onto a rounded polygonWall contour

        :param line_lengths: returns a list of corresponding line lengths, alternating with rounded corner line length:
        [length line, length of corner rounding, length of next line, length of next rounding,...]
        This can be obtained as return value of polygonWall().
        :param bedBolts: A bedBolt object for every second element of line_lengths, or None
        :param extra_thickness_outset: Add one thickness to the length of the first and last line. This is to fit nicely to other parts with 'h' edges.
        :param move:  (Default value = None)

        """
        width, depth, = self.width, self.depth

        total_w = sum(line_lengths) + 4*self.thickness
        if(extra_thickness_outset):
            total_w += + 2*self.thickness
        total_h = self.width + 3*self.thickness
        
        if self.move(total_w, total_h, move, before=True):
            return

        self.moveTo(2*self.thickness, 0)

        if(bedBolts is not None and len(bedBolts) != len(line_lengths)//2):
            raise ValueError("exactly %n bedBolts must be specified", len(line_lengths)//2)
        
        # if(line_lengths[-1] != 0.0):
        #     raise ValueError("last element of line_lengths must 0.0: there must not be a rounding at the last corner considered for this part")

        if(extra_thickness_outset):
            self.edges["E"](1 * self.thickness)
        
        for i in range(0,len(line_lengths),2):
            self.edges["E"](line_lengths[i],
                            bedBolts=self.getEntry(bedBolts,i//2),
                            bedBoltSettings=self.getEntry(bedBoltSettings,i//2))
            self.edges["X"](line_lengths[i+1], self.width + 2 * self.thickness)

        if(extra_thickness_outset):
            self.edges["E"](1 * self.thickness)
        
        self.edgeCorner(self.edges['E'], self.edges['E'], 90)
        self.edges["E"](self.width)
        self.edgeCorner(self.edges['E'], self.edges['E'], 90)

        if(extra_thickness_outset):
            self.edges["E"](1 * self.thickness)
        
        for i in reversed(range(0,len(line_lengths),2)):
            self.edges["E"](line_lengths[i+1])
            self.edges["E"](line_lengths[i],
                            bedBolts=self.getEntry(bedBolts,i//2),
                            bedBoltSettings=self.getEntry(bedBoltSettings,i//2))

        if(extra_thickness_outset):
            self.edges["E"](1 * self.thickness)
        
        self.edgeCorner(self.edges['E'], self.edges['E'], 90)
        self.edges["E"](self.width)
        self.edgeCorner(self.edges['E'], self.edges['E'], 90)

        self.move(total_w, total_h, move)
