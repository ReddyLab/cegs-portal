const bandColors = {
    acen: "#708090",
    gneg: "#FFFFFF",
    gpos: "#000000",
    gpos100: "#000000",
    gpos25: "#D9D9D9",
    gpos33: "#BFBFBF",
    gpos50: "#999999",
    gpos66: "#7F7F7F",
    gpos75: "#666666",
    gvar: "#E0E0E0",
    stalk: "#708090",
};

export const sourceColors = d3.interpolateCool;
const fadedSourceColors = d3.interpolateCubehelixLong(d3.cubehelix(-260, 0.75, 0.95), d3.cubehelix(80, 1.5, 0.95));
export const targetColors = d3.interpolateWarm;
const fadedTargetColors = d3.interpolateCubehelixLong(d3.cubehelix(-100, 0.75, 0.95), d3.cubehelix(80, 1.5, 0.95));
const svgns = "http://www.w3.org/2000/svg";

export class Tooltip {
    constructor(renderContext) {
        this.renderContext = renderContext;
        this._count = document.createElementNS(svgns, "text");
        this._count.setAttribute("y", "-32");
        this._range = document.createElementNS(svgns, "text");
        this._range.setAttribute("y", "-20");
        this.node = document.createElementNS(svgns, "g");
        this.node.setAttribute("pointer-events", "none");
        this.node.setAttribute("display", "none");
        this.node.setAttribute("font-family", "sans-serif");
        this.node.setAttribute("font-size", "12");
        this.node.setAttribute("text-anchor", "middle");
        this._rect = document.createElementNS(svgns, "rect");
        this._rect.setAttribute("x", "-85");
        this._rect.setAttribute("width", "170");
        this._rect.setAttribute("y", "-50");
        this._rect.setAttribute("height", "40");
        this._rect.setAttribute("fill", "white");
        this.node.appendChild(this._rect);
        this.node.appendChild(this._count);
        this.node.appendChild(this._range);
    }

    show(chomIdx, d, scaleX, scaleY) {
        this.node.removeAttribute("display");
        this.node.setAttribute(
            "transform",
            `translate(${this.renderContext.xInset + this.renderContext.toPx(d.start) * scaleX}, ${
                this.renderContext.yInset +
                chomIdx *
                    (this.renderContext.chromDimensions.chromHeight + this.renderContext.chromDimensions.chromSpacing) *
                    scaleY
            }) scale(2)`
        );
        this._count.textContent = `Ct: ${d.count}`;
        this._range.textContent = `Loc: (${d.start}, ${d.end})`;
    }

    hide() {
        this.node.setAttribute("display", "none");
    }
}

function ChromDimensions(genome) {
    this.chromHeight = 98;
    this.chromSpacing = 10;
    this.maxPxChromWidth = 2048;
    this.maxChromSize = genome.reduce((a, c) => (c.size > a ? c.size : a), 0);
}

function VizRenderContext(chromDimensions, genome) {
    this.chromDimensions = chromDimensions;
    this.xInset = 60;
    this.yInset = 100;
    this.viewWidth = chromDimensions.maxPxChromWidth + this.xInset * 2;
    this.viewHeight = this.yInset * 2 + (chromDimensions.chromHeight + chromDimensions.chromSpacing) * genome.length;

    this.toPx = function (size) {
        return this.chromDimensions.maxPxChromWidth * (size / this.chromDimensions.maxChromSize);
    };
}

export class GenomeRenderer {
    constructor(genome) {
        this.genome = genome;
        this.chromDimensions = new ChromDimensions(genome);
        this.renderContext = new VizRenderContext(this.chromDimensions, genome);
        this.tooltip = new Tooltip(this.renderContext);
        this.onBucketClick = null;
        this.onBackgroundClick = null;
    }

