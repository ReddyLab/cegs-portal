import {g} from "../dom.js";
import {addDragListeners, addSelectListeners} from "./drag_drop.js";

function experimentListURL(queries) {
    let queryString = queries.map((query) => `${query[0]}=${query[1]}`).join("&");

    return `experiment${queryString !== "" ? `?${queryString}` : ""}`;
}

function allQueriesExcept(queryParams, exception) {
    let facets = [];
    for (var query of queryParams) {
        if (query[0] === exception) {
            continue;
        }
        facets.push(query);
    }
    return facets;
}

function facetQueries(facetCheckboxes, targetParam) {
    let facets = [];
    for (var facet of Array.from(facetCheckboxes)) {
        if (facet.checked) {
            facets.push([targetParam, facet.id]);
        }
    }
    return facets;
}

function _facetFilterSetup(facetDivId, queryParam, targetID) {
    let facetCheckboxes = g(facetDivId).querySelectorAll("input[type=checkbox]");
    let queryParams = new URLSearchParams(window.location.search);
    let currentlySelectedFacets = queryParams.getAll(queryParam);

    facetCheckboxes.forEach((checkbox) => {
        checkbox.checked = currentlySelectedFacets.includes(checkbox.id); // reset the checkboxes after a page reload.
        checkbox.addEventListener("change", (_event) => {
            let queryParams = new URLSearchParams(window.location.search);
            let queries = [...allQueriesExcept(queryParams, queryParam), ...facetQueries(facetCheckboxes, queryParam)];
            let url = experimentListURL(queries);

            // We don't want to mess with the state when using this from a modal
            // on an experiment/multi-experiment page
            if (window.location.pathname === "/search/experiment") {
                window.history.pushState({}, document.title, url);
            }

            htmx.ajax("GET", `/search/${url}`, targetID)
                .then(() => {
                    addDragListeners();
                    addSelectListeners();
                })
                .catch((err) => {
                    console.error(err.message);
                });
        });
    });
}
export function facetFilterSetup() {
    _facetFilterSetup("categorical-facets", "facet", "#experiment-list");
    _facetFilterSetup("categorical-collection-facets", "coll_facet", "#experiment-collection-list");
}
