import {a, g, rc, t} from "../dom.js";
import {Legend} from "./obsLegend.js";
import {coverageTypeDeferredFunctions, coverageTypeFunctions} from "./covTypeUtils.js";
import {
    STATE_ZOOM_CHROMO_INDEX,
    STATE_SCALE,
    STATE_SCALE_X,
    STATE_SCALE_Y,
    STATE_VIEWBOX,
    STATE_ALL_FILTERED,
    STATE_NUMERIC_FILTER_INTERVALS,
    STATE_COUNT_FILTER_INTERVALS,
    STATE_HIGHLIGHT_REGIONS,
    STATE_ITEM_COUNTS,
    STATE_SOURCE_TYPE,
    STATE_LEGEND_INTERVALS,
} from "./consts.js";

let sourceRenderColors = coverageTypeFunctions(
    {
        color: d3.interpolateCool,
        faded: d3.interpolateCubehelixLong(d3.cubehelix(-260, 0.75, 0.95), d3.cubehelix(80, 1.5, 0.95)),
    },
    {
        color: d3.interpolateCubehelixLong(d3.cubehelix(80, 1.5, 0.8), d3.cubehelix(260, 0.75, 0.35)),
        faded: d3.interpolateCubehelixLong(d3.cubehelix(80, 1.5, 0.95), d3.cubehelix(-260, 0.75, 0.95)),
    },
    {
        color: d3.interpolateCubehelixLong(d3.cubehelix(80, 1.5, 0.8), d3.cubehelix(260, 0.75, 0.35)),
        faded: d3.interpolateCubehelixLong(d3.cubehelix(80, 1.5, 0.95), d3.cubehelix(-260, 0.75, 0.95)),
    },
);

let targetRenderColors = coverageTypeFunctions(
    {
        color: d3.interpolateWarm,
        faded: d3.interpolateCubehelixLong(d3.cubehelix(-100, 0.75, 0.95), d3.cubehelix(80, 1.5, 0.95)),
    },
    {
        color: d3.interpolateCubehelixLong(d3.cubehelix(80, 1.5, 0.8), d3.cubehelix(-100, 0.75, 0.35)),
        faded: d3.interpolateCubehelixLong(d3.cubehelix(80, 1.5, 0.95), d3.cubehelix(-100, 0.75, 0.95)),
    },
    {
        color: d3.interpolateCubehelixLong(d3.cubehelix(80, 1.5, 0.8), d3.cubehelix(-100, 0.75, 0.35)),
        faded: d3.interpolateCubehelixLong(d3.cubehelix(80, 1.5, 0.95), d3.cubehelix(-100, 0.75, 0.95)),
    },
);

let sourceRenderDataTransform = coverageTypeDeferredFunctions(
    (state) => {
        return (d) => {
            let sourceCountInterval = state.g(STATE_COUNT_FILTER_INTERVALS).source;
            let sourceCountRange = sourceCountInterval[1] - sourceCountInterval[0];
            return sourceCountRange != 0 ? (d.count - sourceCountInterval[0]) / sourceCountRange : 0.5;
        };
    },
    (state) => (d) => {
        let significanceInterval = state.g(STATE_NUMERIC_FILTER_INTERVALS).sig;
        let significanceRange = significanceInterval[1] - significanceInterval[0];
        return significanceRange != 0 ? (d.max_log10_sig - significanceInterval[0]) / significanceRange : 0.5;
    },
    (state) => (d) => {
        let effectSizeInterval = state.g(STATE_NUMERIC_FILTER_INTERVALS).effect;
        let effectSizeRange = effectSizeInterval[1] - effectSizeInterval[0];
        return effectSizeRange != 0 ? (d.max_abs_effect - effectSizeInterval[0]) / effectSizeRange : 0.5;
    },
);

