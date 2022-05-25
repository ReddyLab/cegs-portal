importScripts("./vizUtils.js");

onmessage = function(e) {
    const data = e.data.data
    const effectSizeRange = e.data.continuousFilters[0];
    const sigRange = e.data.continuousFilters[1];

    let newData = shallowClone(data);

    for (let cIdx = 0; cIdx < data.chromosomes.length; cIdx++) {
        const gene_intervals = data.chromosomes[cIdx].gene_intervals;
        for (let iIdx = 0; iIdx < gene_intervals.length; iIdx++) {
            const genes = gene_intervals[iIdx].genes;
            let newGenes = [];
            for (let gIdx = 0; gIdx < genes.length; gIdx++) {
                let regEffects = genes[gIdx][0];
                let contFacetCount = regEffects[0];
                let newRegEffects = Array(regEffects.length)
                newRegEffects[0] = contFacetCount;
                let newREIdx = 1;
                for (let rIdx = 1; rIdx < regEffects.length;) {
                    const discFacetCount = regEffects[rIdx];
                    const effectSize = regEffects[rIdx + 1 + discFacetCount];
                    const significance = regEffects[rIdx + 1 + discFacetCount + 1];

                    if ((effectSize >= effectSizeRange[0] && effectSize <= effectSizeRange[1]) &&
                        (significance >= sigRange[0] && significance <= sigRange[1])) {
                            newRegEffects[newREIdx++] = discFacetCount;
                            for (let dIdx = 0; dIdx < discFacetCount; dIdx++, newREIdx++) {
                                newRegEffects[newREIdx] = regEffects[rIdx + 1 + dIdx];
                            }
                            newRegEffects[newREIdx++] = effectSize;
                            newRegEffects[newREIdx++] = significance;
                    }
                    rIdx += 1 + discFacetCount + contFacetCount;
                }

                newRegEffects.length = newREIdx;
                if (newRegEffects.length > 1) {
                    newGenes.push([newRegEffects, genes[gIdx][1]]);
                }
            }
            newData.chromosomes[cIdx].gene_intervals[iIdx] = {
                start: data.chromosomes[cIdx].gene_intervals[iIdx].start,
                genes: newGenes
            };
        }

        const ccre_intervals = data.chromosomes[cIdx].ccre_intervals;
        for (let iIdx = 0; iIdx < ccre_intervals.length; iIdx++) {
            const ccres = ccre_intervals[iIdx].ccres;
            let newcCREs = [];
            for (let gIdx = 0; gIdx < ccres.length; gIdx++) {
                let regEffects = ccres[gIdx][0];
                let contFacetCount = regEffects[0];
                let newRegEffects = Array(regEffects.length)
                newRegEffects[0] = contFacetCount;
                let newREIdx = 1;
                for (let rIdx = 1; rIdx < regEffects.length;) {
                    const discFacetCount = regEffects[rIdx];
                    const effectSize = regEffects[rIdx + 1 + discFacetCount];
                    const significance = regEffects[rIdx + 1 + discFacetCount + 1];

                    if ((effectSize >= effectSizeRange[0] && effectSize <= effectSizeRange[1]) &&
                        (significance >= sigRange[0] && significance <= sigRange[1])) {
                            newRegEffects[newREIdx++] = discFacetCount;
                            for (let dIdx = 0; dIdx < discFacetCount; dIdx++, newREIdx++) {
                                newRegEffects[newREIdx] = regEffects[rIdx + 1 + dIdx];
                            }
                            newRegEffects[newREIdx++] = effectSize;
                            newRegEffects[newREIdx++] = significance;
                    }
                    rIdx += 1 + discFacetCount + contFacetCount;
                }

                newRegEffects.length = newREIdx;
                if (newRegEffects.length > 1) {
                    newcCREs.push([newRegEffects, ccres[gIdx][1]]);
                }
            }
            newData.chromosomes[cIdx].ccre_intervals[iIdx] = {
                start: data.chromosomes[cIdx].ccre_intervals[iIdx].start,
                ccres: newcCREs
            };
        }
    }

    postMessage(newData);
}
