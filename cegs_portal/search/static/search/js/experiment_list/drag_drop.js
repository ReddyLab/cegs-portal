import {a, cc, e, g, rc, t} from "../dom.js";

function closeButton() {
    return e(
        "span",
        {class: "close-button inline-block mr-2"},
        e(
            "svg",
            {
                xmlns: "http://www.w3.org/2000/svg",
                width: "24",
                height: "24",
                fill: "currentColor",
                class: "bi bi-x-lg",
                viewBox: "0 0 16 16",
            },
            e(
                "path",
                {
                    d: "M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z",
                },
                []
            )
        )
    );
}

function addRemoveListener(node, accession) {
    node.addEventListener("click", (evt) => {
        g(`${accession}-list-item`).remove();

        let experimentListItems = document.getElementsByClassName("experiment-list-item");
        if (experimentListItems.length == 0) {
            let noExperiments = e(
                "div",
                {class: "italic", id: "no-selected-experiments"},
                "Drag experiments here to select"
            );
            g("selected-experiment-list").before(noExperiments);

            let dataDownloadLink = g("dataDownloadLink");
            if (dataDownloadLink) {
                rc(dataDownloadLink, t("Please select at least one experiment."));
            }

            let experiments_link = g("experiments-link");
            if (experiments_link) {
                rc(experiments_link, t("Please select at least one experiment."));
            }
        }
    });
}

function addToExperimentList(experimentItemText) {
    let wrapper = e("template");
    wrapper.innerHTML = experimentItemText;
    let experimentItem = wrapper.content.firstChild;
    let selectedExperimentList = g("selected-experiment-list");

    // Don't add an experiment more than once
    let newAccession = experimentItem.dataset.accession;
    let experimentListItems = document.getElementsByClassName("experiment-list-item");
    let accessionIds = Array.from(experimentListItems, (item) => item.dataset.accession);
    if (accessionIds.includes(newAccession)) {
        return;
    } else {
        accessionIds.push(newAccession);
    }

    let close = closeButton();
    addRemoveListener(close, newAccession);
    experimentItem.before(close);
    a(selectedExperimentList, e("div", {id: `${newAccession}-list-item`}, [close, experimentItem]));

    let dataDownloadLink = g("dataDownloadLink");
    if (dataDownloadLink) {
        cc(dataDownloadLink);
    }

    let noExperiments = g("no-selected-experiments");
    if (noExperiments) {
        noExperiments.remove();
    }

    let experiments_link = g("experiments-link");
    if (experiments_link) {
        rc(
            experiments_link,
            e(
                "a",
                {
                    href: `experiments?${accessionIds.map((id) => `exp=${id}`).join("&")}`,
                    class: "expr-list-link",
                },
                `Analyze ${accessionIds.length} Selected ${
                    accessionIds.length > 1 ? "Experiments together" : "Experiment"
                }`
            )
        );
    }
}

export function addDropListeners() {
    let selectedExperiments = g("selected-experiments");
    selectedExperiments.addEventListener("dragover", (evt) => {
        evt.preventDefault();
        evt.dataTransfer.dropEffect = "copy";
    });
    selectedExperiments.addEventListener("drop", (evt) => {
        evt.preventDefault();
        addToExperimentList(evt.dataTransfer.getData("text/html"));
    });
}

function experimentListItemText(name, accession) {
    return `<span class="experiment-list-item" data-accession="${accession}"><span class="exp-name">${name}</span> <span class="accession-id">${accession}</span></span>`;
}

export function addSelectListeners() {
    let experimentSummaries = document.getElementsByClassName("select-experiment");

    for (let summary of experimentSummaries) {
        summary.addEventListener("click", (evt) => {
            evt.preventDefault();
            addToExperimentList(experimentListItemText(evt.target.dataset.name, evt.target.dataset.accession));
        });
    }
}

export function addDragListeners() {
    let experimentSummaries = document.getElementsByClassName("experiment-summary");

    for (let summary of experimentSummaries) {
        summary.addEventListener("dragstart", (evt) => {
            evt.dataTransfer.setData("text/plain", `${evt.target.dataset.name} (${evt.target.dataset.accession})`);
            evt.dataTransfer.setData(
                "text/html",
                experimentListItemText(evt.target.dataset.name, evt.target.dataset.accession)
            );
        });
    }
}
