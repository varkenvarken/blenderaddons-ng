# test_select_colinear_edges_benchmark

Selecting colinear edges has two modes: one only allowing colinear paths, where all selected edges must be connected to the originally selected ons, and one where all colinear edges are selected, even if there are gaps in between.

The first one performs in roughly linear time with the number of originally selected edges, because it only looks at connected edges. The second mode however has to test *all* edges in the mesh for colinearity which for large meshes can take a very long time!

## benchmark (baseline)

A basic cube subdivided 100 times actually takes almost 100ms. If we look at the benchmark, we get this result:

Runs in 92 ms (11 Ops/s)

So it is time to profile and see if we can improve that.

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

   ... lines left out for brevity ...

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

Python function calls are slow, so lets first inline the normalized direction calculation

That runs in 85 ms or 11.5 Ops/s, only a slight improvement. But we also see that normalization takes up a lot of time (lines 90 and 95),
while we don´t need that for the call to the `angle()` method as this will take care of it itself.

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
  
   ... lines left out for brevity ...
  
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

We can make another slight improvement by not testing it the angle is None (line 99), and we can do that providing a fallback value that is way bigger than pi.

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

  
   ... lines left out for brevity ...
  

```

## using a fallback

Alas, no difference (line 101).

If we want further improvements we will have to stop using Blender's mathutils module and reimplement our core routine using numpy.

```
Timer unit: 1e-06 s

Total time: 0.167435 s
File: /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py
Function: are_colinear at line 86

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    86                                                   @profile
    87                                                   def are_colinear(e1, e2):
    88                                                       # Check if direction vectors are parallel
    89    122412      20389.0      0.2     12.2              v1, v2 = e1.verts
    90    122412      18732.6      0.2     11.2              dir1 = (v2.co - v1.co)  # .normalized()
    91                                                       # guard against zero length edges
    92                                                       # if dir1.length < 1e-6:
    93                                                       #     return False
    94    122412      20143.2      0.2     12.0              v1, v2 = e2.verts
    95    122412      17714.4      0.1     10.6              dir2 = (v2.co - v1.co)  # .normalized()
    96                                                       # if dir2.length < 1e-6:
    97                                                       #     return False
    98    122412      24820.8      0.2     14.8              angle = dir1.angle(dir2, 10)
    99                                                       # if angle is None:
   100                                                       #     return False
   101    122412      18129.9      0.1     10.8              if not (angle < threshold_rad or abs(angle - 3.14159265) < threshold_rad):
   102     81608       5670.5      0.1      3.4                  return False
   103                                                       # Check if the vector between their start points is also parallel to the direction
   104     40804       6573.1      0.2      3.9              v1 = e1.verts[0].co
   105     40804       5450.5      0.1      3.3              w1 = e2.verts[0].co
   106     40804       4280.9      0.1      2.6              between = w1 - v1
   107                                                       # If between is zero vector, they share a vertex, so colinear
   108     40804       4766.4      0.1      2.8              if between.length < 1e-6:
   109         1          0.1      0.1      0.0                  return True
   110     40803       6687.2      0.2      4.0              between_dir = between.normalized()
   111     40803       7396.6      0.2      4.4              angle2 = dir1.angle(between_dir)
   112     40803       6679.8      0.2      4.0              return angle2 < threshold_rad or abs(angle2 - 3.14159265) < threshold_rad

  
   ... lines left out for brevity ...
  
```

## numpy

With the core routine implemented with numpy, we benchmark at about 64ms or 13.5 Ops/s.

And now only about 59% of the time is spent in the colinearity core routines (line 196), and this does change only marginally if we up the number of cuts from 100 to 500.

This implies that it will be very difficult to improve this, because 500 cuts is well over 3 million edges.

The `select_colinear()` function spends all its time either in core `foreach_get()` or `foreach_set()` method calls (line 40-42,47), which we cannot optimize, or (for about a third of time) in the `colinear_edges()` function (line 46), which has its running time spread pretty evenly across many of its lines (line 55-82). Tweaking those lines may gain a few percent, which then only contributes to a third of 59% of the total, which is a wasted effort (1%  * 33% * 59% ≈ 1/2000).

However, 40% or so of the total runtime is spent switching to and from object mode (lines 195, 197), so it would be nice if we could do without that, and that is something we might look in later.

```
Timer unit: 1e-06 s

