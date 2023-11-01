import {a, cc, e, g, rc, t} from "../dom.js";
import {State} from "../state.js";
import {getRegions} from "../bed.js";
import {getJson, postJson} from "../files.js";
import {Legend} from "./obsLegend.js";
import {GenomeRenderer} from "./chromosomeSvg.js";
import {getDownloadRegions, getDownloadAll} from "./downloads.js";
import {debounce} from "../utils.js";

const STATE_ZOOMED = "state-zoomed";
const STATE_ZOOM_CHROMO_INDEX = "state-zoom-chromo-index";
const STATE_SCALE = "state-scale";
const STATE_SCALE_X = "state-scale-x";
const STATE_SCALE_Y = "state-scale-y";
const STATE_VIEWBOX = "state-viewbox";
const STATE_FACETS = "state-facets";
const STATE_CATEGORICAL_FACET_VALUES = "state-categorical-facets";
const STATE_NUMERIC_FACET_VALUES = "state-numeric-facets";
const STATE_COUNT_FILTER_VALUES = "state-count-filter";
const STATE_COVERAGE_DATA = "state-coverage-data";
const STATE_ALL_FILTERED = "state-all-filtered";
const STATE_NUMERIC_FILTER_INTERVALS = "state-numeric-filter-intervals";
const STATE_COUNT_FILTER_INTERVALS = "state-count-filter-intervals";
const STATE_HIGHLIGHT_REGIONS = "state-highlight-regions";
const STATE_SELECTED_EXPERIMENTS = "state-selected-experiments";
const STATE_ITEM_COUNTS = "state-item-counts";
const STATE_SOURCE_TYPE = "state-source-type";
const STATE_ANALYSIS = "state-analysis";
const STATE_COVERAGE_TYPE = "state-coverage-type";
const STATE_LEGEND_INTERVALS = "state-legend-intervals";

const COVERAGE_TYPE_COUNT = "coverage-type-count";
const COVERAGE_TYPE_SIG = "coverage-type-sig";
const COVERAGE_TYPE_EFFECT = "coverage-type-effect";

class GenomeError extends Error {
    constructor(message, options) {
        super(message, options);
    }
}

function intersect_array(arr1, arr2) {
    if (arr1.length == 0 || arr2.length == 0) {
        return [];
    }

    let intersection = [];
    for (let val of arr1) {
        if (arr2.indexOf(val) != -1) {
            intersection.push(val);
        }
    }

    return intersection;
}

function intersect_obj(obj1, obj2) {
    if (obj1.length == 0 || obj2.length == 0) {
        return {};
    }

    let intersection = {};
    for (let key in obj1) {
        if (obj2.hasOwnProperty(key) && obj2[key] === obj1[key]) {
            intersection[key] = obj1[key];
        }
    }
    return intersection;
}

// Merge is the intersection of facets
function merge_facets(experiments_facets) {
    if (experiments_facets.length == 1) {
        return experiments_facets[0];
    }

    let new_facets = [];

    // Create an array of objects mapping facet ids to facets
    let facet_maps = experiments_facets.map((facet_array) =>
        facet_array.reduce((acc, f) => {
            acc[f.id] = f;
            return acc;
        }, {})
    );
    let base_facets = facet_maps[0];
    let rest_facets = facet_maps.slice(1);

    // Get the IDs of facets that are in all experiments
    let facet_id_arrays = experiments_facets.map((facet_array) => facet_array.map((f) => f.id));
    let facet_id_intersection = facet_id_arrays
        .slice(1)
        .reduce((acc, ids) => intersect_array(acc, ids), facet_id_arrays[0]);

    for (let facet_id of facet_id_intersection) {
        let new_facet = base_facets[facet_id];
        for (let facets of rest_facets) {
            let curr_facet = facets[facet_id];
            if (new_facet.facet_type == "FacetType.CATEGORICAL") {
                new_facet.values = intersect_obj(curr_facet.values, new_facet.values);
            } else if (new_facet.facet_type == "FacetType.NUMERIC" && new_facet.range) {
                new_facet.range = [
                    Math.min(new_facet.range[0], curr_facet.range[0]),
                    Math.max(new_facet.range[1], curr_facet.range[1]),
                ];
            } else if (new_facet.facet_type == "FacetType.NUMERIC" && new_facet.range64) {
                new_facet.range64 = [
                    Math.min(new_facet.range64[0], curr_facet.range64[0]),
                    Math.max(new_facet.range64[1], curr_facet.range64[1]),
                ];
            }
        }
        new_facets.push(new_facet);
    }

    return new_facets;
}

