onmessage = function (statusURLData) {
    let statusURL = statusURLData.data;
    let getStatus = (url, tries) => {
        return fetch(url)
            .then((response) => response.json())
            .then((json) => {
                let progress = json["file progress"];
                postMessage(progress);
                if (progress == "in_preparation") {
                    setTimeout(getStatus(url, tries - 1), 500);
                }
            })
            .catch((err) => {
                console.log(err);
            });
    };
    Promise.all([getStatus(statusURL, 5)]);
};
