# Plumb line

A small add-on to show the distance from a reference point to a point on a object directly below it.

(For the name, see: https://en.wikipedia.org/wiki/Plumb_bob)

## Description

The operator shows a overlayed vertical line from the reference point to a point on an object directly below it and shows the distance as a label.
The point of intersection is shown in a blue highlight.

The reference point can be moved around using the arrow keys and the page up/down keys, while you can still change your viewpoint using mouse and numpad keys in the usual way.
By default, the distance to a point on the active object is shown, regardless of any other objects in the scene that might be in the way, but this might be changed by pressing the S-key,
in which case the point on the nearest object will be shown.

The add-on isn´t necessarily very useful in itself, but it does demonstrate the following features:

- how to create a modal operator
  
  after the operator is is called from the Object menu, a modal handler is installed that calls the operator's modal() method with an event. 
  The method acts on these events if they are relevant (arrow keys, right mouse button, etc.) or lets them pass through if they are mouse or numpas events.

- how to create overlays in the 3d view
  
  the plumb line and highlighted intersection point are shown in the 3d view with a post view handler, 
  while the label with the distance is shown as a post pixel handler

- how to force reloading modules when reinstalling the add-on

  to make developement a little bit easier we reload modules that where already loaded.
  this obviates the need to restart blender when updating the code, so you only need to reinstall the add-on from the add-ons panel.
  There is no startup penalty when the add-on is installed the first time or when blender is restarted.

- how to use the Object.ray_cast() and Scene.ray_cast() functions
  
  The Object variant is extra interesting because there we also show how convert from object space to world space coordinates.

- how to work with user preferences
  
  for some color and font size options

- how to use a small part of numpy's functionality
  
  a really small part, but numpy is bundled with Blender and super conveniet to do array calculations, so we use it here for some of the graphical routines,
  not because we will notice any performance improvement on the small arrays we use here, but just because it saves some code.

## Type hinting

Even though I am [a bit sceptical about](https://blog.michelanders.nl/2026/01/on-the-usefulness-of-python-type-annotations-in-Blender-add-ons.html) using type hints in top level Blender code, 
I did my best to provide type annotations where possible.
This means that in a development environment outside Blender you to have the fake-bpy-module installed.

## Testing

Because this code has no side effects (it only displays an overlay as long as needed but doesn´t change the scene), I didn´t add any test code.
Top-level, interactive UI code is difficult if not impossible to test inside blender-as-a-module, and the only code worth testing otherwise
would be the ray intersecting code, but because this is only a few lines of code, I didn´t bother.