function build_state(manifests, genomeRenderer, accessionIDs, sourceType) {
    let coverageData = [];
    let facets = merge_facets(manifests.map((m) => m.facets));
    let default_facets = manifests[0].hasOwnProperty("default_facets") ? manifests[0].default_facets : []; // merge
    let reoCount = manifests.map((m) => m.reo_count).reduce((acc, c) => acc + c, 0);
    let sourceCount = 0;
    let targetCount = 0;
    let sourceCountInterval = levelCountInterval(coverageData, "source_intervals");
    let targetCountInterval = levelCountInterval(coverageData, "target_intervals");
    let effectSizeFilterInterval = facets.filter((f) => f.name === "Effect Size")[0].range;
    let sigFilterInterval = facets.filter((f) => f.name === "Significance")[0].range64;
    let coverageSelectorValue = g("covSelect").value;
    let legendIntervalFunc = sigInterval;

    if (coverageSelectorValue == "count") {
        legendIntervalFunc = levelCountInterval;
    } else if (coverageSelectorValue == "sig") {
        legendIntervalFunc = sigInterval;
    } else if (coverageSelectorValue == "effect") {
        legendIntervalFunc = effectInterval;
    }

    let state = new State({
        [STATE_ZOOMED]: false,
        [STATE_ZOOM_CHROMO_INDEX]: undefined,
        [STATE_SCALE]: 1,
        [STATE_SCALE_X]: 1,
        [STATE_SCALE_Y]: 1,
        [STATE_VIEWBOX]: [0, 0, genomeRenderer.renderContext.viewWidth, genomeRenderer.renderContext.viewHeight],
        [STATE_FACETS]: facets,
        [STATE_CATEGORICAL_FACET_VALUES]: default_facets,
        [STATE_COVERAGE_DATA]: coverageData,
        [STATE_ALL_FILTERED]: coverageData,
        [STATE_NUMERIC_FILTER_INTERVALS]: {effect: effectSizeFilterInterval, sig: sigFilterInterval},
        [STATE_NUMERIC_FACET_VALUES]: [effectSizeFilterInterval, sigFilterInterval],
        [STATE_COUNT_FILTER_INTERVALS]: {source: sourceCountInterval, target: targetCountInterval},
        [STATE_COUNT_FILTER_VALUES]: [sourceCountInterval, targetCountInterval],
        [STATE_HIGHLIGHT_REGIONS]: {},
        [STATE_SELECTED_EXPERIMENTS]: accessionIDs,
        [STATE_ITEM_COUNTS]: [reoCount, sourceCount, targetCount],
        [STATE_SOURCE_TYPE]: sourceType,
        [STATE_COVERAGE_TYPE]: coverageValue(coverageSelectorValue),
        [STATE_LEGEND_INTERVALS]: {
            source: legendIntervalFunc(coverageData, "source_intervals"),
            target: legendIntervalFunc(coverageData, "target_intervals"),
        },
    });

    return state;
}

