importScripts("./vizUtils.js");

onmessage = function (e) {
    const data = e.data.data;
    const countFilters = e.data.countFilters;

    let sourceFilter = countFilters[0];
    let targetFilter = countFilters[1];
    let newData = shallowClone(data);

    for (let cIdx = 0; cIdx < data.chromosomes.length; cIdx++) {
        newData.chromosomes[cIdx].target_intervals = data.chromosomes[cIdx].target_intervals.filter(inter => {
            return inter.targets.length >= targetFilter[0] && inter.targets.length <= targetFilter[1];
        });
        newData.chromosomes[cIdx].source_intervals = data.chromosomes[cIdx].source_intervals.filter(inter => {
            return inter.sources.length >= sourceFilter[0] && inter.sources.length <= sourceFilter[1];
        });
    }

    postMessage(newData);
}
