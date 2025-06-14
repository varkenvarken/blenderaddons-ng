# test_select_colinear_edges_benchmark

## benchmark

Runs in 92 ms (11 Ops/s)

## line profile

As we can see, more than 90% of the time is spent in the colinearity test (line 130), and in that function about 76% is spent calculating normalized direction vectors (lines 89 and 93).

```
Timer unit: 1e-06 s

Total time: 0.0934679 s
File: /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py
Function: edge_dir at line 81

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    81                                                   @profile
    82                                                   def edge_dir(edge):
    83    244824      38918.9      0.2     41.6              v1, v2 = edge.verts
    84    244824      54549.0      0.2     58.4              return (v2.co - v1.co).normalized()

Total time: 0.48377 s
File: /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py
Function: are_colinear at line 86

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    86                                                   @profile
    87                                                   def are_colinear(e1, e2):
    88                                                       # Check if direction vectors are parallel
    89    122412     187058.9      1.5     38.7              dir1 = edge_dir(e1)
    90                                                       # guard against zero length edges
    91    122412      14275.8      0.1      3.0              if dir1.length < 1e-6:
    92                                                           return False
    93    122412     186678.8      1.5     38.6              dir2 = edge_dir(e2)
    94    122412      11999.9      0.1      2.5              if dir2.length < 1e-6:
    95                                                           return False
    96    122412      19896.7      0.2      4.1              angle = dir1.angle(dir2)
    97    122412      16685.6      0.1      3.4              if not (angle < threshold_rad or abs(angle - 3.14159265) < threshold_rad):
    98     81608       5574.4      0.1      1.2                  return False
    99                                                       # Check if the vector between their start points is also parallel to the direction
   100     40804       7619.7      0.2      1.6              v1 = e1.verts[0].co
   101     40804       6518.7      0.2      1.3              w1 = e2.verts[0].co
   102     40804       4389.1      0.1      0.9              between = w1 - v1
   103                                                       # If between is zero vector, they share a vertex, so colinear
   104     40804       3950.7      0.1      0.8              if between.length < 1e-6:
   105         1          0.1      0.1      0.0                  return True
   106     40803       5928.0      0.1      1.2              between_dir = between.normalized()
   107     40803       6776.4      0.2      1.4              angle2 = dir1.angle(between_dir)
   108     40803       6417.3      0.2      1.3              return angle2 < threshold_rad or abs(angle2 - 3.14159265) < threshold_rad

Total time: 0.770792 s
File: /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py
Function: do_execute at line 63

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    63                                               @profile
    64                                               def do_execute(self, context: bpy.types.Context) -> set[str]:
    65         1          1.2      1.2      0.0          obj = context.active_object
    66         1          5.8      5.8      0.0          bm = bmesh.from_edit_mesh(obj.data)
    67         1          1.1      1.1      0.0          bm.edges.ensure_lookup_table()
    68                                           
    69                                                   # Find all originally selected edges
    70         1       9866.5   9866.5      1.3          original_selected_edges = [e for e in bm.edges if e.select]
    71         1          0.5      0.5      0.0          if not original_selected_edges:
    72                                                       self.report({"WARNING"}, "No edges selected")
    73                                                       return {"CANCELLED"}
    74                                           
    75                                                   # Deselect all edges first
    76    122413      10196.4      0.1      1.3          for e in bm.edges:
    77    122412      10583.6      0.1      1.4              e.select = False
    78                                           
    79         1         27.6     27.6      0.0          threshold_rad = self.angle_threshold
    80                                           
    81         2         66.0     33.0      0.0          @profile
    82         2          0.7      0.4      0.0          def edge_dir(edge):
    83                                                       v1, v2 = edge.verts
    84                                                       return (v2.co - v1.co).normalized()
    85                                           
    86         2         69.9     34.9      0.0          @profile
    87         2          0.5      0.3      0.0          def are_colinear(e1, e2):
    88                                                       # Check if direction vectors are parallel
    89                                                       dir1 = edge_dir(e1)
    90                                                       # guard against zero length edges
    91                                                       if dir1.length < 1e-6:
    92                                                           return False
    93                                                       dir2 = edge_dir(e2)
    94                                                       if dir2.length < 1e-6:
    95                                                           return False
    96                                                       angle = dir1.angle(dir2)
    97                                                       if not (angle < threshold_rad or abs(angle - 3.14159265) < threshold_rad):
    98                                                           return False
    99                                                       # Check if the vector between their start points is also parallel to the direction
   100                                                       v1 = e1.verts[0].co
   101                                                       w1 = e2.verts[0].co
   102                                                       between = w1 - v1
   103                                                       # If between is zero vector, they share a vertex, so colinear
   104                                                       if between.length < 1e-6:
   105                                                           return True
   106                                                       between_dir = between.normalized()
   107                                                       angle2 = dir1.angle(between_dir)
   108                                                       return angle2 < threshold_rad or abs(angle2 - 3.14159265) < threshold_rad
   109                                           
   110         1          3.1      3.1      0.0          if self.only_colinear_paths:
   111                                                       visited = set()
   112                                                       queue = []
   113                                                       for e in original_selected_edges:
   114                                                           queue.append(e)
   115                                                           visited.add(e)
   116                                           
   117                                                       while queue:
   118                                                           current_edge = queue.pop(0)
   119                                                           current_edge.select = True
   120                                                           for v in current_edge.verts:
   121                                                               for neighbor in v.link_edges:
   122                                                                   if neighbor is current_edge or neighbor in visited:
   123                                                                       continue
   124                                                                   if are_colinear(current_edge, neighbor):
   125                                                                       queue.append(neighbor)
   126                                                                       visited.add(neighbor)
   127                                                   else:
   128    122413      10613.5      0.1      1.4              for e in bm.edges:
   129    244723      20421.4      0.1      2.6                  for sel_edge in original_selected_edges:
   130    122412     708241.5      5.8     91.9                      if are_colinear(sel_edge, e):
   131       101         12.2      0.1      0.0                          e.select = True
   132       101          9.7      0.1      0.0                          break
   133                                           
   134         1        670.8    670.8      0.1          bmesh.update_edit_mesh(obj.data)
   135         1          0.5      0.5      0.0          return {"FINISHED"}

  0.09 seconds - /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py:81 - edge_dir
  0.48 seconds - /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py:86 - are_colinear
  0.77 seconds - /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py:63 - do_execute
```