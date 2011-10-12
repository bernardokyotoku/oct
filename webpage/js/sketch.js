var drawNodes = [];
var sketchpad = null;
var start = null;
var outline = null;
var offset = null;

$('#sketch').svg({
    onLoad: function (svg) {
        sketchpad = svg;
        var surface = svg.rect(0, 0, '100%', '100%', {
            id: 'surface',
            fill: 'white'
        });
        $(surface).mousedown(startDrag).mousemove(dragging).mouseup(endDrag);
//	resetSize(svg, '100%', '100%');
    }
});

// Remember where we started 
function startDrag(event) {
    offset = ($.browser.msie ? {
        left: 0,
        top: 0
    } : $('#sketch').offset());
    if (!$.browser.msie) {
        offset.left -= document.documentElement.scrollLeft || document.body.scrollLeft;
        offset.top -= document.documentElement.scrollTop || document.body.scrollTop;
    }
    start = {
        X: event.clientX - offset.left,
        Y: event.clientY - offset.top
    };
    event.preventDefault();
}

//   Provide feedback as we drag 
function dragging(event) {
    if (!start) {
        return;
    }
    if (!outline) {
        outline = sketchpad.rect(0, 0, 0, 0, {
            fill: 'blue',
            stroke: '#c0c0c0',
            strokeWidth: 1,
            strokeDashArray: '2,2'
        });
        $(outline).mouseup(endDrag);
    }
    sketchpad.change(outline, {
        x: Math.min(event.clientX - offset.left, start.X),
        y: Math.min(event.clientY - offset.top, start.Y),
        width: Math.abs(event.clientX - offset.left - start.X),
        height: Math.abs(event.clientY - offset.top - start.Y)
    });
    event.preventDefault();
}

// Draw where we finish 
function endDrag(event) {
    if (!start) {
        return;
    }
    $(outline).remove();
    outline = null;
    drawShape(start.X, start.Y, event.clientX - offset.left, event.clientY - offset.top);
    start = null;
    event.preventDefault();
}

// Draw the selected element on the canvas 
function drawShape(x1, y1, x2, y2) {
    var left = Math.min(x1, x2);
    var top = Math.min(y1, y2);
    var right = Math.max(x1, x2);
    var bottom = Math.max(y1, y2);
    var settings = {
        fill: $('#fill').val(),
        stroke: $('#stroke').val(),
        strokeWidth: $('#swidth').val()
    };
    var shape = $('#shape').val();
    var node = null;
    if (shape == 'rect') {
        node = sketchpad.rect(left, top, right - left, bottom - top, settings);
    }
    else if (shape == 'circle') {
        var r = Math.min(right - left, bottom - top) / 2;
        node = sketchpad.circle(left + r, top + r, r, settings);
    }
    else if (shape == 'ellipse') {
        var rx = (right - left) / 2;
        var ry = (bottom - top) / 2;
        node = sketchpad.ellipse(left + rx, top + ry, rx, ry, settings);
    }
    else if (shape == 'line') {
        node = sketchpad.line(x1, y1, x2, y2, settings);
    }
    else if (shape == 'polyline') {
        node = sketchpad.polyline([
            [(x1 + x2) / 2, y1],
            [x2, y2],
            [x1, (y1 + y2) / 2],
            [x2, (y1 + y2) / 2],
            [x1, y2],
            [(x1 + x2) / 2, y1]], $.extend(settings, {
            fill: 'none'
        }));
    }
    else if (shape == 'polygon') {
        node = sketchpad.polygon([
            [(x1 + x2) / 2, y1],
            [x2, y1],
            [x2, y2],
            [(x1 + x2) / 2, y2],
            [x1, (y1 + y2) / 2]], settings);
    }
    drawNodes[drawNodes.length] = node;
    $(node).mousedown(startDrag).mousemove(dragging).mouseup(endDrag);
    $('#sketch').focus();
};

//  Remove the last drawn element 
$('#undo').click(function () {
    if (!drawNodes.length) {
        return;
    }
    sketchpad.remove(drawNodes[drawNodes.length - 1]);
    drawNodes.splice(drawNodes.length - 1, 1);
});

//   Clear the canvas 
$('#clear2').click(function () {
    while (drawNodes.length) {
        $('#undo').trigger('click');
    }
});

//    Convert to text 
$('#toSVG').click(function () {
    alert(sketchpad.toSVG());
});