    _chromosomeOutline(scales, d, i) {
        let chromDimensions = this.chromDimensions;
        let renderContext = this.renderContext;
        const width = renderContext.toPx(d.size) * scales.scaleX;
        const top =
            renderContext.yInset + (chromDimensions.chromSpacing + chromDimensions.chromHeight) * i * scales.scaleY;
        const bottom = top + chromDimensions.chromHeight * scales.scaleY;
        const outlinePath = ["M", renderContext.xInset, ",", top];
        outlinePath.push(
            "C",
            renderContext.xInset - 12 * scales.scale,
            ",",
            top,
            " ",
            renderContext.xInset - 12 * scales.scale,
            ",",
            bottom,
            " ",
            renderContext.xInset,
            ",",
            bottom
        );
        outlinePath.push("M", renderContext.xInset + width, ",", top);
        outlinePath.push(
            "C",
            renderContext.xInset + width + 12 * scales.scale,
            ",",
            top,
            " ",
            renderContext.xInset + width + 12 * scales.scale,
            ",",
            bottom,
            " ",
            renderContext.xInset + width,
            ",",
            bottom
        );

        for (const band of d.bands) {
            let bandStart = band.start < band.end ? band.start : band.end;
            let bandEnd = band.start > band.end ? band.start : band.end;
            let bandPxStart = this.renderContext.toPx(bandStart) * scales.scaleX;
            let bandPxEnd = this.renderContext.toPx(bandEnd) * scales.scaleX;
            let bandPxWidth = bandPxEnd - bandPxStart;

            if (band.type == "acen") {
                if (band.id.startsWith("p")) {
                    outlinePath.push("M", renderContext.xInset + bandPxStart, ",", top);
                    outlinePath.push("l", bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scales.scaleY);
                    outlinePath.push("l", -bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scales.scaleY);
                } else {
                    outlinePath.push("M", renderContext.xInset + bandPxEnd, ",", top);
                    outlinePath.push("l", -bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scales.scaleY);
                    outlinePath.push("l", bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scales.scaleY);
                }
            } else {
                outlinePath.push("M", renderContext.xInset + bandPxStart, ",", top);
                outlinePath.push("l", bandPxWidth, ",", 0);
                outlinePath.push("M", renderContext.xInset + bandPxStart, ",", bottom);
                outlinePath.push("l", bandPxWidth, ",", 0);
            }
        }

        return outlinePath.join("");
    }

    _chromosomeBand(scales, chromIndex) {
        let renderContext = this.renderContext;
        let chromDimensions = this.chromDimensions;
        return function (band) {
            const top =
                renderContext.yInset +
                (chromDimensions.chromSpacing + chromDimensions.chromHeight) * chromIndex * scales.scaleY;
            let bandStart = band.start < band.end ? band.start : band.end;
            let bandPxStart = renderContext.toPx(bandStart) * scales.scaleX;
            let bandEnd = band.start > band.end ? band.start : band.end;
            let bandPxEnd = renderContext.toPx(bandEnd) * scales.scaleX;
            let bandPxWidth = bandPxEnd - bandPxStart;
            let outlinePath = ["M", renderContext.xInset + bandPxStart, ",", top];
            if (band.type == "acen") {
                if (band.id.startsWith("p")) {
                    outlinePath.push("M", renderContext.xInset + bandPxStart, ",", top);
                    outlinePath.push("l", bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scales.scaleY);
                    outlinePath.push("l", -bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scales.scaleY);
                } else {
                    outlinePath.push("M", renderContext.xInset + bandPxEnd, ",", top);
                    outlinePath.push("l", -bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scales.scaleY);
                    outlinePath.push("l", bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scales.scaleY);
                }
            } else {
                outlinePath.push("l", 0, ",", chromDimensions.chromHeight * scales.scaleY);
                outlinePath.push("l", bandPxWidth, ",", 0);
                outlinePath.push("l", 0, ",", -chromDimensions.chromHeight * scales.scaleY);
                outlinePath.push("l", -bandPxWidth, ",", 0);
            }

            return outlinePath.join("");
        };
    }

    _zoomOutButton(svg, chromIndex, scales, xInset) {
        const buttonVMargin = 10;
        const buttonHeight = this.chromDimensions.chromSpacing * scales.scaleY - buttonVMargin * 2;
        const buttonTop =
            this.renderContext.yInset +
            (this.chromDimensions.chromSpacing + this.chromDimensions.chromHeight) * chromIndex * scales.scaleY -
            (buttonHeight + buttonVMargin);
        const buttonWidth = 25 * scales.scaleX;

        let buttonGroup = svg.append("g");
        let button = buttonGroup.append("rect");
        button
            .attr("width", buttonWidth)
            .attr("x", xInset + (this.renderContext.viewWidth - buttonWidth) / 2)
            .attr("y", buttonTop)
            .attr("height", buttonHeight)
            .attr("stroke", 1)
            .attr("fill", "#9D9D9D")
            .attr("rx", 3 * scales.scale);
        let buttonText = buttonGroup.append("text");
        buttonText
            .attr("x", xInset + this.renderContext.viewWidth / 2)
            .attr("y", buttonTop + buttonHeight / 2 - 7)
            .attr("font-size", 140)
            .attr("text-anchor", "middle")
            .attr("dominant-baseline", "central")
            .text("Zoom Out");
    }