function render(state, genomeRenderer) {
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
            highlightRegions
        )
    );
    rc(
        g("chrom-data-legend"),
        Legend(d3.scaleSequential(legendIntervals.source, sourceColors.color), {
            title: sourceLegendTitle(state),
        })
    );
    a(
        g("chrom-data-legend"),
        Legend(d3.scaleSequential(legendIntervals.target, targetColors.color), {
            title: targetLegendTitle(state),
        })
    );
    rc(g("reo-count"), t(`Observations: ${itemCounts[0].toLocaleString()}`));
    rc(g("source-count"), t(`${state.g(STATE_SOURCE_TYPE)}s: ${itemCounts[1].toLocaleString()}`));
    rc(g("target-count"), t(`Genes: ${itemCounts[2].toLocaleString()}`));
}

function categoricalFilterControls(facets, default_facets) {
    return facets
        .filter((f) => f.facet_type == "FacetType.CATEGORICAL")
        .map((facet) => {
            return e("fieldset", {name: "facetfield", class: "my-4"}, [
                e("legend", {class: "font-bold"}, facet.name),
                e(
                    "div",
                    {class: "flex flex-row flex-wrap gap-1"},
                    Object.entries(facet.values).map((entry) => {
                        return e("div", {class: "ml-1"}, [
                            default_facets.includes(parseInt(entry[0]))
                                ? e("input", {type: "checkbox", id: entry[0], name: facet.name, checked: "true"}, [])
                                : e("input", {type: "checkbox", id: entry[0], name: facet.name}, []),
                            e("label", {for: entry[0]}, entry[1]),
                        ]);
                    })
                ),
            ]);
        });
}

function numericFilterControls(state, facets) {
    const numericFacets = facets.filter((f) => f.facet_type == "FacetType.NUMERIC");
    let sliderNodes = [e("div", {name: "facetslider"}, []), e("div", {name: "facetslider"}, [])];
    let filterNodes = [];
    let intervals = state.g(STATE_NUMERIC_FILTER_INTERVALS);

    for (let i = 0; i < numericFacets.length; i++) {
        let facet = numericFacets[i];
        let sliderNode = sliderNodes[i];

        let range;
        let sliderLabel;

        if (facet.name === "Effect Size") {
            range = intervals.effect;
            sliderLabel = facet.name;
        } else if (facet.name === "Significance") {
            range = [intervals.sig[0], intervals.sig[1]];
            sliderLabel = "Significance (-log10)";
        } else {
            continue;
        }

        noUiSlider.create(sliderNode, {
            start: [range[0], range[1]],
            format: {
                to: (n) => n.toPrecision(3),
                from: (s) => Number.parseFloat(s),
            },
            connect: true,
            range: {
                min: range[0],
                max: range[1],
            },
            pips: {
                mode: "range",
                density: 5,
                format: {
                    to: (n) => n.toPrecision(3),
                    from: (s) => Number.parseFloat(s),
                },
            },
        });

        sliderNode.noUiSlider.on("start", function (values, handle) {
            sliderNode.noUiSlider.updateOptions({tooltips: [true, true]});
        });

        sliderNode.noUiSlider.on("end", function (values, handle) {
            sliderNode.noUiSlider.updateOptions({tooltips: [false, false]});
        });

        filterNodes.push(e("div", {class: "h-24 w-72"}, [e("div", sliderLabel), sliderNode]));
    }

    sliderNodes.forEach((sliderNode) => {
        sliderNode.noUiSlider.on("slide", function (values, handle) {
            state.u(
                STATE_NUMERIC_FACET_VALUES,
                sliderNodes.map((n) => n.noUiSlider.get(true))
            );
        });
    });

    return filterNodes;
}

