function a(p, c) {
    p.appendChild(c);
}

function e(name) {
    let attributes = {};
    let children = [];
    if (arguments.length == 2) {
        children = arguments[1];
    }
    if (arguments.length == 3) {
        attributes = arguments[1];
        children = arguments[2];
    }

    let element = document.createElement(name);
    for (const key in attributes) {
        element.setAttribute(key, attributes[key]);
    }
    if (Array.isArray(children)) {
        for (let child of children) {
            if (typeof child === "string") {
                child = t(child);
            }
            a(element, child);
        }
    } else {
        if (typeof children === "string") {
            children = t(children);
        }

        a(element, children);
    }

    return element;
}

function g(id) {
    return document.getElementById(id);
}

function t(text) {
    return document.createTextNode(text);
}

// Clear children
function cc(p) {
    while (p.firstChild) {
        p.removeChild(p.firstChild);
    }
}

// Replace Children
function rc(p, c) {
    cc(p);
    if (Array.isArray(c)) {
        for (let child of c) {
            a(p, child);
        }
    } else {
        a(p, c);
    }
}

export {a, cc, e, g, rc, t};
