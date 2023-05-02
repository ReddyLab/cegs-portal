import {a, cc, e, g, rc, t} from "../dom.js";
import {State} from "../state.js";
import {getRegions} from "../bed.js";
import {getJson, postJson} from "../files.js";
import {Legend} from "./obsLegend.js";
import {sourceColors, targetColors, GenomeRenderer} from "./chromosomeSvg.js";

const STATE_ZOOMED = "state-zoomed";
const STATE_ZOOM_CHROMO_INDEX = "state-zoom-chromo-index";
const STATE_SCALE = "state-scale";
const STATE_SCALE_X = "state-scale-x";
const STATE_SCALE_Y = "state-scale-y";
const STATE_VIEWBOX = "state-viewbox";
const STATE_FACETS = "state-facets";
const STATE_DISCRETE_FACET_VALUES = "state-discrete-facets";
const STATE_CONTINUOUS_FACET_VALUES = "state-continuous-facets";
const STATE_COUNT_FILTER_VALUES = "state-count-filter";
const STATE_COVERAGE_DATA = "state-coverage-data";
const STATE_ALL_FILTERED = "state-all-filtered";
const STATE_CONTINUOUS_FILTER_INTERVALS = "state-continuous-filter-intervals";
const STATE_COUNT_FILTER_INTERVALS = "state-count-filter-intervals";
const STATE_HIGHLIGHT_REGIONS = "state-highlight-regions";
const STATE_SELECTED_EXPERIMENTS = "state-selected-experiments";

function build_state(coverageData, facets, genomeRenderer, exprAccessionID) {
    let sourceCountInterval = levelCountInterval(coverageData, "source_intervals");
    let targetCountInterval = levelCountInterval(coverageData, "target_intervals");
    let effectSizeInterval = facets.filter((f) => f.name === "Effect Size")[0].range;
    let sigInterval = facets.filter((f) => f.name === "Significance")[0].range;

    let state = new State({
        [STATE_ZOOMED]: false,
        [STATE_ZOOM_CHROMO_INDEX]: undefined,
        [STATE_SCALE]: 1,
        [STATE_SCALE_X]: 1,
        [STATE_SCALE_Y]: 1,
        [STATE_VIEWBOX]: [0, 0, genomeRenderer.renderContext.viewWidth, genomeRenderer.renderContext.viewHeight],
        [STATE_FACETS]: facets,
        [STATE_DISCRETE_FACET_VALUES]: [],
        [STATE_COVERAGE_DATA]: coverageData,
        [STATE_ALL_FILTERED]: coverageData,
        [STATE_CONTINUOUS_FILTER_INTERVALS]: {effect: effectSizeInterval, sig: sigInterval},
        [STATE_CONTINUOUS_FACET_VALUES]: [effectSizeInterval, sigInterval],
        [STATE_COUNT_FILTER_INTERVALS]: {source: sourceCountInterval, target: targetCountInterval},
        [STATE_COUNT_FILTER_VALUES]: [sourceCountInterval, targetCountInterval],
        [STATE_HIGHLIGHT_REGIONS]: {},
        [STATE_SELECTED_EXPERIMENTS]: [exprAccessionID],
    });

    return state;
}

