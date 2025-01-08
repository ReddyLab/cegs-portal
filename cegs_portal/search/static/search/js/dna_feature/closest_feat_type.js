import {g} from "../dom.js";

let closestFeaturesURL = function (feature_accession_id, facetQuery) {
    return `/search/feature/accession/${feature_accession_id}/closest${facetQuery !== "" ? "?" + facetQuery : ""}`;
};

export function closestFeatureTypeSetup(feature_accession_id) {
    let typeCheckboxes = g("closest-types");
    if (typeCheckboxes == null) {
        return;
    }

    typeCheckboxes = typeCheckboxes.querySelectorAll("input[type=checkbox]");

    typeCheckboxes.forEach((checkbox) => {
        checkbox.checked = false; // reset the checkboxes after a page reload.
        checkbox.addEventListener("change", (_event) => {
            let facetQuery = Array.from(typeCheckboxes) // Convert checkboxes to an array to use filter and map.
                .filter((i) => i.checked) // Use Array.filter to remove unchecked checkboxes.
                .map((i) => `type=${i.id}`)
                .join("&");

            htmx.ajax("GET", closestFeaturesURL(feature_accession_id, facetQuery), "#closest-features-table").catch(
                (err) => {
                    console.error(err.message);
                },
            );
        });
    });
}
