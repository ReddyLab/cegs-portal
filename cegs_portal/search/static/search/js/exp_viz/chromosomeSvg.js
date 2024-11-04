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

const svgns = "http://www.w3.org/2000/svg";

export class Tooltip {
    constructor(renderContext) {
        this.renderContext = renderContext;
        this.width = 540;
        this.height = 225;
        this._range = document.createElementNS(svgns, "text");
        this._range.setAttribute("y", "42");
        this._count_value = document.createElementNS(svgns, "text");
        this._count_value.setAttribute("y", "96");
        this._sig_value = document.createElementNS(svgns, "text");
        this._sig_value.setAttribute("y", "150");
        this._effect_value = document.createElementNS(svgns, "text");
        this._effect_value.setAttribute("y", "204");
        this.node = document.createElementNS(svgns, "g");
        this.node.setAttribute("pointer-events", "none");
        this.node.setAttribute("display", "none");
        this.node.setAttribute("font-family", "sans-serif");
        this.node.setAttribute("font-size", "36");
        this.node.setAttribute("text-anchor", "middle");
        this._rect = document.createElementNS(svgns, "rect");
        this._rect.setAttribute("x", `-${this.width / 2}`);
        this._rect.setAttribute("width", `${this.width}`);
        this._rect.setAttribute("height", `${this.height}`);
        this._rect.setAttribute("fill", "white");
        this._rect.setAttribute("rx", "15");
        this._rect.setAttribute("stroke", "gray");
        this.node.appendChild(this._rect);
        this.node.appendChild(this._range);
        this.node.appendChild(this._count_value);
        this.node.appendChild(this._sig_value);
        this.node.appendChild(this._effect_value);
    }