function countFilterControls(state) {
    let sliderNodes = [e("div", {name: "facetslider"}, []), e("div", {name: "facetslider"}, [])];
    let filterNodes = [];
    let intervals = state.g(STATE_COUNT_FILTER_INTERVALS);

    for (let i = 0; i < 2; i++) {
        let sliderNode = sliderNodes[i];

        let range;
        let name;

        if (i == 0) {
            range = intervals.source;
            name = `Number of ${state.g(STATE_SOURCE_TYPE)}s`;
        } else if (i == 1) {
            range = intervals.target;
            name = "Number of Genes Assayed";
        } else {
            continue;
        }

        noUiSlider.create(sliderNode, {
            start: [range[0], range[1]],
            step: 1,
            connect: true,
            range: {
                min: range[0],
                max: range[1],
            },
            pips: {
                mode: "range",
                density: 5,
            },
        });

        sliderNode.noUiSlider.on("start", function (values, handle) {
            sliderNode.noUiSlider.updateOptions({tooltips: [true, true]});
        });

        sliderNode.noUiSlider.on("end", function (values, handle) {
            sliderNode.noUiSlider.updateOptions({tooltips: [false, false]});
        });

        filterNodes.push(e("div", {class: "h-24 w-72"}, [e("div", name), sliderNode]));
    }

    sliderNodes.forEach((sliderNode) => {
        sliderNode.noUiSlider.on("slide", function (values, handle) {
            state.u(
                STATE_COUNT_FILTER_VALUES,
                sliderNodes.map((n) => n.noUiSlider.get(true))
            );
        });
    });

    return filterNodes;
}

function getFilterBody(state, genome, chroms, filter_values) {
    let filters = {
        filters: filter_values,
        chromosomes: genome.map((c) => c.chrom),
    };
    if (state.g(STATE_ZOOMED)) {
        let zoomChromoIndex = state.g(STATE_ZOOM_CHROMO_INDEX);
        filters.zoom = chroms[zoomChromoIndex].chrom;
    }

    return filters;
}

function mergeFilteredData(current_data, response_data) {
    let resp_obj = response_data.reduce((obj, chrom) => {
        obj[chrom.chrom] = chrom;
        return obj;
    }, {});

    return current_data.map((chrom) => {
        return chrom.chrom in resp_obj ? resp_obj[chrom.chrom] : chrom;
    });
}

function experimentsQuery(state) {
    let selectedExperiments = state.g(STATE_SELECTED_EXPERIMENTS);
    return selectedExperiments.map((e) => `exp=${e[0]}`).join("&");
}

function valueInterval(selector) {
    return (chroms, interval, chromoIndex) => {
        if (chromoIndex) {
            chroms = [chroms[chromoIndex]];
        }
        let max = Number.NEGATIVE_INFINITY;
        let min = Number.POSITIVE_INFINITY;
        for (const chrom of chroms) {
            const values = chrom[interval].map(selector);
            max = Math.max(max, Math.max(...values));
            min = Math.min(min, Math.min(...values));
        }

        if (max == Number.NEGATIVE_INFINITY || min == Number.POSITIVE_INFINITY) {
            return [0, 0];
        }

        return [min, max];
    };
}

const levelCountInterval = valueInterval((d) => d.count);
const sigInterval = valueInterval((d) => d.max_log10_sig);
const effectInterval = valueInterval((d) => d.max_abs_effect);

function coverageTypeFunctions(count, sig, effect) {
    return (state) => {
        const coverage_type = state.g(STATE_COVERAGE_TYPE);
        if (coverage_type == COVERAGE_TYPE_COUNT) {
            return count;
        } else if (coverage_type == COVERAGE_TYPE_SIG) {
            return sig;
        } else if (coverage_type == COVERAGE_TYPE_EFFECT) {
            return effect;
        }
    };
}

function coverageTypeDeferredFunctions(count, sig, effect) {
    return (state) => {
        const coverage_type = state.g(STATE_COVERAGE_TYPE);
        if (coverage_type == COVERAGE_TYPE_COUNT) {
            return count(state);
        } else if (coverage_type == COVERAGE_TYPE_SIG) {
            return sig(state);
        } else if (coverage_type == COVERAGE_TYPE_EFFECT) {
            return effect(state);
        }
    };
}

let getLegendIntervalFunc = coverageTypeFunctions(levelCountInterval, sigInterval, effectInterval);

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

