
export function mergeFacets(facetList, cloneFn) {
    if (facetList.length == 0) {
        throw "No facets to merge"
    } else if (facetList.length == 1) {
        return facetList[0];
    }
    let newFacets = cloneFn(facetList[0]);
    let newFacetsDict = {};
    for (let facet of newFacets) {
        newFacetsDict[facet.id] = facet;
    }

    for (let facets of facetList.slice(1)) {
        for (let facet of facets) {
            if (facet.id in newFacetsDict) {
                let newFacet = newFacetsDict[facet.id];
                if (facet.facet_type == "FacetType.CONTINUOUS") {
                    newFacet.range = [Math.min(newFacet.range[0], facet.range[0]), Math.max(newFacet.range[1], facet.range[1])];
                } else {
                    for (let facetValueID of Object.keys(facet.values)) {
                        if (!(facetValueID in newFacet.values)) {
                            newFacet.values[facetValueID] = facet.values[facetValueID];
                        }
                    }
                }
            } else {
                newFacetsDict[facet.id] = facet;
                newFacets.push(cloneFn(facet));
            }
        }
    }
    return newFacets;
}

export function mergeCoverageData(coveragesList, genome, cloneFn) {
    if (coveragesList.length == 0) {
        throw "No facets to merge"
    } else if (coveragesList.length == 1) {
        return coveragesList[0];
    }

    let newCoverage = [];
    let chromsCovered = new Set();

    for (let genChromosome of genome) {
        let newChromosome = null;
        for (let coverage of coveragesList) {
            for (let chromosome of coverage) {
                // Wrong chromosome
                if (genChromosome.chrom != chromosome.chrom) {
                    continue;
                }

                // Right chromosome, but hasn't been added yet so no merging needed
                if (!chromsCovered.has(chromosome.chrom)) {
                    chromsCovered.add(chromosome.chrom);
                    newChromosome = cloneFn(chromosome);
                    break;
                }

                // Right chromosome; has been added already; need to merge
                let sourceIntervals = [];
                for (let i = 0, j = 0;;) {
                    if (i >= newChromosome.source_intervals.length) {
                        sourceIntervals.push(...chromosome.source_intervals.slice(j));
                        break;
                    }

                    if (j >= chromosome.source_intervals.length) {
                        sourceIntervals.push(...newChromosome.source_intervals.slice(i));
                        break;
                    }

                    if (newChromosome.source_intervals[i].start < chromosome.source_intervals[j].start) {
                        sourceIntervals.push(newChromosome.source_intervals[i]);
                        i += 1;
                    } else if (newChromosome.source_intervals[i].start > chromosome.source_intervals[j].start) {
                        sourceIntervals.push(chromosome.source_intervals[j]);
                        j += 1;
                    } else {
                        sourceIntervals.push({
                            start: chromosome.source_intervals[j].start,
                            count: chromosome.source_intervals[j].count + newChromosome.source_intervals[i].count,
                            associated_buckets: chromosome.source_intervals[j].associated_buckets.concat(newChromosome.source_intervals[i].associated_buckets)
                        })
                        i += 1;
                        j += 1;
                    }
                }
                newChromosome.source_intervals = sourceIntervals;
                let targetIntervals = [];
                for (let i = 0, j = 0;;) {
                    if (i >= newChromosome.target_intervals.length) {
                        targetIntervals.push(...chromosome.target_intervals.slice(j));
                        break;
                    }

                    if (j >= chromosome.target_intervals.length) {
                        targetIntervals.push(...newChromosome.target_intervals.slice(i));
                        break;
                    }

                    if (newChromosome.target_intervals[i].start < chromosome.target_intervals[j].start) {
                        targetIntervals.push(newChromosome.target_intervals[i]);
                        i += 1;
                    } else if (newChromosome.target_intervals[i].start > chromosome.target_intervals[j].start) {
                        targetIntervals.push(chromosome.target_intervals[j]);
                        j += 1;
                    } else {
                        targetIntervals.push({
                            start: chromosome.target_intervals[j].start,
                            count: chromosome.target_intervals[j].count + newChromosome.target_intervals[i].count,
                            associated_buckets: chromosome.target_intervals[j].associated_buckets.concat(newChromosome.target_intervals[i].associated_buckets)
                        })
                        i += 1;
                        j += 1;
                    }
                }
                newChromosome.target_intervals = targetIntervals;
                break;
            }
        }
        newCoverage.push(newChromosome);
    }

    return newCoverage;
}