let targetRenderDataTransform = coverageTypeDeferredFunctions(
    (state) => {
        return (d) => {
            let targetCountInterval = state.g(STATE_COUNT_FILTER_INTERVALS).target;
            let targetCountRange = targetCountInterval[1] - targetCountInterval[0];
            return sourceCountRange != 0 ? (d.count - targetCountInterval[0]) / targetCountRange : 0.5;
        };
    },
    (state) => (d) => {
        let significanceInterval = state.g(STATE_NUMERIC_FILTER_INTERVALS).sig;
        let significanceRange = significanceInterval[1] - significanceInterval[0];
        return significanceRange != 0 ? (d.max_log10_sig - significanceInterval[0]) / significanceRange : 0.5;
    },
    (state) => (d) => {
        let effectSizeInterval = state.g(STATE_NUMERIC_FILTER_INTERVALS).effect;
        let effectSizeRange = effectSizeInterval[1] - effectSizeInterval[0];
        return effectSizeRange != 0 ? (d.max_abs_effect - effectSizeInterval[0]) / effectSizeRange : 0.5;
    },
);

function sourceTooltipDataLabel(state) {
    return [`${state.g(STATE_SOURCE_TYPE)} Count`, "Largest Significance", "Greatest Effect Size"];
}

let targetTooltipDataLabel = ["Gene Count", "Largest Significance", "Greatest Effect Size"];

let sourceLegendTitle = coverageTypeDeferredFunctions(
    (state) => `Number of ${state.g(STATE_SOURCE_TYPE)}s`,
    (state) => `${state.g(STATE_SOURCE_TYPE)} Effect Significance`,
    (state) => `${state.g(STATE_SOURCE_TYPE)} Effect Size`,
);

let targetLegendTitle = coverageTypeFunctions(
    "Number of Genes Assayed",
    "Significance of Effect on Assayed Genes",
    "Size of Effect on Assayed Genes",
);

let tooltipDataSelectors = [
    (d) => d.count,
    (d) => {
        if (d.max_log10_sig >= 0.001) {
            return d.max_log10_sig.toFixed(3); // e.g., 12.34567890 -> 12.345
        } else {
            return d.max_log10_sig.toExponential(2); // e.g., 0.0000000000345345345 -> 3.45e-11
        }
    },
    (d) => {
        if (Math.abs(d.max_abs_effect) >= 0.001) {
            return d.max_abs_effect.toFixed(3); // e.g., 12.34567890 -> 12.345
        } else {
            return d.max_abs_effect.toExponential(2); // e.g., 0.0000000000345345345 -> 3.45e-11
        }
    },
];

export function render(state, genomeRenderer) {
    const viewBox = state.g(STATE_VIEWBOX);
    const scale = state.g(STATE_SCALE);
    const scaleX = state.g(STATE_SCALE_X);
    const scaleY = state.g(STATE_SCALE_Y);
    const highlightRegions = state.g(STATE_HIGHLIGHT_REGIONS);
    let currentLevel = state.g(STATE_ALL_FILTERED);
    let focusIndex = state.g(STATE_ZOOM_CHROMO_INDEX);
    let itemCounts = state.g(STATE_ITEM_COUNTS);
    let legendIntervals = state.g(STATE_LEGEND_INTERVALS);

    let sourceColors = sourceRenderColors(state);
    let targetColors = targetRenderColors(state);

    rc(
        g("chrom-data"),
        genomeRenderer.render(
            currentLevel,
            focusIndex,
            sourceColors,
            targetColors,
            sourceRenderDataTransform(state),
            targetRenderDataTransform(state),
            tooltipDataSelectors,
            sourceTooltipDataLabel(state),
            targetTooltipDataLabel,
            viewBox,
            scale,
            scaleX,
            scaleY,
            highlightRegions,
        ),
    );
    rc(
        g("chrom-data-legend"),
        Legend(d3.scaleSequential(legendIntervals.source, sourceColors.color), {
            title: sourceLegendTitle(state),
        }),
    );
    a(
        g("chrom-data-legend"),
        Legend(d3.scaleSequential(legendIntervals.target, targetColors.color), {
            title: targetLegendTitle(state),
        }),
    );
    rc(g("reo-count"), t(`Observations: ${itemCounts[0].toLocaleString()}`));
    rc(g("source-count"), t(`${state.g(STATE_SOURCE_TYPE)}s: ${itemCounts[1].toLocaleString()}`));
    rc(g("target-count"), t(`Genes: ${itemCounts[2].toLocaleString()}`));
}