function sourceTooltipDataLabel(state) {
    return [`${state.g(STATE_SOURCE_TYPE)} Count`, "Largest Significance", "Greatest Effect Size"];
}
let targetTooltipDataLabel = ["Gene Count", "Largest Significance", "Greatest Effect Size"];

let sourceLegendTitle = coverageTypeDeferredFunctions(
    (state) => `Number of ${state.g(STATE_SOURCE_TYPE)}s`,
    (state) => `${state.g(STATE_SOURCE_TYPE)} Effect Significance`,
    (state) => `${state.g(STATE_SOURCE_TYPE)} Effect Size`
);

let targetLegendTitle = coverageTypeFunctions(
    "Number of Genes Assayed",
    "Significance of Effect on Assayed Genes",
    "Size of Effect on Assayed Genes"
);

let sourceRenderDataTransform = coverageTypeDeferredFunctions(
    (state) => {
        return (d) => {
            let sourceCountInterval = state.g(STATE_COUNT_FILTER_INTERVALS).source;
            let sourceCountRange = sourceCountInterval[1] - sourceCountInterval[0];
            return (d.count - sourceCountInterval[0]) / sourceCountRange;
        };
    },
    (state) => (d) => {
        let significanceInterval = state.g(STATE_NUMERIC_FILTER_INTERVALS).sig;
        let significanceRange = significanceInterval[1] - significanceInterval[0];
        return (d.max_log10_sig - significanceInterval[0]) / significanceRange;
    },
    (state) => (d) => {
        let effectSizeInterval = state.g(STATE_NUMERIC_FILTER_INTERVALS).effect;
        let effectSizeRange = effectSizeInterval[1] - effectSizeInterval[0];
        return (d.max_abs_effect - effectSizeInterval[0]) / effectSizeRange;
    }
);

let targetRenderDataTransform = coverageTypeDeferredFunctions(
    (state) => {
        return (d) => {
            let targetCountInterval = state.g(STATE_COUNT_FILTER_INTERVALS).target;
            let targetCountRange = targetCountInterval[1] - targetCountInterval[0];
            return (d.count - targetCountInterval[0]) / targetCountRange;
        };
    },
    (state) => (d) => {
        let significanceInterval = state.g(STATE_NUMERIC_FILTER_INTERVALS).sig;
        let significanceRange = significanceInterval[1] - significanceInterval[0];
        return (d.max_log10_sig - significanceInterval[0]) / significanceRange;
    },
    (state) => (d) => {
        let effectSizeInterval = state.g(STATE_NUMERIC_FILTER_INTERVALS).effect;
        let effectSizeRange = effectSizeInterval[1] - effectSizeInterval[0];
        return (d.max_abs_effect - effectSizeInterval[0]) / effectSizeRange;
    }
);

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
    }
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
    }
);

function setFacetControls(state, categoricalFacetControls, defaultFacets, facets) {
    cc(categoricalFacetControls);
    categoricalFilterControls(facets, defaultFacets).forEach((element) => {
        a(categoricalFacetControls, element);
    });
    let facetCheckboxes = categoricalFacetControls.querySelectorAll("input[type=checkbox]");
    facetCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", (_) => {
            let checkedFacets = Array.from(facetCheckboxes) // Convert checkboxes to an array to use filter and map.
                .filter((i) => i.checked) // Use Array.filter to remove unchecked checkboxes.
                .map((i) => Number(i.id));
            state.u(STATE_CATEGORICAL_FACET_VALUES, checkedFacets);
        });
    });

    let effectSizeFilterInterval = facets.filter((f) => f.name === "Effect Size")[0].range;
    let sigFilterInterval = facets.filter((f) => f.name === "Significance")[0].range64;
    state.u(STATE_NUMERIC_FILTER_INTERVALS, {effect: effectSizeFilterInterval, sig: sigFilterInterval});
}