async function getCoverageData(staticRoot, exprAccessionID) {
    let manifest;
    let genome;
    try {
        manifest = await getJson(`${staticRoot}search/experiments/${exprAccessionID}/coverage_manifest.json`);
        genome = await getJson(`${staticRoot}search/experiments/${exprAccessionID}/${manifest.genome.file}`);
        // genomeName = manifest.genome.name;
        // coverageData = manifest.chromosomes;
        // facets = manifest.facets;
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
    let countIntervals = state.g(STATE_COUNT_FILTER_INTERVALS);
    let sourceCountInterval = countIntervals.source;
    let targetCountInterval = countIntervals.target;

    rc(
        g("chrom-data"),
        genomeRenderer.render(
            currentLevel,
            focusIndex,
            sourceCountInterval,
            targetCountInterval,
            viewBox,
            scale,
            scaleX,
            scaleY,
            highlightRegions
        )
    );
    rc(
        g("chrom-data-legend"),
        Legend(d3.scaleSequential(sourceCountInterval, sourceColors), {
            title: "Source Count",
        })
    );
    a(
        g("chrom-data-legend"),
        Legend(d3.scaleSequential(targetCountInterval, targetColors), {
            title: "Target Count",
        })
    );
}

function discreteFilterControls(facets) {
    return facets
        .filter((f) => f.facet_type == "FacetType.DISCRETE")
        .map((facet) => {
            return e("fieldset", {name: "facetfield", class: "my-4"}, [
                e("legend", {class: "font-bold"}, facet.name),
                e(
                    "div",
                    {class: "flex flex-row flex-wrap gap-1"},
                    Object.entries(facet.values).map((entry) => {
                        return e("div", {class: "ml-1"}, [
                            e("input", {type: "checkbox", id: entry[0], name: facet.name}, []),
                            e("label", {for: entry[0]}, entry[1]),
                        ]);
                    })
                ),
            ]);
        });
}

function continuousFilterControls(state, facets) {
    const contFacets = facets.filter((f) => f.facet_type == "FacetType.CONTINUOUS");
    let sliderNodes = [e("div", {name: "facetslider"}, []), e("div", {name: "facetslider"}, [])];
    let filterNodes = [];
    let intervals = state.g(STATE_CONTINUOUS_FILTER_INTERVALS);

    for (let i = 0; i < contFacets.length; i++) {
        let facet = contFacets[i];
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
                STATE_CONTINUOUS_FACET_VALUES,
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
            name = "Source Count";
        } else if (i == 1) {
            range = intervals.target;
            name = "Target count";
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

function levelCountInterval(chroms, interval, chromoIndex) {
    if (chromoIndex) {
        chroms = [chroms[chromoIndex]];
    }
    let max = Number.NEGATIVE_INFINITY;
    let min = Number.POSITIVE_INFINITY;
    for (const chrom of chroms) {
        const count = chrom[interval].map((d) => d.count);
        max = Math.max(max, Math.max(...count));
        min = Math.min(min, Math.min(...count));
    }

    if (max == Number.NEGATIVE_INFINITY || min == Number.POSITIVE_INFINITY) {
        return [0, 0];
    }

    return [min, max];
}

function setFacetControls(state, discreteFacets, facets) {
    cc(discreteFacets);
    discreteFilterControls(facets).forEach((element) => {
        a(discreteFacets, element);
    });
    let facetCheckboxes = discreteFacets.querySelectorAll("input[type=checkbox]");
    facetCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", (_) => {
            let checkedFacets = Array.from(facetCheckboxes) // Convert checkboxes to an array to use filter and map.
                .filter((i) => i.checked) // Use Array.filter to remove unchecked checkboxes.
                .map((i) => Number(i.id));
            state.u(STATE_DISCRETE_FACET_VALUES, checkedFacets);
        });
    });

    let effectSizeInterval = facets.filter((f) => f.name === "Effect Size")[0].range;
    let sigInterval = facets.filter((f) => f.name === "Significance")[0].range;
    state.u(STATE_CONTINUOUS_FILTER_INTERVALS, {effect: effectSizeInterval, sig: sigInterval});
}

function setCountControls(state, coverageData) {
    let sourceCountInterval = levelCountInterval(coverageData, "source_intervals");
    let targetCountInterval = levelCountInterval(coverageData, "target_intervals");
    state.u(STATE_COUNT_FILTER_INTERVALS, {source: sourceCountInterval, target: targetCountInterval});
    state.u(STATE_COUNT_FILTER_VALUES, [sourceCountInterval, targetCountInterval]);
}

function getHighlightRegions(regionUploadInput, regionReader) {
    if (regionUploadInput.files.length != 1) {
        return;
    }
    regionReader.readAsText(regionUploadInput.files[0]);
}

