# test_select_colinear_edges_benchmark

## benchmark (baseline)

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

# inlining

Python function calls are slow, so we inline the normalized direction calculation

That runs in 85 ms or 11.5 Ops/s, only a slight improvement. But we also see that normalization takes up a lot of time,
while we don´t need that for the call to the angle() method as this will take care of it itself.

```Timer unit: 1e-06 s

Total time: 0.210154 s
File: /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py
Function: are_colinear at line 86

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    86                                                   @profile
    87                                                   def are_colinear(e1, e2):
    88                                                       # Check if direction vectors are parallel
    89    122412      20016.7      0.2      9.5              v1, v2 = e1.verts
    90    122412      29174.3      0.2     13.9              dir1 = (v2.co - v1.co).normalized()
    91                                                       # guard against zero length edges
    92    122412      15178.4      0.1      7.2              if dir1.length < 1e-6:
    93                                                           return False
    94    122412      22067.3      0.2     10.5              v1, v2 = e2.verts
    95    122412      26362.2      0.2     12.5              dir2 = (v2.co - v1.co).normalized()
    96    122412      14050.9      0.1      6.7              if dir2.length < 1e-6:
    97                                                           return False
    98    122412      20161.1      0.2      9.6              angle = dir1.angle(dir2)
    99    122412      17008.4      0.1      8.1              if not (angle < threshold_rad or abs(angle - 3.14159265) < threshold_rad):
   100     81608       5700.8      0.1      2.7                  return False
   101                                                       # Check if the vector between their start points is also parallel to the direction
   102     40804       6774.9      0.2      3.2              v1 = e1.verts[0].co
   103     40804       5571.9      0.1      2.7              w1 = e2.verts[0].co
   104     40804       4114.5      0.1      2.0              between = w1 - v1
   105                                                       # If between is zero vector, they share a vertex, so colinear
   106     40804       4773.9      0.1      2.3              if between.length < 1e-6:
   107         1          0.1      0.1      0.0                  return True
   108     40803       6162.8      0.2      2.9              between_dir = between.normalized()
   109     40803       6723.0      0.2      3.2              angle2 = dir1.angle(between_dir)
   110     40803       6312.7      0.2      3.0              return angle2 < threshold_rad or abs(angle2 - 3.14159265) < threshold_rad

Total time: 0.519987 s
File: /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py
Function: do_execute at line 63

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    63                                               @profile
    64                                               def do_execute(self, context: bpy.types.Context) -> set[str]:
    65         1          1.3      1.3      0.0          obj = context.active_object
    66         1          6.0      6.0      0.0          bm = bmesh.from_edit_mesh(obj.data)
    67         1          1.7      1.7      0.0          bm.edges.ensure_lookup_table()
    68                                           
    69                                                   # Find all originally selected edges
    70         1       8753.7   8753.7      1.7          original_selected_edges = [e for e in bm.edges if e.select]
    71         1          0.7      0.7      0.0          if not original_selected_edges:
    72                                                       self.report({"WARNING"}, "No edges selected")
    73                                                       return {"CANCELLED"}
    74                                           
    75                                                   # Deselect all edges first
    76    122413      11258.2      0.1      2.2          for e in bm.edges:
    77    122412      11435.4      0.1      2.2              e.select = False
    78                                           
    79         1         13.7     13.7      0.0          threshold_rad = self.angle_threshold
    80                                           
    81         2         63.1     31.5      0.0          @profile
    82         2          0.5      0.3      0.0          def edge_dir(edge):
    83                                                       v1, v2 = edge.verts
    84                                                       return (v2.co - v1.co).normalized()
    85                                           
    86         2         89.8     44.9      0.0          @profile
    87         2          0.5      0.3      0.0          def are_colinear(e1, e2):
    88                                                       # Check if direction vectors are parallel
    89                                                       v1, v2 = e1.verts
    90                                                       dir1 = (v2.co - v1.co).normalized()
    91                                                       # guard against zero length edges
    92                                                       if dir1.length < 1e-6:
    93                                                           return False
    94                                                       v1, v2 = e2.verts
    95                                                       dir2 = (v2.co - v1.co).normalized()
    96                                                       if dir2.length < 1e-6:
    97                                                           return False
    98                                                       angle = dir1.angle(dir2)
    99                                                       if not (angle < threshold_rad or abs(angle - 3.14159265) < threshold_rad):
   100                                                           return False
   101                                                       # Check if the vector between their start points is also parallel to the direction
   102                                                       v1 = e1.verts[0].co
   103                                                       w1 = e2.verts[0].co
   104                                                       between = w1 - v1
   105                                                       # If between is zero vector, they share a vertex, so colinear
   106                                                       if between.length < 1e-6:
   107                                                           return True
   108                                                       between_dir = between.normalized()
   109                                                       angle2 = dir1.angle(between_dir)
   110                                                       return angle2 < threshold_rad or abs(angle2 - 3.14159265) < threshold_rad
   111                                           
   112         1          2.8      2.8      0.0          if self.only_colinear_paths:
   113                                                       visited = set()
   114                                                       queue = []
   115                                                       for e in original_selected_edges:
   116                                                           queue.append(e)
   117                                                           visited.add(e)
   118                                           
   119                                                       while queue:
   120                                                           current_edge = queue.pop(0)
   121                                                           current_edge.select = True
   122                                                           for v in current_edge.verts:
   123                                                               for neighbor in v.link_edges:
   124                                                                   if neighbor is current_edge or neighbor in visited:
   125                                                                       continue
   126                                                                   if are_colinear(current_edge, neighbor):
   127                                                                       queue.append(neighbor)
   128                                                                       visited.add(neighbor)
   129                                                   else:
   130    122413      11165.8      0.1      2.1              for e in bm.edges:
   131    244723      20276.3      0.1      3.9                  for sel_edge in original_selected_edges:
   132    122412     456194.5      3.7     87.7                      if are_colinear(sel_edge, e):
   133       101         12.8      0.1      0.0                          e.select = True
   134       101          9.6      0.1      0.0                          break
   135                                           
   136         1        699.4    699.4      0.1          bmesh.update_edit_mesh(obj.data)
   137         1          0.8      0.8      0.0          return {"FINISHED"}

  0.21 seconds - /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py:86 - are_colinear
  0.52 seconds - /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py:63 - do_execute
```

