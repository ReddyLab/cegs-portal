import {g, rc, t} from "../dom.js";

function getDownload(url, filename) {
    rc(g("dataDownloadLink"), t("Getting your data..."));

    let request = {
        method: "GET",
        credentials: "include",
        mode: "same-origin",
    };

    fetch(url, request)
        .then((response) => {
            if (!response.ok) {
                throw `Data request failed. Http Status: ${response.status}`;
            }
            return response.blob();
        })
        .then((blob) => {
            // The following code that initiates a download is
            // from https://stackoverflow.com/a/56923508
            var fileURL = URL.createObjectURL(blob);

            // create <a> tag dinamically
            var fileLink = document.createElement("a");
            fileLink.href = fileURL;

            // it forces the name of the downloaded file
            fileLink.download = filename;

            // triggers the click event
            fileLink.click();
            rc(g("dataDownloadLink"), t(""));
        })
        .catch((err) => {
            rc(g("dataDownloadLink"), t("Sorry, something went wrong"));
            console.log(err);
        });
}

function getDownloadRegions(facets, chromo, lower, upper, assembly) {
    let facet_queries = facets.map((f) => `f=${f}`).join("&");
    if (facet_queries.length > 0) {
        facet_queries += "&";
    }
    let url = `/exp_data/location?region=chr${chromo}:${lower}-${upper}&${facet_queries}datasource=both&assembly=${assembly}`;

    getDownload(url, `chr${chromo}_${lower}_${upper}_${assembly}`);
}

export function downloadRegionsSetup(state, assembly) {
    let dataDownloadAll = g("dataDownloadAll");
    dataDownloadAll.addEventListener(
        "click",
        () => {
            const facetCheckboxes = document.querySelectorAll("[name=facetfield] input[type=checkbox]");
            let checkedFacets = Array.from(facetCheckboxes) // Convert checkboxes to an array to use filter and map.
                .filter((i) => i.checked) // Use Array.filter to remove unchecked checkboxes.
                .map((i) => i.id);

            let location = state.g("location");
            getDownloadRegions(checkedFacets, location.chr, location.start, location.end, assembly);
        },
        false
    );
}
