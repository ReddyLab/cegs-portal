export function getJson(path) {
    return fetch(path, {credentials: "include"}).then((response) => {
        if (!response.ok) {
            throw new Error(`${path} fetch failed: ${response.status} ${response.statusText}`);
        }

        return response.json();
    });
}

export function postJson(path, body) {
    let init = {
        method: "POST",
        credentials: "include",
        body: body,
        headers: {
            Accept: "application/json",
        },
        mode: "same-origin",
    };

    return fetch(path, init).then((response) => {
        if (!response.ok) {
            throw new Error(`${path} fetch failed: ${response.status} ${response.statusText}`);
        }

        return response.json();
    });
}
