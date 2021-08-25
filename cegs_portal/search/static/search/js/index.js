function e(name) {
    attributes = {}
    children = []
    if(arguments.length == 2) {
        children = arguments[1]
    }
    if(arguments.length == 3) {
        attributes = arguments[1]
        children = arguments[2]
    }

    element = document.createElement(name);
    for(key in attributes) {
        element.setAttribute(key, attributes[key]);
    }
    if(Array.isArray(children)) {
        for(child of children) {
            if(typeof child === "string") {
                child = t(child)
            }
            element.appendChild(child);
        }
    } else {
        if(typeof children === "string") {
            children = t(children)
        }
        element.appendChild(children);
    }

    return element;
}

function t(text) {
    return document.createTextNode(text);
}
