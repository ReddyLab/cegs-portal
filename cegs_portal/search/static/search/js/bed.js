import {getLines} from "./text.js";

const getRegions = function (text) {
    let regions = {};
    for (let line of getLines(text)) {
        let fields = line.split("\t");
        let chrom = fields[0].replace("chr", "");
        let start = parseInt(fields[1]);
        let end = parseInt(fields[2]);

        if (regions[chrom] == undefined) {
            regions[chrom] = [];
        }

        regions[chrom].push([start, end]);
    }

    return regions;
};

export {getRegions};