Total time: 0.0105152 s
File: /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py
Function: colinear_edges at line 50

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    50                                           @profile
    51                                           def colinear_edges(selected: np.ndarray, indices, coords, threshold):
    52         1         26.0     26.0      0.2      colinear = np.zeros_like(selected)
    53                                           
    54                                               # calculate direction vectors for each edge
    55         1       1853.8   1853.8     17.6      edge_dirs = coords[indices[:, 1]] - coords[indices[:, 0]]
    56         1       2614.2   2614.2     24.9      edge_dirs = edge_dirs / np.linalg.norm(edge_dirs, axis=1)[:, np.newaxis]
    57                                           
    58         2         18.1      9.0      0.2      for e in selected.nonzero()[0]:
    59                                                   # get the direction vector of the selected edge
    60         1          0.9      0.9      0.0          dir1 = edge_dirs[e]
    61                                                   # check all other edges for colinearity
    62         1        559.6    559.6      5.3          angles = np.arccos(np.clip(np.dot(dir1, edge_dirs.T), -1.0, 1.0))
    63         1         88.4     88.4      0.8          parallel = (angles < threshold) | (np.abs(angles - np.pi) < threshold)
    64         1          1.7      1.7      0.0          v1 = coords[indices[e, 0]]
    65         1       1415.6   1415.6     13.5          w1 = coords[indices[:, 0]]
    66                                                   # vector between start points
    67         1        716.4    716.4      6.8          between = w1 - v1
    68                                                   # if the vector between start points is zero, they share a vertex, so colinear
    69         1       1846.5   1846.5     17.6          between_length = np.linalg.norm(between, axis=1)
    70         1         14.2     14.2      0.1          connected = between_length < 1e-6
    71         2         19.6      9.8      0.2          angles_between = np.abs(
    72         2        130.9     65.5      1.2              np.arccos(
    73         2        137.6     68.8      1.3                  np.clip(
    74         1        954.3    954.3      9.1                      np.dot(dir1, (between / between_length[:, np.newaxis]).T), -1.0, 1.0
    75                                                           )
    76                                                       )
    77                                                   )
    78         2         19.1      9.6      0.2          bparallel = (angles_between < threshold) | (
    79         1         80.9     80.9      0.8              np.abs(angles_between - np.pi) < threshold
    80                                                   )
    81                                                   # colinear if they are parallel and either share a vertex or the angle between the direction vector and the vector between start points is less than the threshold
    82         1         17.2     17.2      0.2          colinear |= (connected | bparallel) & parallel
    83                                           
    84         1          0.1      0.1      0.0      return colinear

Total time: 0.030595 s
File: /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py
Function: select_colinear at line 33

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    33                                           @profile
    34                                           def select_colinear(edges, vertices, threshold):
    35         1          8.5      8.5      0.0      n_edges = len(edges)
    36         1          0.3      0.3      0.0      n_vertices = len(vertices)
    37         1         10.4     10.4      0.0      indices = np.empty(2 * n_edges, dtype=int)
    38         1          1.4      1.4      0.0      coords = np.empty(3 * n_vertices, dtype=float)
    39         1          5.7      5.7      0.0      selected = np.zeros(n_edges, dtype=bool)
    40         1       6524.1   6524.1     21.3      edges.foreach_get("vertices", indices)
    41         1       2690.8   2690.8      8.8      edges.foreach_get("select", selected)
    42         1       5470.2   5470.2     17.9      vertices.foreach_get("co", coords)
    43         1          5.6      5.6      0.0      coords = coords.reshape((n_vertices, 3))
    44         1          1.1      1.1      0.0      indices = indices.reshape((n_edges, 2))
    45                                           
    46         1      10546.0  10546.0     34.5      colinear = colinear_edges(selected, indices, coords, threshold)
    47         1       5318.3   5318.3     17.4      edges.foreach_set("select", colinear)
    48         1         12.7     12.7      0.0      return np.count_nonzero(colinear)

Total time: 0.0516391 s
File: /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py
Function: do_execute at line 118

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   118                                               @profile
   119                                               def do_execute(self, context: bpy.types.Context) -> set[str]:
  
   ... lines left out for brevity ...
  
   195         1       3270.2   3270.2      6.3              bpy.ops.object.mode_set(mode="OBJECT")
   196         1      30637.2  30637.2     59.3              select_colinear(obj.data.edges, obj.data.vertices, self.angle_threshold)
   197         1      17544.0  17544.0     34.0              bpy.ops.object.mode_set(mode="EDIT")
   198         1          0.8      0.8      0.0          return {"FINISHED"}

  0.01 seconds - /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py:50 - colinear_edges
  0.03 seconds - /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py:33 - select_colinear
  0.05 seconds - /workspaces/blenderaddons-ng/add_ons/select_colinear_edges.py:118 - do_execute
```

## conclusion

Switching to use numpy for the most expensive mode of colinearity testing gains us a lot: Not only do we go from 92ms to 64ms for the 100 times subdivided cube, the 500 times subdivided cube now almost finishes in the same time, where we would not even dare trying it on that number of edges with the old algorithm.

There might me some room for improvement left, but we leave it at that for now.
