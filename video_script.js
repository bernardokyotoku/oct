const SVG = "http://www.w3.org/2000/svg";
const XLINK = "http://www.w3.org/1999/xlink";
const XHTML = "http://www.w3.org/1999/xhtml";
const hotspot = "rgba(0,200,200,0.3)";

var currentTransform = null;
var oldVideo = null;

function doload() {
  var images;

  // Load a few images; some extra stuff here for make
  // testing from file:// URLs easier -- it will load
  // standard wallpapers on OSX or Vista.
      images = [{ url: "file:///home/bernardo/Projects/oct/movie.ogg", width: 1024, height: 1024 }, 
       ];

  // Load the images in the background, and only add them once they're
  // loaded (and, presumably, cached by the broser)
  for (var k = 0; k < images.length; k++) {
      // do some hackyness here to get the correct variables
      // to the function

	      var g = addImage(images[k].url, 1.0, images[k].width, images[k].height);
	      g.style.opacity = 1.0;
	      var c = 0.5;
	      g.vTranslate = [images[k].width*c*0.5,images[k].height*c*0.5];
	      g.vScale = c; // 0.25; // 0.001;
	      g.vRotate = 0;
      
	      setupTransform(g.id);
	      rampOpacityUp(g);
   }
  document.getElementById("canvas").addEventListener("mousemove", onMouseMove, false);
  document.getElementById("canvas").addEventListener("mouseup", onMouseUp, false);
  document.getElementById("background-rect").addEventListener("mousemove", onMouseMove, false);
  document.getElementById("background-rect").addEventListener("mouseup", onMouseUp, false);
}

// convenience function to set X, Y, width, and height attributes
function svgSetXYWH(el, x, y, w, h) {
  el.setAttribute("x", x);
  el.setAttribute("y", y);
  el.setAttribute("width", w);
  el.setAttribute("height", h);
}

// create a new clickable rect [x,y,w,h] with the givenfill/stroke
// with the given handler on mouse down
function newClickableRect(id, x, y, w, h, fill, stroke, handler) {
  var p = document.createElementNS(SVG, "rect");
  p.setAttribute("id", id);
  svgSetXYWH(p, x, y, w, h);
  p.setAttribute("rx", 30);
  p.setAttribute("ry", 30);
  p.setAttribute("fill", fill);
  //p.setAttribute("stroke", stroke);
  //p.setAttribute("stroke-width", 10);
  p.addEventListener("mousedown", handler, false);
  return p;
}

// create all the elements for the given image URL.
// this includes the toplevel group, the image itself,
// and the clickable hotspots used for rotating the image.
var nextImageId = 0;
function addImage(url, initOpacity, imgw, imgh) {
//          var imgw = 640;
//        var imgh = 480;

  var id = nextImageId++;
  var s = "image" + id;
  var g = document.createElementNS(SVG, "g");
  g.setAttribute("id", s);
  g.addEventListener("mouseover", onEnterImage, false);
  g.addEventListener("mouseout", onExitImage, false);
  g.addEventListener("mousedown", function(evt) { startTransform(evt, "c", "move"); }, false);

  if (initOpacity != null)
      g.style.opacity = initOpacity;

  var fo = document.createElementNS(SVG, "foreignObject");
  var video = document.createElementNS(XHTML, "video");          
  var div = document.createElementNS(XHTML, "div");        
  div.setAttribute("id", s+"-div");
  fo.setAttribute("id", s+"-img");
  video.setAttribute("id", s+"-video");
  video.setAttribute("style", "display: block; margin: auto;");
  svgSetXYWH(fo, -imgw/2, -imgh/2, imgw, imgh);
  fo.setAttribute("preserveAspectRatio", "xMinYMin slice");
  fo.setAttributeNS(XLINK, "href", url);
  div.appendChild(video);
  fo.appendChild(div);
  g.appendChild(fo);

  var rect = document.createElementNS(SVG, "rect");
  rect.setAttribute("id", s+"-border");
  svgSetXYWH(rect, -imgw/2, -imgh/2, imgw, imgh);
  rect.setAttribute("stroke", "black");
  rect.setAttribute("rx", "10");
  rect.setAttribute("ry", "10");
  rect.setAttribute("stroke-width", "20");
  rect.setAttribute("fill", "none");

  g.appendChild(rect);

  var g2 = document.createElementNS(SVG, "g");
  g2.setAttribute("id", s+"-overlay");
  g2.setAttribute("class", "image-overlay");
  g2.setAttribute("style", "visibility: hidden");

  var rsz = 80;

  g2.appendChild(newClickableRect(s+"-tl", -imgw/2, -imgh/2, rsz, rsz,
				  hotspot, "rgba(100,100,100,0.5)",
				  function (evt) { return startTransform(evt, 'tl', 'rotate'); }));
  g2.appendChild(newClickableRect(s+"-tr", imgw/2-rsz, -imgh/2, rsz, rsz,
				  hotspot, "rgba(100,100,100,0.5)",
				  function (evt) { return startTransform(evt, 'tr', 'rotate'); }));
  g2.appendChild(newClickableRect(s+"-br", imgw/2-rsz, imgh/2-rsz, rsz, rsz,
				  hotspot, "rgba(100,100,100,0.5)",
				  function (evt) { return startTransform(evt, 'br', 'rotate'); }));
  g2.appendChild(newClickableRect(s+"-bl", -imgw/2, imgh/2-rsz, rsz, rsz,
				  hotspot, "rgba(100,100,100,0.5)",
				  function (evt) { return startTransform(evt, 'bl', 'rotate'); }));
  /*
  g2.appendChild(newClickableRect(s+"-c", -rsz/2, -rsz/2, rsz, rsz,
				  hotspot, "rgba(100,100,100,0.5)",
				  function (evt) { return startTransform(evt, 'c', 'scale'); }));
  */

  g.appendChild(g2);

  document.getElementById("canvas").appendChild(g);
  video.src = url;
  video.muted = true;
  video.play();

  return g;
}

