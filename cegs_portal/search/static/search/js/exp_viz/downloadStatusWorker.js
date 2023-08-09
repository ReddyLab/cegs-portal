onmessage = function (statusURLData) {
    let getStatus = async (url, backoff) => {
        try {
            const response = await fetch(url);
            const json = await response.json();
            let progress = json["file progress"];
            postMessage(progress);
            if (progress == "in_preparation") {
                setTimeout(() => getStatus(url, Math.min(backoff * 2, 6000)), backoff);
            }
        } catch (err) {
            console.log(err);
        }
    };

    let statusURL = statusURLData.data;
    getStatus(statusURL, 500);
};
