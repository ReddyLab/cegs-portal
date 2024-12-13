import {g, rc, t} from "../dom.js";
import {getDownloadRegions} from "../exp_viz/downloads.js";

export function downloadDataSetup(csrfToken) {
    let dataDownloadInput = g("dataDownloadInput");
    dataDownloadInput.addEventListener(
        "change",
        () => {
            let experimentListItems = document.getElementsByClassName("experiment-list-item");
            if (experimentListItems.length == 0) {
                rc(g("dataDownloadLink"), t("Please select at least one experiment."));
                return;
            }

            getDownloadRegions(
                null,
                dataDownloadInput,
                Array.from(experimentListItems, (item) => item.dataset.accession),
                csrfToken,
            );
        },
        false,
    );

    let dataDownloadInputCollection = g("dataDownloadInput-collections");
    dataDownloadInputCollection.addEventListener(
        "change",
        () => {
            let experimentListItems = document.getElementsByClassName("experiment-list-item");
            if (experimentListItems.length == 0) {
                rc(g("dataDownloadLink-collections"), t("Please select at least one experiment."));
                return;
            }

            getDownloadRegions(
                null,
                dataDownloadInputCollection,
                Array.from(experimentListItems, (item) => item.dataset.accession),
                csrfToken,
            );
        },
        false,
    );
}
