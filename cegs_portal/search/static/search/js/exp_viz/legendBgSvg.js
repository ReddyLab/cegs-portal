import {bandColors, chromosomeBand, chromosomeOutline, ChromDimensions, VizRenderContext} from "./chromosomeSvg.js";

export function legendBackground(genome) {
    let chromDimensions = new ChromDimensions(genome);
    let renderContext = new VizRenderContext(chromDimensions, genome);
    renderContext.xInset = 0;
    renderContext.yInset = 0;
    const svg = d3
        .create("svg")
        .style("margin", 0)
        .style("position", "absolute")
        .style("top", "0px")
        .style("z-index", "1");
    const chrom = svg.append("g");
    chrom
        .selectAll("path")
        .data(genome[20].bands)
        .join("path")
        .attr("fill", (b) => bandColors[b.type])
        .attr("fill-opacity", 0.1)
        .attr("stroke", "none")
        .attr("d", chromosomeBand(1, 1, renderContext, chromDimensions, 0));

    chrom
        .append("path")
        .attr("stroke-width", 1)
        .attr("stroke", "rgba(0, 0, 0, .1)")
        .attr("fill", "none")
        .attr("d", chromosomeOutline(1, 1, 1, renderContext, chromDimensions, genome[20], 0));

    return svg.node();
}