## not calling unnecessary methods

Gets us 74ms or almost 13 Ops/s. 

We can make another slight improvement by not testing it the angle is None, and we can do that providing a fallback value that is way bigger than pi.

```Timer unit: 1e-06 s

Total time: 0.169033 s
File: /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py
Function: are_colinear at line 86

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    86                                                   @profile
    87                                                   def are_colinear(e1, e2):
    88                                                       # Check if direction vectors are parallel
    89    122412      20919.2      0.2     12.4              v1, v2 = e1.verts
    90    122412      17661.0      0.1     10.4              dir1 = (v2.co - v1.co)  # .normalized()
    91                                                       # guard against zero length edges
    92                                                       # if dir1.length < 1e-6:
    93                                                       #     return False
    94    122412      20340.2      0.2     12.0              v1, v2 = e2.verts
    95    122412      18505.9      0.2     10.9              dir2 = (v2.co - v1.co)  # .normalized()
    96                                                       # if dir2.length < 1e-6:
    97                                                       #     return False
    98    122412      21353.1      0.2     12.6              angle = dir1.angle(dir2)
    99    122412       9362.9      0.1      5.5              if angle is None:
   100                                                           return False
   101    122412      16795.8      0.1      9.9              if not (angle < threshold_rad or abs(angle - 3.14159265) < threshold_rad):
   102     81608       5695.7      0.1      3.4                  return False
   103                                                       # Check if the vector between their start points is also parallel to the direction
   104     40804       6384.1      0.2      3.8              v1 = e1.verts[0].co
   105     40804       5100.4      0.1      3.0              w1 = e2.verts[0].co
   106     40804       4145.8      0.1      2.5              between = w1 - v1
   107                                                       # If between is zero vector, they share a vertex, so colinear
   108     40804       4442.1      0.1      2.6              if between.length < 1e-6:
   109         1          0.1      0.1      0.0                  return True
   110     40803       5994.3      0.1      3.5              between_dir = between.normalized()
   111     40803       6192.3      0.2      3.7              angle2 = dir1.angle(between_dir)
   112     40803       6140.4      0.2      3.6              return angle2 < threshold_rad or abs(angle2 - 3.14159265) < threshold_rad

Total time: 0.465846 s
File: /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py
Function: do_execute at line 63

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    63                                               @profile
    64                                               def do_execute(self, context: bpy.types.Context) -> set[str]:
    65         1          1.3      1.3      0.0          obj = context.active_object
    66         1          7.5      7.5      0.0          bm = bmesh.from_edit_mesh(obj.data)
    67         1          1.5      1.5      0.0          bm.edges.ensure_lookup_table()
    68                                           
    69                                                   # Find all originally selected edges
    70         1       8951.8   8951.8      1.9          original_selected_edges = [e for e in bm.edges if e.select]
    71         1          0.9      0.9      0.0          if not original_selected_edges:
    72                                                       self.report({"WARNING"}, "No edges selected")
    73                                                       return {"CANCELLED"}
    74                                           
    75                                                   # Deselect all edges first
    76    122413       9666.8      0.1      2.1          for e in bm.edges:
    77    122412      10706.7      0.1      2.3              e.select = False
    78                                           
    79         1         23.6     23.6      0.0          threshold_rad = self.angle_threshold
    80                                           
    81         2         64.6     32.3      0.0          @profile
    82         2          0.6      0.3      0.0          def edge_dir(edge):
    83                                                       v1, v2 = edge.verts
    84                                                       return (v2.co - v1.co).normalized()
    85                                           
    86         2         70.5     35.2      0.0          @profile
    87         2          0.4      0.2      0.0          def are_colinear(e1, e2):
    88                                                       # Check if direction vectors are parallel
    89                                                       v1, v2 = e1.verts
    90                                                       dir1 = (v2.co - v1.co)  # .normalized()
    91                                                       # guard against zero length edges
    92                                                       # if dir1.length < 1e-6:
    93                                                       #     return False
    94                                                       v1, v2 = e2.verts
    95                                                       dir2 = (v2.co - v1.co)  # .normalized()
    96                                                       # if dir2.length < 1e-6:
    97                                                       #     return False
    98                                                       angle = dir1.angle(dir2)
    99                                                       if angle is None:
   100                                                           return False
   101                                                       if not (angle < threshold_rad or abs(angle - 3.14159265) < threshold_rad):
   102                                                           return False
   103                                                       # Check if the vector between their start points is also parallel to the direction
   104                                                       v1 = e1.verts[0].co
   105                                                       w1 = e2.verts[0].co
   106                                                       between = w1 - v1
   107                                                       # If between is zero vector, they share a vertex, so colinear
   108                                                       if between.length < 1e-6:
   109                                                           return True
   110                                                       between_dir = between.normalized()
   111                                                       angle2 = dir1.angle(between_dir)
   112                                                       return angle2 < threshold_rad or abs(angle2 - 3.14159265) < threshold_rad
   113                                           
   114         1          2.8      2.8      0.0          if self.only_colinear_paths:
   115                                                       visited = set()
   116                                                       queue = []
   117                                                       for e in original_selected_edges:
   118                                                           queue.append(e)
   119                                                           visited.add(e)
   120                                           
   121                                                       while queue:
   122                                                           current_edge = queue.pop(0)
   123                                                           current_edge.select = True
   124                                                           for v in current_edge.verts:
   125                                                               for neighbor in v.link_edges:
   126                                                                   if neighbor is current_edge or neighbor in visited:
   127                                                                       continue
   128                                                                   if are_colinear(current_edge, neighbor):
   129                                                                       queue.append(neighbor)
   130                                                                       visited.add(neighbor)
   131                                                   else:
   132    122413      10974.4      0.1      2.4              for e in bm.edges:
   133    244723      20581.1      0.1      4.4                  for sel_edge in original_selected_edges:
   134    122412     404107.5      3.3     86.7                      if are_colinear(sel_edge, e):
   135       101         12.5      0.1      0.0                          e.select = True
   136       101          9.3      0.1      0.0                          break
   137                                           
   138         1        662.1    662.1      0.1          bmesh.update_edit_mesh(obj.data)
   139         1          0.6      0.6      0.0          return {"FINISHED"}

  0.17 seconds - /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py:86 - are_colinear
  0.47 seconds - /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py:63 - do_execute
```