export async function exp_viz(staticRoot, exprAccessionID) {
    let genome, manifest;
    try {
        [genome, manifest] = await getCoverageData(staticRoot, exprAccessionID);
    } catch (error) {
        console.log(error);
        return;
    }
    const genomeRenderer = new GenomeRenderer(genome);

    let state = build_state(manifest.chromosomes, manifest.facets, genomeRenderer, exprAccessionID);

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

    rc(g("chrom-data-header"), t("Experiment Coverage"));

    countFilterControls(state).forEach((element) => {
        a(g("chrom-data-counts"), element);
    });

    state.ac(STATE_ZOOMED, (s, key) => {
        const zoomed = s[key];
        state.u(STATE_SCALE, zoomed ? 15 : 1);
        state.u(STATE_SCALE_X, zoomed ? 30 : 1);
        state.u(STATE_SCALE_Y, zoomed ? 15 : 1);

        let body = getFilterBody(state, genome, manifest.chromosomes, [
            state.g(STATE_DISCRETE_FACET_VALUES),
            state.g(STATE_CONTINUOUS_FACET_VALUES),
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
        STATE_DISCRETE_FACET_VALUES,
        _.debounce((s, key) => {
            // Send facet data to server to get filtered data and updated continuous facets
            let body = getFilterBody(state, genome, manifest.chromosomes, [state.g(STATE_DISCRETE_FACET_VALUES)]);

            postJson(`/search/experiment_coverage?${experimentsQuery(state)}`, JSON.stringify(body)).then(
                (response_json) => {
                    state.u(
                        STATE_COVERAGE_DATA,
                        mergeFilteredData(state.g(STATE_COVERAGE_DATA), response_json.chromosomes)
                    );
                    state.u(STATE_CONTINUOUS_FILTER_INTERVALS, response_json.continuous_intervals);
                    state.u(
                        STATE_CONTINUOUS_FACET_VALUES,
                        [response_json.continuous_intervals.effect, response_json.continuous_intervals.sig],
                        false
                    );
                }
            );
        }, 300)
    );

    state.ac(
        STATE_CONTINUOUS_FACET_VALUES,
        _.debounce((s, key) => {
            // Send facet data to server to get filtered data and updated continuous facets
            let body = getFilterBody(state, genome, manifest.chromosomes, [
                state.g(STATE_DISCRETE_FACET_VALUES),
                state.g(STATE_CONTINUOUS_FACET_VALUES),
            ]);

            postJson(`/search/experiment_coverage?${experimentsQuery(state)}`, JSON.stringify(body)).then(
                (response_json) => {
                    state.u(
                        STATE_COVERAGE_DATA,
                        mergeFilteredData(state.g(STATE_COVERAGE_DATA), response_json.chromosomes)
                    );
                }
            );
        }, 300)
    );

    state.ac(STATE_CONTINUOUS_FILTER_INTERVALS, (s, key) => {
        cc(g("chrom-data-continuous-facets"));
        continuousFilterControls(state, state.g(STATE_FACETS)).forEach((element) =>
            a(g("chrom-data-continuous-facets"), element)
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

    let discreteFacets = g("chrom-data-discrete-facets");

    state.ac(STATE_FACETS, (s, key) => {
        setFacetControls(state, discreteFacets, s[key]);
    });

    state.ac(STATE_COVERAGE_DATA, (s, key) => {
        setCountControls(state, s[key]);
    });

    setFacetControls(state, discreteFacets, state.g(STATE_FACETS));

    let regionReader = new FileReader();
    regionReader.addEventListener(
        "load",
        () => {
            state.u(STATE_HIGHLIGHT_REGIONS, getRegions(regionReader.result));
        },
        false
    );
    let regionUploadInput = g("regionUploadInput");

    regionUploadInput.addEventListener("change", () => getHighlightRegions(regionUploadInput, regionReader), false);
}
