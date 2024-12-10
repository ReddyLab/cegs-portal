import {g} from "../dom.js";
import {addDragListeners, addSelectListeners} from "./drag_drop.js";

let experimentListURL = function (facetCheckboxes) {
    let facetQuery = Array.from(facetCheckboxes) // Convert checkboxes to an array to use filter and map.
        .filter((i) => i.checked) // Use Array.filter to remove unchecked checkboxes.
        .map((i) => `facet=${i.id}`)
        .join("&");

    return `experiment?${facetQuery !== "" ? facetQuery : ""}`;
};

export function facetFilterSetup() {
    let facetCheckboxes = g("categorical-facets").querySelectorAll("input[type=checkbox]");

    let queryParams = new URLSearchParams(window.location.search);
    let experimentFacets = queryParams.getAll("facet");
    facetCheckboxes.forEach((checkbox) => {
        checkbox.checked = experimentFacets.includes(checkbox.id); // reset the checkboxes after a page reload.
        checkbox.addEventListener("change", (_event) => {
            let url = experimentListURL(facetCheckboxes);

            // We don't want to mess with the state when using this from a modal
            // on an experiment/multi-experiment page
            if (window.location.pathname === "/search/experiment") {
                window.history.pushState({}, document.title, url);
            }

            htmx.ajax("GET", `/search/${url}`, "#experiment-list")
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
