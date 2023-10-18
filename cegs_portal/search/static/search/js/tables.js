import {e, g, t} from "./dom.js";

function emptyFeatureTable(emptyString, regionID = "dnafeature") {
    return e("div", {id: regionID}, t(emptyString));
}

function featureTable(features, regionID = "dnafeature") {
    let newTable = e("table", {id: regionID, class: "data-table"}, [
        e("tr", [
            e("th", {class: "chrom-first-end-cap chrom-light-band"}, "Name"),
            e("th", {class: "chrom-light-band"}, "Feature Type"),
            e("th", {class: "chrom-dark-band"}, "Cell Line"),
            e("th", {class: "chrom-light-band"}, "Location"),
            e("th", {class: "chrom-light-band chrom-right-centromere"},"Strand"),
            e("th", {class: "chrom-light-band chrom-left-centromere"},"Closest Gene"),
            e("th", {class: "chrom-dark-band"},"Reference Genome"),
            e("th", {class: "chrom-last-end-cap chrom-light-band"}, "Parent"),
        ]),
    ]);
    for (const feature of features) {
        let row = e("tr", {"data-href": `/search/feature/accession/${feature.accession_id}`}, [
            e("td", feature.name || "N/A"),
            e("td", feature.type),
            e("td", feature.cell_line || "None"),
            e("td", [
                e("span", feature.chr),
                ": ",
                e("span", [`${feature.start.toLocaleString()}-`, e("br"), `${feature.end.toLocaleString()}`]),
            ]),
            e("td", feature.strand || "None"),
            e(
                "td",
                {class: "closest-gene"},
                feature.closest_gene_ensembl_id
                    ? e(
                          "a",
                          {href: `/search/feature/ensembl/${feature.closest_gene_ensembl_id}`},
                          `${feature.closest_gene_name}`
                      )
                    : ""
            ),
            e("td", `${feature.ref_genome}.${feature.ref_genome_patch || 0}`),
            e(
                "td",
                feature.parent
                    ? e("a", {href: `/search/feature/accession/${feature.parent_accession_id}`}, feature.parent)
                    : "N/A"
            ),
        ]);
        row.onclick = function () {
            window.location = row.getAttribute("data-href");
        };
        newTable.append(row);
    }
    let tableContainer = e("div", {class: "container min-w-full"}, [newTable]);
    return tableContainer;
}

function emptyRETable(emptyString, regionID = "regeffect") {
    return e("div", {id: regionID}, t(emptyString));
}

function reTable(regeffects, regionID = "regeffect") {
    let newTable = e("table", {id: regionID, class: "data-table"}, [
        e("tr", [
            e("th", {class: "chrom-first-end-cap"}, "Effect Size (log2FC)"),
            e("th", "Direction"),
            e("th", "Significance (p-value)"),
            e("th", "Experiment"),
            e("th", "Target"),
            e("th", {class: "chrom-last-end-cap"},"REO Details"),
        ]),
    ]);
    for (let effect of regeffects) {
        if (effect.targets == 0) {
            effect.targets = [[null, null]];
        }
        for (const target_info of effect.targets) {
            let target_id = target_info[0];
            let target_name = target_info[1];
            let row = e("tr", {"data-href": `/search/regeffect/${effect.accession_id}`}, [
                e(
                    "td",
                    `${
                        Math.abs(effect.effect_size) > 0.0000001
                            ? effect.effect_size.toFixed(6)
                            : effect.effect_size.toExponential(2)
                    }`
                ),
                e("td", `${effect.direction}`),
                e(
                    "td",
                    `${
                        effect.significance > 0.0000001
                            ? effect.significance.toFixed(6)
                            : effect.significance.toExponential(2)
                    }`
                ),
                e("td", e("a", {href: `/search/experiment/${effect.experiment.accession_id}`}, effect.experiment.name)),
                target_id == null
                    ? e("td", "-")
                    : e("td", e("a", {href: `/search/feature/accession/${target_id}`}, target_name)),
                e(
                    "td",
                    e(
                        "a",
                        {href: `/search/regeffect/${effect.accession_id}`},
                        e(
                            "svg",
                            {
                                xmlns: "http://www.w3.org/2000/svg",
                                width: "16",
                                height: "16",
                                fill: "currentColor",
                                class: "svg-link-arrow bi bi-arrow-up-right-square-fill",
                                viewBox: "0 0 16 16",
                            },
                            e(
                                "path",
                                {
                                    "fill-rule": "evenodd",
                                    d: "M15 2a1 1 0 0 0-1-1H2a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V2zM0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V2zm5.854 8.803a.5.5 0 1 1-.708-.707L9.243 6H6.475a.5.5 0 1 1 0-1h3.975a.5.5 0 0 1 .5.5v3.975a.5.5 0 1 1-1 0V6.707l-4.096 4.096z",
                                },
                                []
                            )
                        )
                    )
                ),
            ]);
            row.onclick = function () {
                window.location = row.getAttribute("data-href");
            };
            newTable.append(row);
        }
    }
    let tableContainer = e("div", {}, [newTable]);
    return tableContainer;
}

