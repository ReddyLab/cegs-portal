import {e, g, rc, t} from "../dom.js";

function getDownload(url, body) {
    rc(g("dataDownloadLink"), t("Getting your data..."));

    let request = {
        method: "POST",
        credentials: "include",
        mode: "same-origin",
        body: body,
    };

    let dlDataWorker;
    fetch(url, request)
        .then((response) => response.json())
        .then((json) => {
            dlDataWorker = new Worker("/static/search/js/exp_viz/downloadStatusWorker.js");
            dlDataWorker.onmessage = (statusData) => {
                let status = statusData.data;
                if (status == "ready") {
                    let filePath = json["file location"].split("/");
                    filePath = filePath[filePath.length - 1];
                    if (filePath.length > 30) {
                        filePath =
                            filePath.substring(0, 15) + "…" + filePath.substring(filePath.length - 15, filePath.length);
                    }
                    rc(
                        g("dataDownloadLink"),
                        e("a", {href: json["file location"], class: "text-blue-700"}, t(filePath))
                    );
                } else if (status == "in_preparation") {
                    // keep spinning
                } else {
                    rc(g("dataDownloadLink"), t("Sorry, something went wrong"));
                }
            };
            dlDataWorker.postMessage(json["file progress"]);
        })
        .catch((err) => {
            rc(g("dataDownloadLink"), t("Sorry, something went wrong"));
            console.log(err);
        });
}

export function getDownloadRegions(facets, dataDownloadInput, exprAccessionIDs, csrfToken) {
    if (dataDownloadInput.files.length != 1) {
        return;
    }

    if (!Array.isArray(exprAccessionIDs)) {
        exprAccessionIDs = [exprAccessionIDs];
    }
    let exprs = exprAccessionIDs.map((a) => `expr=${a}`).join("&");
    let url = `/exp_data/request?${exprs}&datasource=both`;
    let requestBody = new FormData();
    requestBody.set("regions", dataDownloadInput.files[0]);
    requestBody.set("csrfmiddlewaretoken", csrfToken);
    if (facets) {
        requestBody.set("facets", JSON.stringify(facets));
    }

    getDownload(url, requestBody);
}

export function getDownloadAll(facets, exprAccessionID, csrfToken) {
    let url = `/exp_data/request?expr=${exprAccessionID}&datasource=everything`;
    let requestBody = new FormData();
    requestBody.set("csrfmiddlewaretoken", csrfToken);
    requestBody.set("facets", JSON.stringify(facets));

    getDownload(url, requestBody);
}