function setCountControls(state, coverageData) {
    let sourceCountInterval = levelCountInterval(coverageData, "source_intervals");
    let targetCountInterval = levelCountInterval(coverageData, "target_intervals");
    state.u(STATE_COUNT_FILTER_INTERVALS, {source: sourceCountInterval, target: targetCountInterval});
    state.u(STATE_COUNT_FILTER_VALUES, [sourceCountInterval, targetCountInterval]);
}

function setLegendIntervals(state, coverageData) {
    let legendInterval = getLegendIntervalFunc(state);
    let sourceLegendInterval = legendInterval(coverageData, "source_intervals");
    let targetLegendInterval = legendInterval(coverageData, "target_intervals");
    state.u(STATE_LEGEND_INTERVALS, {source: sourceLegendInterval, target: targetLegendInterval});
}

function getHighlightRegions(regionUploadInput, regionReader) {
    if (regionUploadInput.files.length != 1) {
        return;
    }
    regionReader.readAsText(regionUploadInput.files[0]);
}

function coverageValue(selectedCoverageType) {
    if (selectedCoverageType == "count") {
        return COVERAGE_TYPE_COUNT;
    } else if (selectedCoverageType == "sig") {
        return COVERAGE_TYPE_SIG;
    } else if (selectedCoverageType == "effect") {
        return COVERAGE_TYPE_EFFECT;
    }
}

async function getCombinedCoverageData(staticRoot, accessionIDs) {
    let manifests;
    let genome;
    try {
        manifests = await Promise.all(
            accessionIDs.map((accessionIDPair) =>
                getJson(
                    `${staticRoot}search/experiments/${accessionIDPair[0]}/${accessionIDPair[1]}/coverage_manifest.json`
                )
            )
        );

        let genomeNames = manifests.map((m) => m.genome.name);
        if (genomeNames.some((g) => g != genomeNames[0])) {
            throw new GenomeError("Experiment analyses based on different genomes and are incompatible.");
        }

        genome = await getJson(
            `${staticRoot}search/experiments/${accessionIDs[0][0]}/${accessionIDs[0][1]}/${manifests[0].genome.file}`
        );
    } catch (error) {
        let consoleError;
        if (error instanceof Error) {
            consoleError = "Files necessary to load coverage not found.";
        } else if (error instanceof GenomeError) {
            consoleError = error.message;
        }

        throw new Error(consoleError);
    }

    return [genome, manifests];
}

