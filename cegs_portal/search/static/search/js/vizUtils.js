function shallowClone(data) {
    let newData = {};
    newData.chromosomes = [];
    for (let chromosome of data.chromosomes) {
        newData.chromosomes.push({
            chrom: chromosome.chrom,
            bucket_size: chromosome.bucket_size,
            target_intervals: Array(chromosome.target_intervals.length),
            source_intervals: Array(chromosome.source_intervals.length)
        })
    }
    newData.facets = data.facets;
    return newData;
}

function contains(x, y) {
    for(const xItem of x) {
        for (const yItem of y) {
            if (xItem === yItem) {
                return true
            }
        }
    }
    return false;
}

function intersection(x, y) {
    let intersect = [];
    for(const xItem of x) {
        for (const yItem of y) {
            if (xItem === yItem) {
                intersect.push(xItem);
            }
        }
    }
    return intersect;
}
