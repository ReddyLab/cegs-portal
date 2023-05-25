import {e, g, t} from "./dom.js";

function emptyFeatureTable(emptyString, regionID = "dnafeature") {
    return e("div", {id: regionID}, t(emptyString));
}

function featureTable(features, regionID = "dnafeature") {
    let newTable = e("table", {id: regionID, class: "data-table"}, [
        e("tr", [
            e("th", "ID"),
            e("th", "Name"),
            e("th", "Feature Type"),
            e("th", "Cell Line"),
            e("th", "Location"),
            e("th", "Strand"),
            e("th", "Closest Gene"),
            e("th", "Reference Genome"),
        ]),
    ]);
    for (const feature of features) {
        newTable.append(
            e("tr", {class: "data-row"}, [
                e("td", e("a", {href: `/search/feature/accession/${feature.accession_id}`}, feature.accession_id)),
                e("td", feature.name || "N/A"),
                e("td", feature.type),
                e("td", feature.cell_line || "None"),
                e("td", [e("span", feature.chr), ": ", e("span", `${feature.start}-${feature.end}`)]),
                e("td", feature.strand || "None"),
                e(
                    "td",
                    feature.closest_gene_ensembl_id
                        ? e(
                              "a",
                              {href: `/search/feature/ensembl/${feature.closest_gene_ensembl_id}`},
                              `${feature.closest_gene_name} (${feature.closest_gene_ensembl_id})`
                          )
                        : "N/A"
                ),
                e("td", `${feature.ref_genome}.${feature.ref_genome_patch || 0}`),
            ])
        );
    }
    return newTable;
}

function emptyRETable(emptyString, regionID = "regeffect") {
    return e("div", {id: regionID}, t(emptyString));
}

function reTable(regeffects, regionID = "regeffect") {
    let newTable = e("table", {id: regionID, class: "data-table"}, [
        e("tr", [
            e("th", "ID"),
            e("th", "Effect Size"),
            e("th", "Direction"),
            e("th", "Significance"),
            e("th", "Experiment"),
            e("th", "Target"),
        ]),
    ]);
    for (let effect of regeffects) {
        if (effect.target_ids == 0) {
            effect.target_ids = [null];
        }
        for (const target of effect.target_ids) {
            newTable.append(
                e("tr", [
                    e("td", e("a", {href: `/search/regeffect/${effect.accession_id}`}, effect.accession_id)),
                    e("td", `${effect.effect_size.toExponential(3)}`),
                    e("td", `${effect.direction}`),
                    e("td", `${effect.significance.toExponential(3)}`),
                    e(
                        "td",
                        e("a", {href: `/search/experiment/${effect.experiment.accession_id}`}, effect.experiment.name)
                    ),
                    target == null
                        ? e("td", "-")
                        : e("td", e("a", {href: `/search/feature/ensemble/${target}`}, target)),
                ])
            );
        }
    }
    return newTable;
}

function reTargetTable(regeffects, regionID = "regeffect") {
    let newTable = e("table", {id: regionID, class: "data-table"}, [
        e("tr", [
            e("th", "ID"),
            e("th", "Effect Size"),
            e("th", "Direction"),
            e("th", "Significance"),
            e("th", "Experiment"),
            e("th", "Source"),
        ]),
    ]);
    for (let effect of regeffects) {
        if (effect.source_ids == 0) {
            effect.source_ids = [null];
        }
        for (const source of effect.source_ids) {
            newTable.append(
                e("tr", [
                    e("td", e("a", {href: `/search/regeffect/${effect.accession_id}`}, effect.accession_id)),
                    e("td", `${effect.effect_size.toExponential(3)}`),
                    e("td", `${effect.direction}`),
                    e("td", `${effect.significance.toExponential(3)}`),
                    e(
                        "td",
                        e("a", {href: `/search/experiment/${effect.experiment.accession_id}`}, effect.experiment.name)
                    ),
                    source == null
                        ? e("td", "-")
                        : e("td", e("a", {href: `/search/feature/ensemble/${source}`}, source)),
                ])
            );
        }
    }
    return newTable;
}