export async function combined_viz(staticRoot, csrfToken, loggedIn) {
    let experiment_info = JSON.parse(g("experiment_viz").innerText);
    let accessionIDs = experiment_info.map((exp) => [exp.accession_id, exp.analysis_accession_id]);
    let genome, manifests;
    try {
        [genome, manifests] = await getCombinedCoverageData(staticRoot, accessionIDs);
    } catch (error) {
        console.log(error);
        return;
    }
    let genomeName = manifests[0].genome.name;

    rc(g("chrom-data-header"), t("Experiment Coverage"));

    const genomeRenderer = new GenomeRenderer(genome);

    let sourceType = experiment_info.length == 1 ? experiment_info[0].source : "Tested Elements";

    let state = build_state(manifests, genomeRenderer, accessionIDs, sourceType);

    // Get data

    render(state, genomeRenderer);

    genomeRenderer.onBucketClick = (i, chromName, start, end, renderer) => {
        let zoomed = state.g(STATE_ZOOMED);
        if (zoomed) {
            window.open(`/search/results/?query=chr${chromName}:${start}-${end}+${genomeName}`, "_blank");
        } else {
            state.u(STATE_VIEWBOX, [
                renderer.renderContext.xInset +
                    renderer.renderContext.toPx(start) * 30 -
                    renderer.renderContext.viewHeight / 6,
                renderer.renderContext.yInset +
                    (renderer.chromDimensions.chromHeight + renderer.chromDimensions.chromSpacing) * i * 15 -
                    renderer.renderContext.viewHeight / 6,
                renderer.renderContext.viewWidth,
                renderer.renderContext.viewHeight,
            ]);
            state.u(STATE_ZOOM_CHROMO_INDEX, i);
            state.u(STATE_ZOOMED, !zoomed);
        }
    };

    genomeRenderer.onBackgroundClick = (rect, renderer) => {
        let zoomed = state.g(STATE_ZOOMED);
        if (zoomed) {
            state.u(STATE_VIEWBOX, [0, 0, renderer.renderContext.viewWidth, renderer.renderContext.viewHeight]);
            state.u(STATE_ZOOM_CHROMO_INDEX, undefined);
            state.u(STATE_ZOOMED, !zoomed);
        }
    };

    countFilterControls(state).forEach((element) => {
        a(g("chrom-data-counts"), element);
    });

    state.ac(STATE_ZOOMED, (s, key) => {
        const zoomed = s[key];
        state.u(STATE_SCALE, zoomed ? 15 : 1);
        state.u(STATE_SCALE_X, zoomed ? 30 : 1);
        state.u(STATE_SCALE_Y, zoomed ? 15 : 1);

        let body = getFilterBody(state, genome, manifest.chromosomes, [
            state.g(STATE_CATEGORICAL_FACET_VALUES),
            state.g(STATE_NUMERIC_FACET_VALUES),
        ]);

        postJson(`/search/experiment_coverage?${experimentsQuery(state)}`, JSON.stringify(body)).then(
            (response_json) => {
                state.u(
                    STATE_COVERAGE_DATA,
                    mergeFilteredData(state.g(STATE_COVERAGE_DATA), response_json.chromosomes)
                );
            }
        );
    });

    state.ac(STATE_ALL_FILTERED, (s, key) => {
        render(state, genomeRenderer);
    });

    state.ac(
        STATE_CATEGORICAL_FACET_VALUES,
        debounce((s, key) => {
            // Send facet data to server to get filtered data and updated numeric facets
            let body = getFilterBody(state, genome, manifest.chromosomes, [state.g(STATE_CATEGORICAL_FACET_VALUES)]);

            postJson(`/search/experiment_coverage?${experimentsQuery(state)}`, JSON.stringify(body)).then(
                (response_json) => {
                    state.u(
                        STATE_COVERAGE_DATA,
                        mergeFilteredData(state.g(STATE_COVERAGE_DATA), response_json.chromosomes)
                    );
                    state.u(STATE_NUMERIC_FILTER_INTERVALS, response_json.numeric_intervals);
                    state.u(
                        STATE_NUMERIC_FACET_VALUES,
                        [response_json.numeric_intervals.effect, response_json.numeric_intervals.sig],
                        false
                    );
                    state.u(STATE_ITEM_COUNTS, [
                        response_json.reo_count,
                        response_json.source_count,
                        response_json.target_count,
                    ]);
                }
            );
        }, 300)
    );

    state.ac(
        STATE_NUMERIC_FACET_VALUES,
        debounce((s, key) => {
            // Send facet data to server to get filtered data and updated numeric facets
            let body = getFilterBody(state, genome, manifest.chromosomes, [
                state.g(STATE_CATEGORICAL_FACET_VALUES),
                state.g(STATE_NUMERIC_FACET_VALUES),
            ]);

            postJson(`/search/experiment_coverage?${experimentsQuery(state)}`, JSON.stringify(body)).then(
                (response_json) => {
                    state.u(
                        STATE_COVERAGE_DATA,
                        mergeFilteredData(state.g(STATE_COVERAGE_DATA), response_json.chromosomes)
                    );
                    state.u(STATE_ITEM_COUNTS, [
                        response_json.reo_count,
                        response_json.source_count,
                        response_json.target_count,
                    ]);
                }
            );
        }, 300)
    );

    state.ac(STATE_NUMERIC_FILTER_INTERVALS, (s, key) => {
        cc(g("chrom-data-numeric-facets"));
        numericFilterControls(state, state.g(STATE_FACETS)).forEach((element) =>
            a(g("chrom-data-numeric-facets"), element)
        );
    });

    state.ac(STATE_COUNT_FILTER_INTERVALS, (s, key) => {
        cc(g("chrom-data-counts"));
        countFilterControls(state).forEach((element) => a(g("chrom-data-counts"), element));
    });

    let countFacetWorker;
    if (window.Worker) {
        countFacetWorker = new Worker("/static/search/js/exp_viz/countFacetFilterWorker.js");
        countFacetWorker.onmessage = (cf) => {
            state.u(STATE_ALL_FILTERED, cf.data);
        };
    }

    state.ac(
        STATE_COUNT_FILTER_VALUES,
        debounce((s, key) => {
            if (countFacetWorker) {
                countFacetWorker.postMessage({
                    data: state.g(STATE_COVERAGE_DATA),
                    countFilters: state.g(STATE_COUNT_FILTER_VALUES),
                });
            }
        }, 60)
    );

    state.ac(STATE_HIGHLIGHT_REGIONS, (s, key) => {
        render(state, genomeRenderer);
    });

    let categoricalFacetControls = g("chrom-data-categorical-facets");

    state.ac(STATE_FACETS, (s, key) => {
        setFacetControls(state, categoricalFacetControls, [], s[key]);
    });

    setFacetControls(state, categoricalFacetControls, state.g(STATE_CATEGORICAL_FACET_VALUES), state.g(STATE_FACETS));

    state.ac(STATE_COVERAGE_DATA, (s, key) => {
        setCountControls(state, s[key]);
        setLegendIntervals(state, s[key]);
    });

    //
    // Highlight regions
    //
    let regionReader = new FileReader();
    regionReader.addEventListener(
        "load",
        () => {
            state.u(STATE_HIGHLIGHT_REGIONS, getRegions(regionReader.result));
            let highlightResetButton = e("input", {type: "button", value: "Reset Highlights"}, []);
            highlightResetButton.addEventListener("click", () => {
                state.u(STATE_HIGHLIGHT_REGIONS, {});
                cc(g("regionUploadInputReset"));
            });
            rc(g("regionUploadInputReset"), highlightResetButton);
        },
        false
    );
    let regionUploadInput = g("regionUploadInput");

    regionUploadInput.addEventListener("change", () => getHighlightRegions(regionUploadInput, regionReader), false);

    //
    // Data downloads
    //
    if (loggedIn) {
        let dataDownloadInput = g("dataDownloadInput");
        dataDownloadInput.addEventListener(
            "change",
            () =>
                getDownloadRegions(
                    [state.g(STATE_CATEGORICAL_FACET_VALUES), state.g(STATE_NUMERIC_FACET_VALUES)],
                    dataDownloadInput,
                    exprAccessionID,
                    csrfToken
                ),
            false
        );

        let dataDownloadAll = g("dataDownloadAll");
        dataDownloadAll.addEventListener(
            "click",
            () =>
                getDownloadAll(
                    [state.g(STATE_CATEGORICAL_FACET_VALUES), state.g(STATE_NUMERIC_FACET_VALUES)],
                    exprAccessionID,
                    csrfToken
                ),
            false
        );
    }

    //
    // Coverage Type Selector
    //
    let coverageSelector = g("covSelect");
    coverageSelector.addEventListener(
        "change",
        () => {
            let selectedCoverageType = coverageSelector.value;
            state.u(STATE_COVERAGE_TYPE, coverageValue(selectedCoverageType));
        },
        false
    );

    state.ac(STATE_COVERAGE_TYPE, (s, key) => {
        setLegendIntervals(state, state.g(STATE_COVERAGE_DATA));
        render(state, genomeRenderer);
    });
}
