importScripts("./vizUtils.js");

onmessage = function (e) {
    const data = e.data.data;
    const countFilters = e.data.countFilters;

    let sourceFilter = countFilters[0];
    let targetFilter = countFilters[1];
    let newData = shallowClone(data);

    for (let cIdx = 0; cIdx < data.length; cIdx++) {
        newData[cIdx].source_intervals = data[cIdx].source_intervals.filter((inter) => {
            return inter.count >= sourceFilter[0] && inter.count <= sourceFilter[1];
        });
        newData[cIdx].target_intervals = data[cIdx].target_intervals.filter((inter) => {
            return inter.count >= targetFilter[0] && inter.count <= targetFilter[1];
        });
    }

    postMessage(newData);
};
