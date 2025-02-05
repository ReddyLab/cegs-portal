export function getJson(path) {
    let options = {
        credentials: "include",
        headers: {
            Accept: "application/json",
        },
    };

    if (arguments.length == 2) {
        options["signal"] = arguments[1];
    }

    return fetch(path, options).then((response) => {
        if (!response.ok) {
            throw new Error(`${path} fetch failed: ${response.status} ${response.statusText}`);
        }

        return response.json();
    });
}

export function postJson(path, body, csrfToken) {
    let init = {
        method: "POST",
        credentials: "include",
        body: body,
        headers: {
            Accept: "application/json",
        },
        mode: "same-origin",
    };

    if (csrfToken !== undefined) {
        init.headers["X-CSRFToken"] = csrfToken;
    }

    return fetch(path, init).then((response) => {
        if (!response.ok) {
            throw new Error(`${path} fetch failed: ${response.status} ${response.statusText}`);
        }

        return response.json();
    });
}
