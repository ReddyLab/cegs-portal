import {g} from "../dom.js";
import {getDownloadRegions} from "../exp_viz/downloads.js";

export function downloadDataSetup(csrfToken) {
    let dataDownloadInput = g("dataDownloadInput");
    dataDownloadInput.addEventListener(
        "change",
        () => getDownloadRegions(null, dataDownloadInput, JSON.parse(g("experiment-id-list").textContent), csrfToken),
        false
    );
}
