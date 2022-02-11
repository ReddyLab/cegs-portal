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

function emptyRegionTable(emptyString, regionID="dnaregion") {
    return e("div", {id: regionID}, t(emptyString));
}

function regionTable(regions, regionID="dnaregion") {
    newTable = e("table", {id: regionID,  class: "data-table"}, [
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

function emptyRETable(emptyString, regionID="regeffect") {
    return e("div", {id: regionID}, t(emptyString));
}

function reTable(regeffects, regionID="regeffect") {
    newTable = e("table", {id: regionID,  class: "data-table"}, [
        e("tr", [
            e("th", "Direction"),
            e("th", "Effect Size"),
            e("th", "Significance"),
            e("th", "Target Gene"),
            e("th", "Experiment"),
            e("th", "Co-regulating DHSs"),
            e("th", "Co-Sources"),
            e("th"),
        ])
    ])
    for(effect of regeffects) {
        if(effect.target_ids == 0) {
            effect.target_ids = [null];
        }
        for(target of effect.target_ids) {
            newTable.append(
                e("tr", [
                    e("td", `${effect.direction}`),
                    e("td", `${effect.effect_size}`),
                    e("td", `${effect.significance}`),
                    target == null ? e("td", "Unknown") : e("td", e("a", {href: `/search/feature/ensemble/${target}`}, target)),
                    e("td", e("a", {href: `/search/experiment/${effect.experiment.id}`}, effect.experiment.name)),
                    e("td", effect.co_regulators.length == 0 ? "None" : effect.co_regulators.map(coreg => {
                        return e("a", {href: `/search/region/${coreg}`}, `DHS: ${coreg}`)
                    })),
                    e("td", effect.co_sources.length == 0 ? "None" : effect.co_sources.map(cosrc => {
                        return e("a", {href: `/search/region/${cosrc}`}, `DHS: ${cosrc}`)
                    })),
                    e("td", e("a", {href: `/search/regeffect/${effect.id}`}, "More...")),
                ])
            )
        }
    }
    return newTable;
}

function newPagination(paginationID, pageData, idPrefix="",  pageQueryParam="page") {
    if (idPrefix != "") {
        idPrefix = `${idPrefix}_`
    }
    let stepLinks = [];
    if(pageData["has_prev_page"]) {
        stepLinks.push(e("a", {href: `?${pageQueryParam}=1`, id: `${idPrefix}first_link`}, t("« first")))
        stepLinks.push(t(" "))
        stepLinks.push(e("a", {href: `?${pageQueryParam}=${pageData["page"] - 1}`, id: `${idPrefix}prev_link`}, t("previous")))
        stepLinks.push(t(" "))
    }

    stepLinks.push(e("span", {class:"current"}, t(`Page ${pageData["page"]} of ${pageData["num_pages"]}`)))

    if(pageData["has_next_page"]) {
        stepLinks.push(t(" "))
        stepLinks.push(e("a", {href: `?${pageQueryParam}=${pageData["page"] + 1}`, id: `${idPrefix}next_link`}, t("next")))
        stepLinks.push(t(" "))
        stepLinks.push(e("a", {href: `?${pageQueryParam}=${pageData["num_pages"]}`, id: `${idPrefix}last_link`}, t("last »")))
    }

    return e("div", {class:"pagination", "id":paginationID}, [
            e("span", {class: "step-links"}, stepLinks)
        ]
    )
}

function pageLink(linkID, page, getPageFunction) {
    if (link = g(linkID)) {
        link.onclick = function(e) {
            e.preventDefault();
            getPageFunction.bind(getPageFunction)(page);
        }
    }
}

function dataPages(startPage, dataURLFunction, dataTableFunction, emptyDataTableFunction, dataFilter, noDataMessage, dataTableID, paginationID, idPrefix, pageQuery, callback) {
    let dataPage = startPage;

    let pageFunc = function(page) {
        if (page) {
            dataPage = page;
        }

        fetch(`${dataURLFunction()}&${pageQuery}=${dataPage}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Request Failed: ${response.status} ${response.statusText}`);
                }

                return response.json()
            }).then(data => {
                if(data.num_pages == 1 && data.objects.length == 0) {
                    g(dataTableID).replaceWith(emptyDataTableFunction(noDataMessage, dataTableID));
                    g(paginationID).replaceWith(e("div", {id: paginationID, display: "none"}, []));
                    return;
                }

                let filtered_data = data.objects.filter(dataFilter);
                g(dataTableID).replaceWith(dataTableFunction(filtered_data, dataTableID));
                g(paginationID).replaceWith(newPagination(paginationID, data, idPrefix));


                pageLink(`${idPrefix}_first_link`, 1, this);
                pageLink(`${idPrefix}_prev_link`, dataPage - 1, this);
                pageLink(`${idPrefix}_next_link`, dataPage + 1, this);
                pageLink(`${idPrefix}_last_link`, data.num_pages, this);

                if(callback) {
                    callback();
                }
            })
            .catch((error) => {
                console.error(error);
            });
    };

    return pageFunc.bind(pageFunc);
}