function reTargetTable(regeffects, regionID = "regeffect") {
    let newTable = e("table", {id: regionID, class: "data-table"}, [
        e("tr", [
            e("th", {class: "chrom-first-end-cap chrom-light-band"}, "Tested Element(s)"),
            e("th", {class: "chrom-dark-band"}, "Effect Size (log2FC)"),
            e("th", {class: "chrom-light-band"}, "Direction"),
            e("th", {class: "chrom-light-band chrom-right-centromere"}, ["Significance", e("br"), "(p-value)"]),
            e("th", {class: "chrom-light-band chrom-left-centromere"}, "Experiment"),
            e("th", {class: "chrom-last-end-cap chrom-dark-band"}, "REO Details"),
        ]),
    ]);
    for (let effect of regeffects) {
        if (effect.sources == 0) {
            effect.sources = [[null, null, null]];
        }
        for (const source of effect.sources) {
            let source_id = source[0];
            let source_chrom = source[1];
            let source_loc = source[2];
            let source_type = source[3];
            let row = e("tr", {"data-href": `/search/regeffect/${effect.accession_id}`}, [
                source_id == null
                    ? e("td", "-")
                    : e(
                          "td",
                          e(
                              "a",
                              {href: `/search/feature/accession/${source_id}`},
                              `${source_type} (${source_chrom}: ${source_loc[0].toLocaleString()}-${source_loc[1].toLocaleString()}:${
                                  source_loc[2]
                              })`
                          )
                      ),
                e(
                    "td",
                    `${
                        Math.abs(effect.effect_size) > 0.0000001
                            ? effect.effect_size.toFixed(6)
                            : effect.effect_size.toExponential(2)
                    }`
                ),
                e("td", `${effect.direction}`),
                e(
                    "td",
                    `${
                        effect.significance > 0.0000001
                            ? effect.significance.toFixed(6)
                            : effect.significance.toExponential(2)
                    }`
                ),
                e("td", e("a", {href: `/search/experiment/${effect.experiment.accession_id}`}, effect.experiment.name)),
                e(
                    "td",
                    e(
                        "a",
                        {href: `/search/regeffect/${effect.accession_id}`},
                        e(
                            "svg",
                            {
                                xmlns: "http://www.w3.org/2000/svg",
                                width: "16",
                                height: "16",
                                fill: "currentColor",
                                class: "svg-link-arrow bi bi-arrow-up-right-square-fill",
                                viewBox: "0 0 16 16",
                            },
                            e(
                                "path",
                                {
                                    "fill-rule": "evenodd",
                                    d: "M15 2a1 1 0 0 0-1-1H2a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V2zM0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V2zm5.854 8.803a.5.5 0 1 1-.708-.707L9.243 6H6.475a.5.5 0 1 1 0-1h3.975a.5.5 0 0 1 .5.5v3.975a.5.5 0 1 1-1 0V6.707l-4.096 4.096z",
                                },
                                []
                            )
                        )
                    )
                ),
            ]);
            row.onclick = function () {
                window.location = row.getAttribute("data-href");
            };
            newTable.append(row);
        }
    }
    let tableContainer = e("div", {}, [newTable]);
    return tableContainer;
}

function reoNonTargetTable(regeffects, regionID = "regeffect") {
    let newTable = e("table", {id: regionID, class: "data-table"}, [
        e("tr", [
            e("th", {class: "chrom-first-end-cap"}, "Location"),
            e("th", "Effect Size"),
            e("th", "Direction"),
            e("th", "Significance"),
            e("th", "Distance from TSS"),
            e("th", "Source"),
            e("th", {class: "chrom-last-end-cap"}, "Experiment"),
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
                    e(
                        "td",
                        `${
                            Math.abs(effect.effect_size) > 0.0000001
                                ? effect.effect_size.toFixed(6)
                                : effect.effect_size.toExponential(2)
                        }`
                    ),
                    e("td", `${effect.direction}`),
                    e(
                        "td",
                        `${
                            effect.significance > 0.0000001
                                ? effect.significance.toFixed(6)
                                : effect.significance.toExponential(2)
                        }`
                    ),
                ])
            );
        }
    }
    let tableContainer = e("div", {}, [newTable]);
    return tableContainer;
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
        let [_, reoData] = reos[reoSetIdx];
        let rowClass = reoSetIdx % 2 == 0 ? "" : "bg-gray-100";
        for (const reo of reoData) {
            let features = [];
            let sources = ["Source Locations: "];
            for (let location of reo["source_locs"]) {
                sources.push(
                    e(
                        "a",
                        {href: `/search/feature/accession/${location[3]}`},
                        `${location[0]}:\u00A0${location[1].toLocaleString()}-${location[2].toLocaleString()}`
                    )
                );
                sources.push(", ");
            }

            sources.pop(); // remove that last comma

            features.push(e("div", sources));

            if (reo["target_info"].length > 0) {
                let targetGene = reo["target_info"][0];
                features.push(
                    e("div", [
                        `Target Genes: `,
                        e("a", {href: `/search/feature/ensembl/${targetGene[1]}`}, targetGene[0]),
                    ])
                );
            }

            let rowData = e("tr", {class: rowClass}, [
                e("td", features),
                e(
                    "td",
                    e("a", {href: `/search/regeffect/${reo["reo_accession_id"]}`}, [
                        e("div", `Source Locations: ${sourceLocations}`),
                        e("div", `Target Genes: ${targetGenes}`),
                    ])
                ),
                e(
                    "td",
                    reo["effect_size"] != null
                        ? e("a", {href: `/search/regeffect/${reo["reo_accession_id"]}`}, reo["effect_size"].toFixed(6))
                        : ""
                ),
                e("td", e("a", {href: `/search/regeffect/${reo["reo_accession_id"]}`}, reo["sig"].toFixed(6))),
                e("td", e("a", {href: `/search/regeffect/${reo["reo_accession_id"]}`}, reo["p_value"].toFixed(6))),
            ]);

            if (reo == reoData[0]) {
                rowData.append(
                    e(
                        "td",
                        {rowspan: `${reoData.length}`},
                        e("a", {href: `/search/experiment/${reo["expr_accession_id"]}`}, reo["expr_name"])
                    )
                );
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
    reoNonTargetTable,
    sigReoTable,
};
