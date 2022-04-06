export function getJson(path) {
   return fetch(path)
        .then(response => {
            if (!response.ok) {
                throw new Error(`${path} fetch failed: ${response.status} ${response.statusText}`);
            }

            return response.json();
        });
}