    render(
        coverageData,
        focusIndex,
        sourceCountInterval,
        targetCountInterval,
        viewBox,
        scale,
        scaleX,
        scaleY,
        highlightRegions
    ) {
        const bucketHeight = 44 * scaleY;
        const sourceCountRange = sourceCountInterval[1] - sourceCountInterval[0];
        const targetCountRange = targetCountInterval[1] - targetCountInterval[0];
        const scales = {scale, scaleX, scaleY};

        const svg = d3
            .create("svg")
            .attr("stroke", "black")
            .attr("viewBox", viewBox)
            .style("max-width", `${this.chromDimensions.maxPxChromWidth + 20}px`)
            .style("display", "block")
            .style("margin", "auto");

        let chromGroups = [];
        for (let i = 0; i < this.genome.length; i++) {
            const frame = svg.append("g");
            chromGroups.push(frame);
            const chrom = frame.append("g");
            chrom
                .selectAll("path")
                .data(this.genome[i].bands)
                .join("path")
                .attr("fill", (b) => bandColors[b.type])
                .attr("fill-opacity", 0.3)
                .attr("stroke", "none")
                .attr("d", this._chromosomeBand(scales, i));

            chrom
                .append("path")
                .attr("stroke-width", 1)
                .attr("stroke", "black")
                .attr("fill", "none")
                .attr("d", this._chromosomeOutline(scales, this.genome[i], i));
        }

        if (scale > 1) {
            this._zoomOutButton(svg, focusIndex, scales, viewBox[0]);
        }

        let nameGroup = svg.append("g");
        nameGroup
            .selectAll("text")
            .data(coverageData)
            .join("text")
            .attr("x", 0)
            .attr(
                "y",
                (chromo, i) =>
                    this.renderContext.yInset +
                    (this.chromDimensions.chromHeight / 2 +
                        (this.chromDimensions.chromSpacing + this.chromDimensions.chromHeight) * i) *
                        scaleY
            )
            .attr("font-size", Math.max(Math.ceil(14 * (scaleY * 0.3)), 32))
            .text((chromo) => chromo.chrom);

        let allSourceRects = {};
        let allTargetRects = {};

        for (let i = 0; i < coverageData.length; i++) {
            const bucketSize = coverageData[i].bucket_size;
            const chromName = coverageData[i].chrom;
            const r = highlightRegions[chromName];
            const bucketWidth = this.renderContext.toPx(bucketSize) * scaleX;

            const frame = chromGroups[i];
            const sourceOverlay = frame.append("g");
            sourceOverlay.attr("stroke", "none");

            let sourceRects = sourceOverlay
                .selectAll("rect")
                .data(coverageData[i].source_intervals)
                .join("rect")
                .attr("fill", (source) => {
                    if (Object.keys(highlightRegions).length == 0) {
                        return sourceColors((source.count - sourceCountInterval[0]) / sourceCountRange);
                    }

                    if (r == undefined) {
                        return fadedSourceColors((source.count - sourceCountInterval[0]) / sourceCountRange);
                    }

                    if (
                        r.some(
                            (region) =>
                                (region[0] >= source.start && region[0] < source.start + bucketSize) ||
                                (region[1] >= source.start && region[1] < source.start + bucketSize)
                        )
                    ) {
                        return sourceColors((source.count - sourceCountInterval[0]) / sourceCountRange);
                    } else {
                        return fadedSourceColors((source.count - sourceCountInterval[0]) / sourceCountRange);
                    }
                })
                .attr("x", (source) => this.renderContext.xInset + this.renderContext.toPx(source.start) * scaleX)
                .attr(
                    "y",
                    this.renderContext.yInset +
                        (this.chromDimensions.chromSpacing + this.chromDimensions.chromHeight) * i * scaleY
                )
                .attr("width", bucketWidth)
                .attr("height", bucketHeight);

            allSourceRects[i] = sourceRects;

            const targetOverlay = frame.append("g");
            targetOverlay.attr("stroke", "none");
            let targetRects = targetOverlay
                .selectAll("rect")
                .data(coverageData[i].target_intervals)
                .join("rect")
                .attr("fill", (target) => {
                    if (Object.keys(highlightRegions).length == 0) {
                        return targetColors((target.count - targetCountInterval[0]) / targetCountRange);
                    }

                    if (r == undefined) {
                        return fadedTargetColors((target.count - targetCountInterval[0]) / targetCountRange);
                    }

                    if (
                        r.some(
                            (region) =>
                                (region[0] >= target.start && region[0] < target.start + bucketSize) ||
                                (region[1] >= target.start && region[1] < target.start + bucketSize)
                        )
                    ) {
                        return targetColors((target.count - targetCountInterval[0]) / targetCountRange);
                    } else {
                        return fadedTargetColors((target.count - targetCountInterval[0]) / targetCountRange);
                    }
                })
                .attr("x", (target) => this.renderContext.xInset + this.renderContext.toPx(target.start) * scaleX)
                .attr(
                    "y",
                    this.renderContext.yInset +
                        (54 + (this.chromDimensions.chromSpacing + this.chromDimensions.chromHeight) * i) * scaleY
                )
                .attr("width", bucketWidth)
                .attr("height", bucketHeight);

            allTargetRects[i] = targetRects;

            let mouseLeave = () => {
                for (const k of Object.keys(allSourceRects)) {
                    allSourceRects[k].attr("stroke", null);
                    allSourceRects[k].attr("stroke-width", null);
                }
                for (const k of Object.keys(allTargetRects)) {
                    allTargetRects[k].attr("stroke", null);
                    allTargetRects[k].attr("stroke-width", null);
                }
                this.tooltip.hide();
            };

            sourceRects
                .on("mouseenter", (event, rect) => {
                    sourceRects.attr("stroke", (node) => (node.start == rect.start ? "red" : null));
                    sourceRects.attr("stroke-width", (node) => (node.start == rect.start ? 8 : null));

                    let target_buckets = new Array(coverageData.length);
                    for (let i = 0; i < target_buckets.length; i++) {
                        target_buckets[i] = new Set();
                    }

                    for (let i = 0; i < rect.associated_buckets.length; i += 2) {
                        target_buckets[rect.associated_buckets[i]].add(rect.associated_buckets[i + 1]);
                    }

                    for (let i = 0; i < target_buckets.length; i++) {
                        let target_bucket = target_buckets[i];
                        for (let j = 0; j < target_bucket.size; j += 2) {
                            let targetRects = allTargetRects[i];
                            targetRects.attr("stroke", function (node) {
                                if (target_bucket.has((node.start - 1) / bucketSize)) {
                                    return "yellow";
                                }
                                return null;
                            });
                            targetRects.attr("stroke-width", function (node) {
                                if (target_bucket.has((node.start - 1) / bucketSize)) {
                                    return 8;
                                }
                                return null;
                            });
                        }
                    }

                    rect.end = rect.start + bucketSize;
                    this.tooltip.show(i, rect, scaleX, scaleY);
                })
                .on("mouseleave", (event, rect) => {
                    mouseLeave();
                })
                .on("click", (event, rect) => {
                    event.stopImmediatePropagation();
                    this.onBucketClick(i, chromName, rect.start, rect.end, this);
                });

            targetRects
                .on("mouseenter", (event, rect) => {
                    targetRects.attr("stroke", (node) => (node.start == rect.start ? "red" : null));
                    targetRects.attr("stroke-width", (node) => (node.start == rect.start ? 8 : null));

                    let source_buckets = new Array(coverageData.length);
                    for (let i = 0; i < source_buckets.length; i++) {
                        source_buckets[i] = new Set();
                    }

                    for (let i = 0; i < rect.associated_buckets.length; i += 2) {
                        source_buckets[rect.associated_buckets[i]].add(rect.associated_buckets[i + 1]);
                    }

                    for (let i = 0; i < source_buckets.length; i++) {
                        let source_bucket = source_buckets[i];
                        for (let j = 0; j < source_bucket.size; j += 2) {
                            let sourceRects = allSourceRects[i];
                            sourceRects.attr("stroke", function (node) {
                                if (source_bucket.has((node.start - 1) / bucketSize)) {
                                    return "yellow";
                                }
                                return null;
                            });
                            sourceRects.attr("stroke-width", function (node) {
                                if (source_bucket.has((node.start - 1) / bucketSize)) {
                                    return 8;
                                }
                                return null;
                            });
                        }
                    }

                    rect.end = rect.start + bucketSize;
                    this.tooltip.show(i, rect, scaleX, scaleY);
                })
                .on("mouseleave", (event, rect) => {
                    mouseLeave();
                })
                .on("click", (event, rect) => {
                    event.stopImmediatePropagation();
                    this.onBucketClick(i, chromName, rect.start, rect.end, this);
                });
        }

        svg.append(() => this.tooltip.node);
        svg.on("click", (event, rect) => {
            this.onBackgroundClick(rect, this);
        });
        return svg.node();
    }
}
