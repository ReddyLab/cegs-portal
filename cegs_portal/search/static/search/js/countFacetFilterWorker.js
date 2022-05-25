importScripts("./vizUtils.js");

onmessage = function (e) {
    const data = e.data.data;
    const countFilters = e.data.countFilters;

    let ccreFilter = countFilters[0];
    let geneFilter = countFilters[1];
    let newData = shallowClone(data);

    for (let cIdx = 0; cIdx < data.chromosomes.length; cIdx++) {
        newData.chromosomes[cIdx].gene_intervals = data.chromosomes[cIdx].gene_intervals.filter(inter => {
            return inter.genes.length >= geneFilter[0] && inter.genes.length <= geneFilter[1];
        });
        newData.chromosomes[cIdx].ccre_intervals = data.chromosomes[cIdx].ccre_intervals.filter(inter => {
            return inter.ccres.length >= ccreFilter[0] && inter.ccres.length <= ccreFilter[1];
        });
    }

    postMessage(newData);
}
