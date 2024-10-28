import {e, g, rc} from "../dom.js";
import {getJson} from "../files.js";
import {addDragListeners, addSelectListeners} from "./drag_drop.js";

let controller;

let experimentListURL = function (facetQuery) {
    return `experiment?${facetQuery !== "" ? "&" + facetQuery : ""}`;
};

export function facetFilterSetup() {
    let facetCheckboxes = g("categorical-facets").querySelectorAll("input[type=checkbox]");

    let queryParams = new URLSearchParams(window.location.search);
    let experimentFacets = queryParams.getAll("facet");
    facetCheckboxes.forEach((checkbox) => {
        checkbox.checked = experimentFacets.includes(checkbox.id); // reset the checkboxes after a page reload.
        checkbox.addEventListener("change", (_event) => {
            if (controller !== undefined) {
                controller.abort();
            }

            let facetQuery = Array.from(facetCheckboxes) // Convert checkboxes to an array to use filter and map.
                .filter((i) => i.checked) // Use Array.filter to remove unchecked checkboxes.
                .map((i) => `facet=${i.id}`)
                .join("&");

            window.history.pushState({}, document.title, experimentListURL(facetQuery));

            controller = new AbortController();

            getJson(`/search/experiment?${facetQuery}&accept=application/json`, controller.signal)
                .then((response_json) => {
                    let experimentListNode = g("experiment-list");
                    let experimentNodes = response_json["experiments"].map((expr) => {
                        return e(
                            "a",
                            {
                                href: `/search/experiment/${expr.accession_id}`,
                                class: "exp-list-content-container-link experiment-summary",
                                "data-accession": expr.accession_id,
                                "data-name": expr.name,
                            },
                            e(
                                "div",
                                {
                                    class: "container",
                                },
                                [
                                    e("div", {class: "flex justify-between"}, [
                                        e("div", {class: "exp-name"}, expr.name),
                                        e(
                                            "div",
                                            {
                                                class: "select-experiment font-bold text-2xl",
                                                title: "Select Experiment",
                                                "data-accession": expr.accession_id,
                                                "data-name": expr.name,
                                            },
                                            "＋",
                                        ),
                                    ]),
                                    e("div", expr.description),
                                    e("div", {class: "flex justify-between"}, [
                                        e(
                                            "div",
                                            {class: "cell-lines"},
                                            `Cell Lines: ${expr.biosamples.map((b) => b.cell_line).join(", ")}`,
                                        ),
                                        e("div", {class: "accession-id"}, expr.accession_id),
                                    ]),
                                ],
                            ),
                        );
                    });
                    rc(experimentListNode, experimentNodes);

                    addDragListeners();
                    addSelectListeners();
                })
                .catch((err) => {
                    if (err.name != "AbortError") {
                        console.error(err.message);
                    }
                });
        });
    });
}
