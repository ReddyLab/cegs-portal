importScripts("./vizUtils.js");

onmessage = function(e) {
    const data = e.data.data;
    const discreteFacetIds = e.data.facetValues;
    const effectSizeInterval = e.data.effectSizeInterval;
    const sigInterval = e.data.sigInterval;

    if (discreteFacetIds.length == 0) {
        postMessage({data, effectSizeInterval, sigInterval});
        return;
    }

    let newData = shallowClone(data);

    let geneFacets = newData.facets
        .filter(f => f.type == "FacetType.DISCRETE" && f.coverage.includes("gene"))
        .map(f => Object.keys(f.values).map(k => Number.parseInt(k)));

    let cCREFacets = newData.facets
        .filter(f => f.type == "FacetType.DISCRETE" && f.coverage.includes("ccre"))
        .map(f => Object.keys(f.values).map(k => Number.parseInt(k)));

    let geneFacetsWithSelections = geneFacets.filter(gf => contains(gf, discreteFacetIds));
    let cCREFacetsWithSelections = cCREFacets.filter(cf => contains(cf, discreteFacetIds));

    let selectedGeneFacets = geneFacetsWithSelections.map(gf => intersection(gf, discreteFacetIds));
    let selectedcCREFacets = cCREFacetsWithSelections.map(cf => intersection(cf, discreteFacetIds));

    let minEffect = Number.POSITIVE_INFINITY;
    let maxEffect = Number.NEGATIVE_INFINITY;

    let minSig = Number.POSITIVE_INFINITY;
    let maxSig = Number.NEGATIVE_INFINITY;

    for (let cIdx = 0; cIdx < data.chromosomes.length; cIdx++) {
        if (geneFacetsWithSelections.length > 0) {
            const gene_intervals_len = data.chromosomes[cIdx].gene_intervals.length;
            for (let iIdx = 0; iIdx < gene_intervals_len; iIdx++) {
                const genes = data.chromosomes[cIdx].gene_intervals[iIdx].genes;
                const genes_len = genes.length;
                let newGenes = [];
                for (let gIdx = 0; gIdx < genes_len; gIdx++) {
                    let regEffects = genes[gIdx][0];
                    const contFacetCount = regEffects[0];
                    let newRegEffects = Array(regEffects.length)
                    newRegEffects[0] = contFacetCount;
                    let newREIdx = 1;
                    for (let rIdx = 1; rIdx < regEffects.length;) {
                        const discFacetCount = regEffects[rIdx];
                        const discFacets = regEffects.slice(rIdx + 1, rIdx + 1 + discFacetCount);
                        const effectSize = regEffects[rIdx + 1 + discFacetCount];
                        const significance = regEffects[rIdx + 1 + discFacetCount + 1];

                        if (selectedGeneFacets.every(gf => contains(gf, discFacets))) {
                            maxEffect = maxEffect > effectSize ? maxEffect : effectSize;
                            minEffect = minEffect < effectSize ? minEffect : effectSize;
                            maxSig = maxSig > significance ? maxSig : significance;
                            minSig = minSig < significance ? minSig : significance;

                            newRegEffects[newREIdx++] = discFacetCount;
                            for (let dIdx = 0; dIdx < discFacetCount; dIdx++, newREIdx++) {
                                newRegEffects[newREIdx] = discFacets[dIdx];
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
        }

        if (cCREFacetsWithSelections.length > 0) {
            const ccre_intervals_len = data.chromosomes[cIdx].ccre_intervals.length;
            for (let iIdx = 0; iIdx < ccre_intervals_len; iIdx++) {
                const ccres = data.chromosomes[cIdx].ccre_intervals[iIdx].ccres
                const ccres_len = ccres.length;

                let newcCREs = [];
                for (let gIdx = 0; gIdx < ccres_len; gIdx++) {
                    const regEffects = ccres[gIdx][0];
                    const contFacetCount = regEffects[0];
                    let newRegEffects = Array(regEffects.length)
                    newRegEffects[0] = contFacetCount;
                    let newREIdx = 1;
                    for (let rIdx = 1; rIdx < regEffects.length;) {
                        const discFacetCount = regEffects[rIdx];
                        const discFacets = regEffects.slice(rIdx + 1, rIdx + 1 + discFacetCount);
                        const effectSize = regEffects[rIdx + 1 + discFacetCount];
                        const significance = regEffects[rIdx + 1 + discFacetCount + 1];

                        if (selectedcCREFacets.every(cf => contains(cf, discFacets))) {
                            maxEffect = maxEffect > effectSize ? maxEffect : effectSize;
                            minEffect = minEffect < effectSize ? minEffect : effectSize;
                            maxSig = maxSig > significance ? maxSig : significance;
                            minSig = minSig < significance ? minSig : significance;

                            newRegEffects[newREIdx++] = discFacetCount;
                            for (let dIdx = 0; dIdx < discFacetCount; dIdx++, newREIdx++) {
                                newRegEffects[newREIdx] = discFacets[dIdx];
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
    }
    minEffect = minEffect === Number.POSITIVE_INFINITY ? effectSizeInterval[0] : minEffect;
    maxEffect = maxEffect === Number.NEGATIVE_INFINITY ? effectSizeInterval[1] : maxEffect;
    minSig = minSig === Number.POSITIVE_INFINITY ? sigInterval[0] : minSig;
    maxSig = maxSig === Number.NEGATIVE_INFINITY ? sigInterval[1] : maxSig;

    postMessage({data: newData, effectSizeInterval: [minEffect, maxEffect], sigInterval: [minSig, maxSig]});
}
