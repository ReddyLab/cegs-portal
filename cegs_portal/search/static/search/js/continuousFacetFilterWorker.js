importScripts("./vizUtils.js");

onmessage = function(e) {
    const data = e.data.data
    const effectSizeRange = e.data.continuousFilters[0];
    const sigRange = e.data.continuousFilters[1];

    let newData = shallowClone(data);

    for (let cIdx = 0; cIdx < data.chromosomes.length; cIdx++) {
        const target_intervals = data.chromosomes[cIdx].target_intervals;
        for (let iIdx = 0; iIdx < target_intervals.length; iIdx++) {
            const targets = target_intervals[iIdx].targets;
            let newTargets = [];
            for (let gIdx = 0; gIdx < targets.length; gIdx++) {
                let regEffects = targets[gIdx][0];
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
                    newTargets.push([newRegEffects, targets[gIdx][1]]);
                }
            }
            newData.chromosomes[cIdx].target_intervals[iIdx] = {
                start: data.chromosomes[cIdx].target_intervals[iIdx].start,
                targets: newTargets
            };
        }

        const source_intervals = data.chromosomes[cIdx].source_intervals;
        for (let iIdx = 0; iIdx < source_intervals.length; iIdx++) {
            const sources = source_intervals[iIdx].sources;
            let newSources = [];
            for (let gIdx = 0; gIdx < sources.length; gIdx++) {
                let regEffects = sources[gIdx][0];
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
                    newSources.push([newRegEffects, sources[gIdx][1]]);
                }
            }
            newData.chromosomes[cIdx].source_intervals[iIdx] = {
                start: data.chromosomes[cIdx].source_intervals[iIdx].start,
                sources: newSources
            };
        }
    }

    postMessage(newData);
}
