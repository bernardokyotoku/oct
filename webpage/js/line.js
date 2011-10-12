const SVG = "http://www.w3.org/2000/svg";
const XLINK = "http://www.w3.org/1999/xlink";
const XHTML = "http://www.w3.org/1999/xhtml";
const hotspot = "rgba(0,200,200,0.3)";

function newLine(id, x0, y0, xf, yf, stroke) {
  var p = document.createelementns(svg, "line");
  p.setattribute("id", id);
  svgsetxy(p, x0, y0, xf, yf);
  p.setattribute("stroke", stroke);
  p.setattribute("stroke-width", 10);
  return p;
}

// convenience function to set x, y, width, and height attributes
function svgsetxy(el, x0, y0, xf, yf) {
  d = "M "+x0+","+y0+" "+xf+","+yf
  el.setattribute("d",d)
}

line = newLine("line",0,0,100,100,2)

g = document.createElementNS(SVG,"g")