function bringToFront(s) {
  var el = document.getElementById(s);

  el.parentNode.removeChild(el);
  document.getElementById("canvas").appendChild(el);
  if(oldVideo) {
    oldVideo.muted = true;
  }
  oldVideo = document.getElementById(s+"-video");
  oldVideo.muted = false;
  oldVideo.play();
}

// take the transforms saved on the element and turn them into
// svg transform syntax
function setupTransform(s) {
  var g = document.getElementById(s);
  var g2 = document.getElementById(s + "-overlay");

  g.setAttribute("transform", "translate(" + g.vTranslate[0] + "," + g.vTranslate[1] + ") " +
		 "scale(" + g.vScale + "," + g.vScale + ") " +
		 "rotate(" + g.vRotate + ") ");
}

function baseName(ev) {
  var id = ev.target.getAttribute("id");
if(!id) alert(ev.target);
  return id.substr(0, id.indexOf("-"));
}

function onEnterImage(ev) {
  var e = baseName(ev);
  if (!e)
      return;
  document.getElementById(e + '-overlay').style.visibility = "visible";
}

function onExitImage(ev) {
  var e = baseName(ev);
  if (!e)
      return;
  document.getElementById(e + '-overlay').style.visibility = "hidden";
}

function startTransform(ev, corner, what) {
  // ignore if something else is already going on
  if (currentTransform != null)
      return;

  var e = baseName(ev);
  if (!e)
      return;

  bringToFront(e);
  var g = document.getElementById(e);

  currentTransform = { what: what, el: e, corner: corner, g: g,
		       s: g.vScale, r: g.vRotate, t: g.vTranslate,
		       x: ev.clientX, y: ev.clientY };
  rampOpacityDown(currentTransform.g);
}

function onMouseUp(ev) {
  if (currentTransform) {
      rampOpacityUp(currentTransform.g);
  }
  currentTransform = null;
}

function onMouseMove(ev) {
  if (!("currentTransform" in window) ||
      currentTransform == null)
      return;

  var ex = ev.clientX;
  var ey = ev.clientY;
  var pos = currentTransform.g.vTranslate;

  if (currentTransform.what == "rotate") {
      var r2d = 360.0 / (2.0 * Math.PI);

      var lastAngle = Math.atan2(currentTransform.y - pos[1],
				 currentTransform.x - pos[0]) * r2d;
      var curAngle = Math.atan2(ey - pos[1],
				ex - pos[0]) * r2d;

      currentTransform.g.vRotate += (curAngle - lastAngle);

      var lastLen = Math.sqrt(Math.pow(currentTransform.y - pos[1], 2) +
			      Math.pow(currentTransform.x - pos[0], 2));
      var curLen = Math.sqrt(Math.pow(ey - pos[1], 2) +
			     Math.pow(ex - pos[0], 2));

      currentTransform.g.vScale = currentTransform.g.vScale * (curLen / lastLen);

  } else if (currentTransform.what == "move") {
      var xd = ev.clientX - currentTransform.x;
      var yd = ev.clientY - currentTransform.y;

      currentTransform.g.vTranslate = [ pos[0] + xd, pos[1] + yd ];
  }

  currentTransform.x = ex;
  currentTransform.y = ey;

  setupTransform(currentTransform.el);
}

function rampOpacityDown(g) {
  g.style.opacity = 1.0;
  var rampFunc = function () {
      var o = parseFloat(g.style.opacity) - 0.05;
      g.style.opacity = o;
      if (o > 0.7)
	  setTimeout(rampFunc, 10);
  }
  rampFunc();
}

function rampOpacityUp(g) {
  g.style.opacity = 0.7;
  var rampFunc = function () {
      var o = parseFloat(g.style.opacity) + 0.05;
      g.style.opacity = o;
      if (o < 1.0)
	  setTimeout(rampFunc, 10);
  }
  rampFunc();
}
