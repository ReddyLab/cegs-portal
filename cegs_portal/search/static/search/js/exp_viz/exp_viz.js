import {a, cc, e, g, rc, t} from "../dom.js";
import {State} from "../state.js";
import {getRegions} from "../bed.js";
import {getJson, postJson} from "../files.js";
import {Legend} from "./obsLegend.js";
import {GenomeRenderer} from "./chromosomeSvg.js";
import {getDownloadRegions, getDownloadAll} from "./downloads.js";

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

function build_state(manifest, genomeRenderer, exprAccessionID, analysisAccessionID, sourceType) {
    let coverageData = manifest.chromosomes;
    let facets = manifest.facets;
    let default_facets = manifest.hasOwnProperty("default_facets") ? manifest.default_facets : [];
    let reoCount = manifest.reo_count;
    let sourceCount = manifest.source_count;
    let targetCount = manifest.target_count;
    let sourceCountInterval = levelCountInterval(coverageData, "source_intervals");
    let targetCountInterval = levelCountInterval(coverageData, "target_intervals");
    let effectSizeFilterInterval = facets.filter((f) => f.name === "Effect Size")[0].range;
    let sigFilterInterval = facets.filter((f) => f.name === "Significance")[0].range;
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
        [STATE_SELECTED_EXPERIMENTS]: [exprAccessionID],
        [STATE_ITEM_COUNTS]: [reoCount, sourceCount, targetCount],
        [STATE_SOURCE_TYPE]: sourceType,
        [STATE_ANALYSIS]: analysisAccessionID,
        [STATE_COVERAGE_TYPE]: coverageValue(coverageSelectorValue),
        [STATE_LEGEND_INTERVALS]: {
            source: legendIntervalFunc(coverageData, "source_intervals"),
            target: legendIntervalFunc(coverageData, "target_intervals"),
        },
    });

    return state;
}

async function getCoverageData(staticRoot, exprAccessionID, analysisAccessionID) {
    let manifest;
    let genome;
    try {
        manifest = await getJson(
            `${staticRoot}search/experiments/${exprAccessionID}/${analysisAccessionID}/coverage_manifest.json`
        );
        genome = await getJson(
            `${staticRoot}search/experiments/${exprAccessionID}/${analysisAccessionID}/${manifest.genome.file}`
        );
    } catch (error) {
        throw new Error("Files necessary to load coverage not found");
    }

    return [genome, manifest];
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
            tooltipDataSelectors(state),
            sourceTooltipDataLabel(state),
            targetTooltipDataLabel(state),
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

        if (facet.name === "Effect Size") {
            range = intervals.effect;
        } else if (facet.name === "Significance") {
            range = intervals.sig;
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

        filterNodes.push(e("div", {class: "h-24 w-72"}, [e("div", facet.name), sliderNode]));
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
    return selectedExperiments.map((e) => `exp=${e}`).join("&");
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
const sigInterval = valueInterval((d) => d.min_sig);
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

let tooltipDataSelectors = coverageTypeFunctions(
    (d) => d.count,
    (d) => d.min_sig,
    (d) => d.max_abs_effect
);

let sourceTooltipDataLabel = coverageTypeDeferredFunctions(
    (state) => {
        return `${state.g(STATE_SOURCE_TYPE)} Count`;
    },
    (state) => "Significance",
    (state) => "Effect Size"
);
let targetTooltipDataLabel = coverageTypeFunctions("Gene Count", "Significance", "Effect Size");

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
    (state) => (d) => d.min_sig / 0.05,
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
    (state) => (d) => d.min_sig / 0.05,
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
        color: d3.interpolateCool,
        faded: d3.interpolateCubehelixLong(d3.cubehelix(-260, 0.75, 0.95), d3.cubehelix(80, 1.5, 0.95)),
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
        color: d3.interpolateWarm,
        faded: d3.interpolateCubehelixLong(d3.cubehelix(-100, 0.75, 0.95), d3.cubehelix(80, 1.5, 0.95)),
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
    let sigFilterInterval = facets.filter((f) => f.name === "Significance")[0].range;
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

export async function exp_viz(staticRoot, exprAccessionID, analysisAccessionID, csrfToken, sourceType, loggedIn) {
    let genome, manifest;
    try {
        [genome, manifest] = await getCoverageData(staticRoot, exprAccessionID, analysisAccessionID);
    } catch (error) {
        console.log(error);
        return;
    }
    let genomeName = manifest.genome.name;

    rc(g("chrom-data-header"), t("Experiment Coverage"));

    const genomeRenderer = new GenomeRenderer(genome);

    let state = build_state(manifest, genomeRenderer, exprAccessionID, analysisAccessionID, sourceType);

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
        _.debounce((s, key) => {
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
                    state.u(STATE_ITEM_COUNTS, response_json.item_counts);
                }
            );
        }, 300)
    );

    state.ac(
        STATE_NUMERIC_FACET_VALUES,
        _.debounce((s, key) => {
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
                    state.u(STATE_ITEM_COUNTS, response_json.item_counts);
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
        _.debounce((s, key) => {
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
