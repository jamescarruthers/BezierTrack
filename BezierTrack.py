import math
import pcbnew
from math import factorial
import os

class BezierTrack(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Bezier Tracks"
        self.category = "Artistic PCBs"
        self.description = "Convert straight tracks in to baked bezier curves"
        self.show_toolbar_button = True # Optional, defaults to False
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'BezierTrack.png') # Optional, defaults to ""

    def Run(self):
        # The entry function of the plugin that is executed on user action
        board = pcbnew.GetBoard()
        tracks = board.GetTracks()
        
        selectedTracks = []

        for t in tracks:
            if t.IsSelected():
                selectedTracks.append(t)

        points = []

        for t in selectedTracks:
            x, y = t.GetStart().x, t.GetStart().y
            points.append([x,y])
        x, y = selectedTracks[-1].GetEnd().x, selectedTracks[-1].GetEnd().y
        points.append([x, y])
    
        bpoints = self.bezier(points, 40)
        
        for xy0, xy1 in zip(bpoints, bpoints[1::]):
        
            nt = pcbnew.TRACK(board)
            nt.SetStart(pcbnew.wxPoint(xy0[0], xy0[1]))
            nt.SetEnd(pcbnew.wxPoint(xy1[0], xy1[1]))
            nt.SetWidth(selectedTracks[0].GetWidth())
            nt.SetLayer(selectedTracks[0].GetLayer())
            nt.SetNet(selectedTracks[0].GetNet())
            board.Add(nt)
            
        for t in selectedTracks:
            board.RemoveNative(t)

        pcbnew.Refresh()

    def comb(self, n, k):  # also nCr
        "k combinations of n"
        v, n1 = 1, n + 1; nk = n1 - k
        for i in range(nk, n1): v *= i
        return v // factorial(k)
 
    # keep previously computed nCr values
    _ncr_precmp = {}  # for use in bernstein poly/bezier curves
    # gives a slight speed increase for a large number of points along a bezier
    
    def bernstein(self, n, i, x):
        "bernstein polynomial n, i at point x; b_i,n(x)"
        p = self._ncr_precmp.get((n, i))
        if p is None:
            p = self.comb(n, i)
            self._ncr_precmp[(n, i)] = p
        return p * x ** i * (1 - x) ** (n - i)
    
    def bezier(self, clpts, numpts=10, endpt=True):
        "return numpts positions of a bezier curve controlled by clpts"
        if not all(map(lambda x: len(x) == len(clpts[0]), clpts)):
            err = ValueError("control points are different dimensions")
            raise err
        if len(clpts) < 2:
            err = ValueError("at least two control points are required")
            raise err
    
        n, xy = len(clpts), []
        step = float(numpts - 1 if endpt else numpts)
        dims = list(zip(*clpts))  # control points collected by their dimensions
        # [(all x value dimensions), (all y value dimensions), etc...]
    
        for t in range(numpts):
            # collect bernstein values for each control point
            bv = [self.bernstein(n - 1, v, t / step) for v in range(n)]
    
            # summation along dimension values and bernstein values
            pt = []
            for d in dims:
                pt.append(sum(i * j for i, j in zip(d, bv)))
            xy.append(tuple(pt))
        return xy

BezierTrack().register() # Instantiate and register to Pcbnew