    show(chromIdx, d, scaleX, scaleY, viewBox, chromName, dataSelectors, dataLabels) {
        this.node.removeAttribute("display");
        let minXPadding = 2; // minimum X padding
        // Don't let the left portion of the tooltip get cut off
        let xInset = Math.max(
            viewBox[0] + this.width / 2 + minXPadding,
            this.renderContext.xInset + this.renderContext.toPx(d.start) * scaleX,
        );

        // Don't let the right portion of the tooltip get cut off
        xInset = Math.min(xInset, viewBox[0] + viewBox[2] - this.width / 2 - minXPadding);

        // Render above the chromosome
        let yInset =
            this.renderContext.yInset +
            chromIdx *
                (this.renderContext.chromDimensions.chromHeight + this.renderContext.chromDimensions.chromSpacing) *
                scaleY -
            this.height -
            this.renderContext.chromDimensions.chromSpacing;
        if (yInset < viewBox[1]) {
            // Oops, that will cut off the top of the tooltip. Render below the chromosome
            yInset =
                this.renderContext.yInset +
                (chromIdx + 1) *
                    (this.renderContext.chromDimensions.chromHeight + this.renderContext.chromDimensions.chromSpacing) *
                    scaleY;
        }
        this.node.setAttribute("transform", `translate(${xInset}, ${yInset})`);
        this._range.textContent = `chr${chromName}: ${d.start.toLocaleString()} - ${d.end.toLocaleString()}`;
        this._count_value.textContent = `${dataLabels[0]}: ${dataSelectors[0](d)}`;
        this._sig_value.textContent = `${dataLabels[1]}: ${dataSelectors[1](d)}`;
        this._effect_value.textContent = `${dataLabels[2]}: ${dataSelectors[2](d)}`;
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

function legendBackground(genome) {
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

function chromosomeOutline(scale, scaleX, scaleY, renderContext, chromDimensions, chrom, chromIndex) {
    const width = renderContext.toPx(chrom.size) * scaleX;
    const top =
        renderContext.yInset + (chromDimensions.chromSpacing + chromDimensions.chromHeight) * chromIndex * scaleY;
    const bottom = top + chromDimensions.chromHeight * scaleY;
    const outlinePath = ["M", renderContext.xInset, ",", top];
    outlinePath.push(
        "C",
        renderContext.xInset - 12 * scale,
        ",",
        top,
        " ",
        renderContext.xInset - 12 * scale,
        ",",
        bottom,
        " ",
        renderContext.xInset,
        ",",
        bottom,
    );
    outlinePath.push("M", renderContext.xInset + width, ",", top);
    outlinePath.push(
        "C",
        renderContext.xInset + width + 12 * scale,
        ",",
        top,
        " ",
        renderContext.xInset + width + 12 * scale,
        ",",
        bottom,
        " ",
        renderContext.xInset + width,
        ",",
        bottom,
    );

    for (const band of chrom.bands) {
        let bandStart = band.start < band.end ? band.start : band.end;
        let bandEnd = band.start > band.end ? band.start : band.end;
        let bandPxStart = renderContext.toPx(bandStart) * scaleX;
        let bandPxEnd = renderContext.toPx(bandEnd) * scaleX;
        let bandPxWidth = bandPxEnd - bandPxStart;

        if (band.type == "acen") {
            if (band.id.startsWith("p")) {
                outlinePath.push("M", renderContext.xInset + bandPxStart, ",", top);
                outlinePath.push("l", bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scaleY);
                outlinePath.push("l", -bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scaleY);
            } else {
                outlinePath.push("M", renderContext.xInset + bandPxEnd, ",", top);
                outlinePath.push("l", -bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scaleY);
                outlinePath.push("l", bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scaleY);
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

function chromosomeBand(scaleX, scaleY, renderContext, chromDimensions, chromIndex) {
    return function (band) {
        const top =
            renderContext.yInset + (chromDimensions.chromSpacing + chromDimensions.chromHeight) * chromIndex * scaleY;
        let bandStart = band.start < band.end ? band.start : band.end;
        let bandPxStart = renderContext.toPx(bandStart) * scaleX;
        let bandEnd = band.start > band.end ? band.start : band.end;
        let bandPxEnd = renderContext.toPx(bandEnd) * scaleX;
        let bandPxWidth = bandPxEnd - bandPxStart;
        let outlinePath = ["M", renderContext.xInset + bandPxStart, ",", top];
        if (band.type == "acen") {
            if (band.id.startsWith("p")) {
                outlinePath.push("M", renderContext.xInset + bandPxStart, ",", top);
                outlinePath.push("l", bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scaleY);
                outlinePath.push("l", -bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scaleY);
            } else {
                outlinePath.push("M", renderContext.xInset + bandPxEnd, ",", top);
                outlinePath.push("l", -bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scaleY);
                outlinePath.push("l", bandPxWidth, ",", (chromDimensions.chromHeight / 2) * scaleY);
            }
        } else {
            outlinePath.push("l", 0, ",", chromDimensions.chromHeight * scaleY);
            outlinePath.push("l", bandPxWidth, ",", 0);
            outlinePath.push("l", 0, ",", -chromDimensions.chromHeight * scaleY);
            outlinePath.push("l", -bandPxWidth, ",", 0);
        }

        return outlinePath.join("");
    };
}

export class GenomeRenderer {
    constructor(genome) {
        this.genome = genome;
        this.chromDimensions = new ChromDimensions(genome);
        this.renderContext = new VizRenderContext(this.chromDimensions, genome);
        this.tooltip = new Tooltip(this.renderContext);
        this.legendBackground = legendBackground(genome);
        this.onBucketClick = null;
        this.onBackgroundClick = null;
    }

    _zoomOutButton(svg, chromIndex, scales, xInset) {
        const fontSize = 140;
        const strokeSize = 3;
        const fillColor = "#9D9D9D";
        const cornerRadius = 2;
        const vMargin = 10;
        const text = "Zoom Out";
        const textHAnchor = "middle";
        const textVAnchor = "central";
        const height = this.chromDimensions.chromSpacing * scales.scaleY - vMargin * 2;
        const width = 25 * scales.scaleX;
        const top =
            this.renderContext.yInset +
            (this.chromDimensions.chromSpacing + this.chromDimensions.chromHeight) * chromIndex * scales.scaleY -
            (height + vMargin);

        let buttonGroup = svg.append("g");
        let button = buttonGroup.append("rect");
        button
            .attr("width", width)
            .attr("x", xInset + (this.renderContext.viewWidth - width) / 2)
            .attr("y", top)
            .attr("height", height)
            .attr("stroke-width", strokeSize)
            .attr("fill", fillColor)
            .attr("rx", cornerRadius * scales.scale);
        let buttonText = buttonGroup.append("text");
        buttonText
            .attr("x", xInset + this.renderContext.viewWidth / 2)
            .attr("y", top + height / 2)
            .attr("font-size", fontSize)
            .attr("text-anchor", textHAnchor)
            .attr("dominant-baseline", textVAnchor)
            .text(text);
    }

    render(
        coverageData,
        focusIndex,
        sourceRenderColors,
        targetRenderColors,
        sourceRenderDataTransform,
        targetRenderDataTransform,
        tooltipDataSelector,
        sourceTooltipDataLabel,
        targetTooltipDataLabel,
        viewBox,
        scale,
        scaleX,
        scaleY,
        highlightRegions,
    ) {
        const bucketHeight = 44 * scaleY;
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
                .attr("d", chromosomeBand(scaleX, scaleY, this.renderContext, this.chromDimensions, i));

            chrom
                .append("path")
                .attr("stroke-width", 1)
                .attr("stroke", "black")
                .attr("fill", "none")
                .attr(
                    "d",
                    chromosomeOutline(
                        scale,
                        scaleX,
                        scaleY,
                        this.renderContext,
                        this.chromDimensions,
                        this.genome[i],
                        i,
                    ),
                );
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
                        scaleY,
            )
            .attr("font-size", Math.max(Math.ceil(14 * (scaleY * 0.3)), 32))
            .text((chromo) => chromo.chrom);

        let allSourceRects = {};
        let allTargetRects = {};

        const bucketFocusTime = 50; // ms
        const bucketBlurTime = 200; // ms

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
                        return sourceRenderColors.color(sourceRenderDataTransform(source));
                    }

                    if (r == undefined) {
                        return sourceRenderColors.faded(sourceRenderDataTransform(source));
                    }

                    if (
                        r.some(
                            (region) =>
                                (region[0] >= source.start && region[0] < source.start + bucketSize) ||
                                (region[1] >= source.start && region[1] < source.start + bucketSize),
                        )
                    ) {
                        return sourceRenderColors.color(sourceRenderDataTransform(source));
                    } else {
                        return sourceRenderColors.faded(sourceRenderDataTransform(source));
                    }
                })
                .attr("x", (source) => this.renderContext.xInset + this.renderContext.toPx(source.start) * scaleX)
                .attr(
                    "y",
                    this.renderContext.yInset +
                        (this.chromDimensions.chromSpacing + this.chromDimensions.chromHeight) * i * scaleY,
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
                        return targetRenderColors.color(targetRenderDataTransform(target));
                    }

                    if (r == undefined) {
                        return targetRenderColors.faded(targetRenderDataTransform(target));
                    }

                    if (
                        r.some(
                            (region) =>
                                (region[0] >= target.start && region[0] < target.start + bucketSize) ||
                                (region[1] >= target.start && region[1] < target.start + bucketSize),
                        )
                    ) {
                        return targetRenderColors.color(targetRenderDataTransform(target));
                    } else {
                        return targetRenderColors.faded(targetRenderDataTransform(target));
                    }
                })
                .attr("x", (target) => this.renderContext.xInset + this.renderContext.toPx(target.start) * scaleX)
                .attr(
                    "y",
                    this.renderContext.yInset +
                        (54 + (this.chromDimensions.chromSpacing + this.chromDimensions.chromHeight) * i) * scaleY,
                )
                .attr("width", bucketWidth)
                .attr("height", bucketHeight);

            allTargetRects[i] = targetRects;

            let mouseLeave = () => {
                const t = d3.transition().duration(bucketBlurTime);
                for (const k of Object.keys(allSourceRects)) {
                    allSourceRects[k].interrupt();
                    allSourceRects[k]
                        .transition(t)
                        .attr("fill", (node) => sourceRenderColors.color(sourceRenderDataTransform(node)));
                }
                for (const k of Object.keys(allTargetRects)) {
                    allTargetRects[k].interrupt();
                    allTargetRects[k]
                        .transition(t)
                        .attr("fill", (node) => targetRenderColors.color(targetRenderDataTransform(node)));
                }
                this.tooltip.hide();
            };

            sourceRects
                .on("mouseenter", (event, rect) => {
                    const t = d3.transition().duration(bucketFocusTime);
                    for (const k of Object.keys(allSourceRects)) {
                        allSourceRects[k].interrupt();
                        allSourceRects[k]
                            .transition(t)
                            .attr("fill", (node) =>
                                k == i && node.start == rect.start
                                    ? sourceRenderColors.color(sourceRenderDataTransform(node))
                                    : sourceRenderColors.faded(sourceRenderDataTransform(node)),
                            );
                    }

                    let targetBuckets = new Array(coverageData.length);
                    for (let i = 0; i < targetBuckets.length; i++) {
                        targetBuckets[i] = new Set();
                    }

                    for (let i = 0; i < rect.associated_buckets.length; i += 2) {
                        targetBuckets[rect.associated_buckets[i]].add(rect.associated_buckets[i + 1]);
                    }

                    for (let i = 0; i < targetBuckets.length; i++) {
                        let targetBucket = targetBuckets[i];
                        let targetRects = allTargetRects[i];
                        targetRects.transition(t).attr("fill", (node) => {
                            if (targetBucket.has((node.start - 1) / bucketSize)) {
                                return targetRenderColors.color(targetRenderDataTransform(node));
                            }
                            return targetRenderColors.faded(targetRenderDataTransform(node));
                        });
                    }

                    rect.end = rect.start + bucketSize;
                    this.tooltip.show(
                        i,
                        rect,
                        scaleX,
                        scaleY,
                        viewBox,
                        chromName,
                        tooltipDataSelector,
                        sourceTooltipDataLabel,
                    );
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
                    const t = d3.transition().duration(bucketFocusTime);
                    for (const k of Object.keys(allTargetRects)) {
                        allTargetRects[k].interrupt();
                        allTargetRects[k]
                            .transition(t)
                            .attr("fill", (node) =>
                                k == i && node.start == rect.start
                                    ? targetRenderColors.color(targetRenderDataTransform(node))
                                    : targetRenderColors.faded(targetRenderDataTransform(node)),
                            );
                    }

                    let sourceBuckets = new Array(coverageData.length);
                    for (let i = 0; i < sourceBuckets.length; i++) {
                        sourceBuckets[i] = new Set();
                    }

                    for (let i = 0; i < rect.associated_buckets.length; i += 2) {
                        sourceBuckets[rect.associated_buckets[i]].add(rect.associated_buckets[i + 1]);
                    }

                    for (let i = 0; i < sourceBuckets.length; i++) {
                        let sourceBucket = sourceBuckets[i];
                        let sourceRects = allSourceRects[i];
                        sourceRects.transition(t).attr("fill", (node) => {
                            if (sourceBucket.has((node.start - 1) / bucketSize)) {
                                return sourceRenderColors.color(sourceRenderDataTransform(node));
                            }
                            return sourceRenderColors.faded(sourceRenderDataTransform(node));
                        });
                    }

                    rect.end = rect.start + bucketSize;
                    this.tooltip.show(
                        i,
                        rect,
                        scaleX,
                        scaleY,
                        viewBox,
                        chromName,
                        tooltipDataSelector,
                        targetTooltipDataLabel,
                    );
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
