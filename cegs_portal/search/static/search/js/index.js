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

function regionTable(regions, emptyString) {
    if (regions.length == 0) {
        return e("div", {id: "dnaregion"}, t(emptyString));
    }

    newTable = e("table", {id: "dnaregion",  class: "data-table"}, [
        e("tr", [
            e("th", "Region Type"),
            e("th", "Cell Line"),
            e("th", "Location"),
            e("th", "Strand"),
            e("th", "Closest Gene"),
            e("th", "Reference Genome"),
            e("th"),
        ])
    ])
    for(region of regions) {
        newTable.append(
            e("tr", [
                e("td", region.type),
                e("td", region.cell_line || "None"),
                e("td", [
                    e("span", region.chr),
                    ": ",
                    e("span", `${region.start}-${region.end}`)
                ]),
                e("td", region.strand || "None"),
                e("td", e("a", {href: `/search/feature/ensembl/${region.closest_gene_id}`}, `${region.closest_gene_name} (${region.closest_gene_id})`)),
                e("td", `${region.ref_genome}.${region.ref_genome_patch || 0}`),
                e("td", e("a", {href: `/search/region/${region.id}`}, "More...")),
            ])
        )
    }
    return newTable;
}

function newPagination(pagination_id, page_data, id_prefix="",  page_query_param="page") {
    if (id_prefix != "") {
        id_prefix = `${id_prefix}_`
    }
    let stepLinks = [];
    if(page_data["has_prev_page"]) {
        stepLinks.push(e("a", {href: `?${page_query_param}=1`, id: `${id_prefix}first_link`}, t("« first")))
        stepLinks.push(t(" "))
        stepLinks.push(e("a", {href: `?${page_query_param}=${page_data["page"] - 1}`, id: `${id_prefix}prev_link`}, t("previous")))
        stepLinks.push(t(" "))
    }

    stepLinks.push(e("span", {class:"current"}, t(`Page ${page_data["page"]} of ${page_data["num_pages"]}`)))

    if(page_data["has_next_page"]) {
        stepLinks.push(t(" "))
        stepLinks.push(e("a", {href: `?${page_query_param}=${page_data["page"] + 1}`, id: `${id_prefix}next_link`}, t("next")))
        stepLinks.push(t(" "))
        stepLinks.push(e("a", {href: `?${page_query_param}=${page_data["num_pages"]}`, id: `${id_prefix}last_link`}, t("last »")))
    }

    return e("div", {class:"pagination", "id":pagination_id}, [
            e("span", {class: "step-links"}, stepLinks)
        ]
    )

}
