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
import math

class BookEnvelope(Boxes):
    """Book Envelope"""

    webinterface = True

    ui_group = "Misc"

    SPECIAL_FORMAT = "special format"
    FLEX_BACK_SOLID_FRONT = "flex back, and solid front"
    FLEX_BACK_LOOSE_FRONT = "flex back, and loose front"
    OPEN_BACK_LOOSE_FRONT = "open back, and loose front"

    def __init__(self):
        Boxes.__init__(self)

        self.din_page_sizes = {
            "DIN A0": (841, 1189)
        }
        din_key = "DIN A%d"
        for i in range(1,8):
            self.din_page_sizes[din_key % i] = (self.din_page_sizes[din_key % (i-1)][1]/2, self.din_page_sizes[din_key % (i-1)][0])

        self.addSettingsArgs(edges.FlexSettings)
        self.buildArgParser()
        self.argparser.add_argument(
                    "--page_format", action="store", type=str,
                    choices=sorted(self.din_page_sizes.keys()) + [self.SPECIAL_FORMAT,],
                    default=sorted(self.din_page_sizes.keys())[6],
                    help="DIN page format")
        self.argparser.add_argument(
                    "--portrait", action="store", type=boolarg, default=True,
                    help="portrait (Checked) or landscape (unchecked)")

        self.argparser.add_argument(
                    "--width", action="store", type=float, default=148,
                    help="special format: (portrait format) width in mm")
        self.argparser.add_argument(
                    "--height", action="store", type=float, default=210,
                    help="special format: (portrait format) height in mm")

        self.argparser.add_argument(
                    "--extra", action="store", type=float, default=5,
                    help="extra rim size at three sides, in mm")
        
        self.argparser.add_argument(
                    "--depth", action="store", type=float, default=8,
                    help="inner depth in mm (only revelant if flex back is used)")

        self.argparser.add_argument(
                    "--corner_radius", action="store", type=float, default=3,
                    help="corner radius in mm")

        self.argparser.add_argument(
                    "--hole_diameter_back", action="store", type=float, default=6,
                    help="hole diameter in mm (default: ISO 838)")
        self.argparser.add_argument(
                    "--hole_diameter_front", action="store", type=float, default=6,
                    help="hole diameter in mm (default: ISO 838)")
        self.argparser.add_argument(
                    "--hole_distance", action="store", type=float, default=80,
                    help="hole distance in mm (default: ISO 838)")
        self.argparser.add_argument(
                    "--hole_margin", action="store", type=float, default=12,
                    help="hole margin in mm (default: ISO 838)")

        self.argparser.add_argument(
            "--type",  action="store", type=str,
            choices=[self.FLEX_BACK_SOLID_FRONT, self.FLEX_BACK_LOOSE_FRONT, self.OPEN_BACK_LOOSE_FRONT],
            help="")


    def render(self):
        import ast
        import numpy.linalg

        # Initialize canvas
        self.open()

        # render your parts here
        self.bookEnvelope(move='right')
        self.close()


    def bookEnvelope(self, move=None):
        """
        :param move:  (Default value = None)
        """
        if(self.page_format == self.SPECIAL_FORMAT):
            width, height = self.width, self.height
        else:
            width, height = self.din_page_sizes[self.page_format]

        if(not self.portrait):
            # swap the format
            width, height = height, width

        print("This is width, height:", width, height)
        
        width += self.extra
        height += self.extra*2

        

        
        
        total_w = width * 2
        total_h = height
        
        if self.move(total_w, total_h, move, before=True):
            return

        FLEX_BACK = (self.FLEX_BACK_LOOSE_FRONT, self.FLEX_BACK_SOLID_FRONT)
        if(self.type in FLEX_BACK):
            if((self.depth) >= 20):
                radius = (self.depth + self.thickness)/2
                flex_arclength = radius*math.pi
            else:
                radius = 10 + self.thickness
                flex_arclength = radius*2*math.pi * 4.0/8.0
        else:
            flex_arclength = 0
        
        if(self.type in FLEX_BACK):
            self.edges["e"](width-self.corner_radius)
            self.edges["X"](flex_arclength, height)
            self.edges["e"](width-self.corner_radius)

            #self.edgeCorner(self.edges["e"], self.edges["e"], 90)
            self.corner(90, self.corner_radius)
            self.edges["e"](height-self.corner_radius*2)
            #self.edgeCorner(self.edges["e"], self.edges["e"], 90)
            self.corner(90, self.corner_radius)

            self.edges["e"](width-self.corner_radius)
            self.edges["e"](flex_arclength)
            self.edges["e"](width-self.corner_radius)
        
            #self.edgeCorner(self.edges["e"], self.edges["e"], 90)
            self.corner(90, self.corner_radius)
            self.edges["e"](height-self.corner_radius*2)
            #self.edgeCorner(self.edges["e"], self.edges["e"], 90)
            self.corner(90, self.corner_radius)
            # holes on the back
            if(self.hole_diameter_back > 0):
                self.rectangularHole(width-self.hole_margin,
                                 height/2-self.hole_distance/2,
                                 self.hole_diameter_back, self.hole_diameter_back,
                                 r=self.hole_diameter_back/2)
            
                self.rectangularHole(width-self.hole_margin,
                                 height/2+self.hole_distance/2,
                                 self.hole_diameter_back, self.hole_diameter_back,
                                 r=self.hole_diameter_back/2)
            
            # holes on the front
            if(self.hole_diameter_front > 0):
                self.rectangularHole(width + flex_arclength + self.hole_margin,
                                 height/2-self.hole_distance/2,
                                 self.hole_diameter_front, self.hole_diameter_front,
                                 r=self.hole_diameter_front/2)
            
                self.rectangularHole(width + flex_arclength + self.hole_margin,
                                 height/2+self.hole_distance/2,
                                 self.hole_diameter_front, self.hole_diameter_front,
                                 r=self.hole_diameter_front/2)
        else:
            # holes on the back
            if(self.hole_diameter_back > 0):
                self.rectangularHole(width-self.hole_margin,
                                 height/2-self.hole_distance/2,
                                 self.hole_diameter_back, self.hole_diameter_back,
                                 r=self.hole_diameter_back/2)
            
                self.rectangularHole(width-self.hole_margin,
                                 height/2+self.hole_distance/2,
                                 self.hole_diameter_back, self.hole_diameter_back,
                                 r=self.hole_diameter_back/2)
            # this is without rounded corners:
            #self.rectangularWall(width, height, "eeee", move="right")
            # now with 2 rounded corners:
            self.edges["e"](width-self.corner_radius)
            self.corner(90, self.corner_radius)
            self.edges["e"](height-self.corner_radius*2)
            self.corner(90, self.corner_radius)
            self.edges["e"](width-self.corner_radius)
            self.corner(90, 0)
            self.edges["e"](height)
            self.corner(90, 0)

            self.move(width, height, move)
            
            # holes on the front
            if(self.hole_diameter_front > 0):
                self.rectangularHole(self.hole_margin,
                                 height/2-self.hole_distance/2,
                                 self.hole_diameter_front, self.hole_diameter_front,
                                 r=self.hole_diameter_front/2)
            
                self.rectangularHole(self.hole_margin,
                                 height/2+self.hole_distance/2,
                                 self.hole_diameter_front, self.hole_diameter_front,
                                 r=self.hole_diameter_front/2)
            hole_cutout_distance = self.hole_diameter_front/2 + 5
            hole_cutout_width = 2*self.thickness
            stripe_width = self.hole_margin + self.hole_diameter_front/2 + hole_cutout_distance
            
            # this is without rounded corners:
            self.rectangularWall(stripe_width, height, "eeee", move="right")

            # this is without rounded corners:
            part_width = width - stripe_width - hole_cutout_width
            #self.rectangularWall(part_width, height, "eeee", move="right")
            # now with 2 rounded corners:
            self.edges["e"](part_width-self.corner_radius)
            self.corner(90, self.corner_radius)
            self.edges["e"](height-self.corner_radius*2)
            self.corner(90, self.corner_radius)
            self.edges["e"](part_width-self.corner_radius)
            self.corner(90, 0)
            self.edges["e"](height)
            self.corner(90, 0)
            
            self.move(width, height, move)



        # # cut out stripe, to allow for opening
        # if(self.type = self.OPEN_BACK):
        #     self.rectangularHole(width + flex_arclength + self.hole_margin + self.hole_diameter_front/2 + hole_cutout_distance,
        #                          height/2,
        #                          hole_cutout_width, height,
        #                          r=0)

        
        self.move(total_w, total_h, move)

        


