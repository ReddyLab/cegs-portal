import {a, cc, e, g, rc, t} from "../dom.js";
import {State} from "../state.js";
import {getRegions} from "../bed.js";
import {getJson, postJson} from "../files.js";
import {GenomeRenderer} from "./chromosomeSvg.js";
import {getDownloadRegions, getDownloadAll} from "./downloads.js";
import {debounce} from "../utils.js";
import {render} from "./render.js";
import {getHighlightRegions} from "./highlightRegions.js";
import {mergeFilteredData} from "./coverageData.js";
import {coverageValue, effectInterval, levelCountInterval, sigInterval} from "./covTypeUtils.js";
import {
    STATE_ZOOMED,
    STATE_ZOOM_CHROMO_INDEX,
    STATE_SCALE,
    STATE_SCALE_X,
    STATE_SCALE_Y,
    STATE_VIEWBOX,
    STATE_FACETS,
    STATE_CATEGORICAL_FACET_VALUES,
    STATE_NUMERIC_FACET_VALUES,
    STATE_COUNT_FILTER_VALUES,
    STATE_COVERAGE_DATA,
    STATE_ALL_FILTERED,
    STATE_NUMERIC_FILTER_INTERVALS,
    STATE_COUNT_FILTER_INTERVALS,
    STATE_HIGHLIGHT_REGIONS,
    STATE_SELECTED_EXPERIMENTS,
    STATE_ITEM_COUNTS,
    STATE_SOURCE_TYPE,
    STATE_COVERAGE_TYPE,
    STATE_LEGEND_INTERVALS,
    STATE_FEATURE_FILTER_TYPE,
} from "./consts.js";
import {
    numericFilterControls,
    countFilterControls,
    getFilterBody,
    setFacetControls,
    setCountControls,
    setLegendIntervals,
} from "./ui.js";

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
        [STATE_FEATURE_FILTER_TYPE]: "sources",
    });

    return state;
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

        genome = await getJson(`${staticRoot}genome_data/${manifests[0].genome.file}`);
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

    rc(g("chrom-data-header"), t("Experiment Overview"));

    const genomeRenderer = new GenomeRenderer(genome);

    let sourceType = experiment_info.length == 1 ? experiment_info[0].source : "Tested Element";

    let state = build_state(manifests, genomeRenderer, accessionIDs, sourceType);

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

        let body = getFilterBody(state, genome, manifests[0].chromosomes, [
            state.g(STATE_CATEGORICAL_FACET_VALUES),
            state.g(STATE_NUMERIC_FACET_VALUES),
        ]);

        postJson("/search/combined_experiment_coverage", JSON.stringify(body)).then((response_json) => {
            state.u(STATE_COVERAGE_DATA, mergeFilteredData(state.g(STATE_COVERAGE_DATA), response_json.chromosomes));
        });
    });

    state.ac(STATE_ALL_FILTERED, (s, key) => {
        render(state, genomeRenderer);
    });

    function get_all_data() {
        let body = getFilterBody(state, genome, manifests[0].chromosomes, [state.g(STATE_CATEGORICAL_FACET_VALUES)]);

        postJson("/search/combined_experiment_coverage", JSON.stringify(body)).then((response_json) => {
            state.u(STATE_COVERAGE_DATA, mergeFilteredData(state.g(STATE_COVERAGE_DATA), response_json.chromosomes));
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
        });
    }

    get_all_data();

    state.ac(
        STATE_CATEGORICAL_FACET_VALUES,
        debounce((s, key) => get_all_data(), 300)
    );

    state.ac(
        STATE_NUMERIC_FACET_VALUES,
        debounce((s, key) => {
            // Send facet data to server to get filtered data and updated numeric facets
            let body = getFilterBody(state, genome, manifests[0].chromosomes, [
                state.g(STATE_CATEGORICAL_FACET_VALUES),
                state.g(STATE_NUMERIC_FACET_VALUES),
            ]);

            postJson("/search/combined_experiment_coverage", JSON.stringify(body)).then((response_json) => {
                state.u(
                    STATE_COVERAGE_DATA,
                    mergeFilteredData(state.g(STATE_COVERAGE_DATA), response_json.chromosomes)
                );
                state.u(STATE_ITEM_COUNTS, [
                    response_json.reo_count,
                    response_json.source_count,
                    response_json.target_count,
                ]);
            });
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

    //
    // Feature Filter Selector
    //
    let featureFilterSelector = g("feature-select");
    featureFilterSelector.value = "sources";
    featureFilterSelector.addEventListener(
        "change",
        () => {
            state.u(STATE_FEATURE_FILTER_TYPE, featureFilterSelector.value);
        },
        false
    );

    state.ac(STATE_FEATURE_FILTER_TYPE, (s, key) => {
        get_all_data();
    });
}
