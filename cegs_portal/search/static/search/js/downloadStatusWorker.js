onmessage = function (statusURLData) {
    let getStatus = async (url, tries) => {
        try {
            const response = await fetch(url);
            const json = await response.json();
            let progress = json["file progress"];
            postMessage(progress);
            if (progress == "in_preparation") {
                setTimeout(getStatus(url, tries - 1), 500);
            }
        } catch (err) {
            console.log(err);
        }
    };

    let statusURL = statusURLData.data;
    getStatus(statusURL, 5);
};
