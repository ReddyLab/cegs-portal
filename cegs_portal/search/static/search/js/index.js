function a(p, c) {
    p.appendChild(c)
}

function e(name) {
    attributes = {};
    children = [];
    if (arguments.length == 2) {
        children = arguments[1];
    }
    if (arguments.length == 3) {
        attributes = arguments[1];
        children = arguments[2];
    }

    element = document.createElement(name);
    for (key in attributes) {
        element.setAttribute(key, attributes[key]);
    }
    if (Array.isArray(children)) {
        for (child of children) {
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

// Replace Children
function rc(p, c) {
    while (p.firstChild) {
        p.removeChild(p.firstChild);
    }

    a(p, c);
}

function dhsTable(data) {
    newTable = e("table", {id: "dnaregion",  class: "data-table"}, [
        e("tr", [
            e("th", "Cell Line"),
            e("th", "Location"),
            e("th", "Strand"),
            e("th", "Closest Gene"),
            e("th", "Reference Genome"),
            e("th"),
        ])
    ])
    for(dhs of data) {
        newTable.append(
            e("tr", [
                e("td", dhs.cell_line || "None"),
                e("td", [
                    e("span", dhs.chr),
                    ": ",
                    e("span", `${dhs.start}-${dhs.end}`)
                ]),
                e("td", dhs.strand || "None"),
                e("td", e("a", {href: `/search/gene/ensembl/${dhs.closest_gene.id}`}, `${dhs.closest_gene_name} (${dhs.closest_gene.id})`)),
                e("td", `${dhs.ref_genome}.${dhs.ref_genome_patch || 0}`),
                e("td", e("a", {href: `/search/dhs/${dhs.id}`}, "More...")),
            ])
        )
    }
    return newTable;
}
