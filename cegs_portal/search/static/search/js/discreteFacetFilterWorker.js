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

    let targetFacets = newData.facets
        .filter(f => f.type == "FacetType.DISCRETE" && f.coverage.includes("target"))
        .map(f => Object.keys(f.values).map(k => Number.parseInt(k)));

    let sourceFacets = newData.facets
        .filter(f => f.type == "FacetType.DISCRETE" && f.coverage.includes("source"))
        .map(f => Object.keys(f.values).map(k => Number.parseInt(k)));

    let targetFacetsWithSelections = targetFacets.filter(gf => contains(gf, discreteFacetIds));
    let sourceFacetsWithSelections = sourceFacets.filter(cf => contains(cf, discreteFacetIds));

    let selectedTargetFacets = targetFacetsWithSelections.map(gf => intersection(gf, discreteFacetIds));
    let selectedSourceFacets = sourceFacetsWithSelections.map(cf => intersection(cf, discreteFacetIds));

    let minEffect = Number.POSITIVE_INFINITY;
    let maxEffect = Number.NEGATIVE_INFINITY;

    let minSig = Number.POSITIVE_INFINITY;
    let maxSig = Number.NEGATIVE_INFINITY;

    for (let cIdx = 0; cIdx < data.chromosomes.length; cIdx++) {
        if (targetFacetsWithSelections.length > 0) {
            const target_intervals_len = data.chromosomes[cIdx].target_intervals.length;
            for (let iIdx = 0; iIdx < target_intervals_len; iIdx++) {
                const targets = data.chromosomes[cIdx].target_intervals[iIdx].targets;
                const targets_len = targets.length;
                let newTargets = [];
                for (let gIdx = 0; gIdx < targets_len; gIdx++) {
                    let regEffects = targets[gIdx][0];
                    const contFacetCount = regEffects[0];
                    let newRegEffects = Array(regEffects.length)
                    newRegEffects[0] = contFacetCount;
                    let newREIdx = 1;
                    for (let rIdx = 1; rIdx < regEffects.length;) {
                        const discFacetCount = regEffects[rIdx];
                        const discFacets = regEffects.slice(rIdx + 1, rIdx + 1 + discFacetCount);
                        const effectSize = regEffects[rIdx + 1 + discFacetCount];
                        const significance = regEffects[rIdx + 1 + discFacetCount + 1];

                        if (selectedTargetFacets.every(gf => contains(gf, discFacets))) {
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
                        newTargets.push([newRegEffects, targets[gIdx][1]]);
                    }
                }
                newData.chromosomes[cIdx].target_intervals[iIdx] = {
                    start: data.chromosomes[cIdx].target_intervals[iIdx].start,
                    targets: newTargets
                };
            }
        }

        if (sourceFacetsWithSelections.length > 0) {
            const source_intervals_len = data.chromosomes[cIdx].source_intervals.length;
            for (let iIdx = 0; iIdx < source_intervals_len; iIdx++) {
                const sources = data.chromosomes[cIdx].source_intervals[iIdx].sources
                const sources_len = sources.length;

                let newSources = [];
                for (let gIdx = 0; gIdx < sources_len; gIdx++) {
                    const regEffects = sources[gIdx][0];
                    const contFacetCount = regEffects[0];
                    let newRegEffects = Array(regEffects.length)
                    newRegEffects[0] = contFacetCount;
                    let newREIdx = 1;
                    for (let rIdx = 1; rIdx < regEffects.length;) {
                        const discFacetCount = regEffects[rIdx];
                        const discFacets = regEffects.slice(rIdx + 1, rIdx + 1 + discFacetCount);
                        const effectSize = regEffects[rIdx + 1 + discFacetCount];
                        const significance = regEffects[rIdx + 1 + discFacetCount + 1];

                        if (selectedSourceFacets.every(cf => contains(cf, discFacets))) {
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
                        newSources.push([newRegEffects, sources[gIdx][1]]);
                    }
                }
                newData.chromosomes[cIdx].source_intervals[iIdx] = {
                    start: data.chromosomes[cIdx].source_intervals[iIdx].start,
                    sources: newSources
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
