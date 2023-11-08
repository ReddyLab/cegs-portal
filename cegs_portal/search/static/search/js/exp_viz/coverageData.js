export function mergeFilteredData(current_data, response_data) {
    if (current_data.length == 0) {
        return response_data;
    }

    let resp_obj = response_data.reduce((obj, chrom) => {
        obj[chrom.chrom] = chrom;
        return obj;
    }, {});

    return current_data.map((chrom) => {
        return chrom.chrom in resp_obj ? resp_obj[chrom.chrom] : chrom;
    });
}