function sigReoTable(reos, regionID = "sig-reg-effects") {
    let newTable = e("table", {id: regionID, class: "data-table"}, [
        e("tr", [
            e("th", "Enahncer/Gene"),
            e("th", "Effect Size"),
            e("th", "Significance"),
            e("th", "Raw p-value"),
            e("th", "Experiment"),
        ]),
    ]);
    for (const reoSetIdx in reos) {
        let [accessionIds, reoData] = reos[reoSetIdx];
        let rowClass = reoSetIdx % 2 == 0 ? "" : "bg-gray-100";
        for (const reo of reoData) {
            let sourceLocations = reo["source_locs"]
                .map((location) => `${location[0]}:${location[1].toLocaleString()}-${location[2].toLocaleString()}`)
                .join(", ");
            let targetGenes = reo["target_info"].map((gene) => gene[0]).join(", ");
            let rowData = e("tr", {class: rowClass}, [
                e(
                    "td",
                    e("a", {href: `/search/regeffect/${reo["reo_accesion_id"]}`}, [
                        e("div", `Source Locations: ${sourceLocations}`),
                        e("div", `Target Genes: ${targetGenes}`),
                    ])
                ),
                e("td", reo["effect_size"] != null ? reo["effect_size"].toPrecision(6) : ""),
                e("td", reo["sig"].toPrecision(6)),
                e("td", reo["p_value"].toPrecision(6)),
            ]);

            if (reo == reoData[0]) {
                rowData.append(e("td", {rowspan: `${reoData.length}`}, accessionIds[0]));
            }
            newTable.append(rowData);
        }
    }
    return newTable;
}

function newPagination(paginationID, pageData, idPrefix = "", pageQueryParam = "page") {
    if (idPrefix != "") {
        idPrefix = `${idPrefix}_`;
    }
    let stepLinks = [];
    if (pageData["has_prev_page"]) {
        stepLinks.push(e("a", {href: `?${pageQueryParam}=1`, id: `${idPrefix}first_link`}, t("« first")));
        stepLinks.push(t(" "));
        stepLinks.push(
            e("a", {href: `?${pageQueryParam}=${pageData["page"] - 1}`, id: `${idPrefix}prev_link`}, t("previous"))
        );
        stepLinks.push(t(" "));
    }

    stepLinks.push(e("span", {class: "current"}, t(`Page ${pageData["page"]} of ${pageData["num_pages"]}`)));

    if (pageData["has_next_page"]) {
        stepLinks.push(t(" "));
        stepLinks.push(
            e("a", {href: `?${pageQueryParam}=${pageData["page"] + 1}`, id: `${idPrefix}next_link`}, t("next"))
        );
        stepLinks.push(t(" "));
        stepLinks.push(
            e("a", {href: `?${pageQueryParam}=${pageData["num_pages"]}`, id: `${idPrefix}last_link`}, t("last »"))
        );
    }

    return e("div", {class: "pagination", id: paginationID}, [e("span", {class: "step-links"}, stepLinks)]);
}

function pageLink(linkID, page, getPageFunction) {
    let link = g(linkID);
    if (link) {
        link.onclick = function (e) {
            e.preventDefault();
            getPageFunction.bind(getPageFunction)(page);
        };
    }
}

function dataPages(
    startPage,
    dataURLFunction,
    dataTableFunction,
    emptyDataTableFunction,
    dataFilter,
    noDataMessage,
    dataTableID,
    paginationID,
    idPrefix,
    pageQuery,
    callback
) {
    let dataPage = startPage;

    let pageFunc = function (page) {
        if (page) {
            dataPage = page;
        }

        fetch(`${dataURLFunction()}&${pageQuery}=${dataPage}`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Request Failed: ${response.status} ${response.statusText}`);
                }

                return response.json();
            })
            .then((data) => {
                if (data.num_pages == 1 && data.object_list.length == 0) {
                    g(dataTableID).replaceWith(emptyDataTableFunction(noDataMessage, dataTableID));
                    g(paginationID).replaceWith(e("div", {id: paginationID, display: "none"}, []));
                    return;
                }

                let filtered_data = data.object_list.filter(dataFilter);
                g(dataTableID).replaceWith(dataTableFunction(filtered_data, dataTableID));
                g(paginationID).replaceWith(newPagination(paginationID, data, idPrefix, pageQuery));

                pageLink(`${idPrefix}_first_link`, 1, this);
                pageLink(`${idPrefix}_prev_link`, dataPage - 1, this);
                pageLink(`${idPrefix}_next_link`, dataPage + 1, this);
                pageLink(`${idPrefix}_last_link`, data.num_pages, this);

                if (callback) {
                    callback();
                }
            })
            .catch((error) => {
                console.error(error);
            });
    };

    return pageFunc.bind(pageFunc);
}

export {
    pageLink,
    dataPages,
    newPagination,
    featureTable,
    emptyFeatureTable,
    emptyRETable,
    reTable,
    reTargetTable,
    sigReoTable,
};
