import {a, cc, e, g, rc, t} from "../dom.js";
import {State} from "../state.js";
import {getRegions} from "../bed.js";
import {getJson, postJson} from "../files.js";
import {GenomeRenderer, BucketLocation, ChromRange} from "./chromosomeSvg.js";
import {getDownloadRegions, getDownloadAll} from "./downloads.js";
import {debounce} from "../utils.js";
import {render} from "./render.js";
import {getHighlightRegions} from "./highlightRegions.js";
import {mergeFilteredData} from "./coverageData.js";
import {coverageValue, effectInterval, levelCountInterval, sigInterval} from "./covTypeUtils.js";
import {
    STATE_ZOOMED,
    STATE_ZOOM_GENOME_LOCATION,
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
    STATE_COMBO_SET_OP,
} from "./consts.js";
import {
    numericFilterControls,
    countFilterControls,
    getFilterBody,
    setFacetControls,
    setCountControls,
    setLegendIntervals,
} from "./ui.js";

function union_array(arr1, arr2) {
    if (arr1.length == 0) {
        return arr2.slice();
    }

    if (arr2.length == 0) {
        return arr1.slice();
    }

    let union = arr1.slice();
    for (let val of arr2) {
        if (arr1.indexOf(val) == -1) {
            union.push(val);
        }
    }

    return union;
}

function union_obj(obj1, obj2) {
    let union = {};
    for (let key in obj1) {
        union[key] = obj1[key];
    }

    for (let key in obj2) {
        if (!union.hasOwnProperty(key)) union[key] = obj2[key];
    }
    return union;
}

function distinct(sortedArray) {
    let newArray = [sortedArray[0]];
    for (let element of sortedArray) {
        if (element != newArray[newArray.length - 1]) {
            newArray.push(element);
        }
    }
    return newArray;
}

// Merge is the intersection of facets
function merge_facets(experiments_facets) {
    if (experiments_facets.length == 1) {
        return experiments_facets[0];
    }

    // Create an array of objects mapping facet ids to facets
    let facet_maps = experiments_facets.map((facet_array) =>
        facet_array.reduce((acc, f) => {
            acc[f.id] = f;
            return acc;
        }, {}),
    );

    // Get the IDs of facets that are in all experiments
    let facet_id_arrays = experiments_facets.map((facet_array) => facet_array.map((f) => f.id));
    let facet_id_union = facet_id_arrays.slice(1).reduce((acc, ids) => union_array(acc, ids), facet_id_arrays[0]);
    let new_facets = {};

    for (let facet_id of facet_id_union) {
        for (let facet_set of facet_maps) {
            let curr_facet = facet_set[facet_id];
            if (curr_facet === undefined) continue;

            let new_facet = new_facets[facet_id];
            if (new_facet === undefined) {
                new_facets[facet_id] = curr_facet;
                continue;
            }

            if (new_facet.facet_type == "FacetType.CATEGORICAL") {
                new_facet.values = union_obj(curr_facet.values, new_facet.values);
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
    }

    return Object.values(new_facets);
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
        [STATE_ZOOM_GENOME_LOCATION]: undefined,
        [STATE_VIEWBOX]: [0, 0, genomeRenderer.renderContext.viewWidth, genomeRenderer.renderContext.viewHeight],
        [STATE_FACETS]: facets,
        [STATE_CATEGORICAL_FACET_VALUES]: default_facets.map((i) => String(i)),
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
        [STATE_FEATURE_FILTER_TYPE]: g("feature-select").value,
        [STATE_COMBO_SET_OP]: g("set-op-select").value,
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
                    `${staticRoot}search/experiments/${accessionIDPair[0]}/${accessionIDPair[1]}/coverage_manifest.json`,
                ),
            ),
        );
        genome = await getJson(`${staticRoot}genome_data/${manifests[0].genome.file}`);
    } catch (error) {
        let consoleError;
        if (error instanceof Error) {
            consoleError = "Files necessary to load coverage not found.";
        }

        throw new Error(consoleError);
    }

    return [genome, manifests];
}

function multipleGenomeAssemblyError(genomeNames) {
    let message = `These experiment analyses are based on different genomes (${genomeNames.join(", ")}) and cannot be compared.`;
    let chromData = document.getElementById("chrom-error");
    a(chromData, e("div", {class: "comparison-error inline-block"}, t(message)));
}

export async function combined_viz(staticRoot, csrfToken, loggedIn) {
    let experiment_info = JSON.parse(g("experiment_viz").innerText);
    let accessionIDs = experiment_info.map((exp) => [exp.accession_id, exp.analysis_accession_id]);
    let genomeNames = distinct(experiment_info.map((exp) => exp.genome_assembly).sort());
    if (genomeNames.length > 1) {
        multipleGenomeAssemblyError(genomeNames);
        return;
    }

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
                    renderer.renderContext.toPx(start + (end - start) / 2) * renderer.renderContext.scaleX(true) -
                    renderer.renderContext.viewWidth / 2,
                renderer.renderContext.yInset +
                    (renderer.chromDimensions.chromHeight + renderer.chromDimensions.chromSpacing) *
                        i *
                        renderer.renderContext.scaleY(true) -
                    renderer.renderContext.viewHeight / 6,
                renderer.renderContext.viewWidth,
                renderer.renderContext.viewHeight,
            ]);
            state.u(STATE_ZOOM_GENOME_LOCATION, new BucketLocation(i, new ChromRange(start, end)));
            state.u(STATE_ZOOMED, true);
        }
    };

    genomeRenderer.onBackgroundClick = (rect, renderer) => {
        let zoomed = state.g(STATE_ZOOMED);
        if (zoomed) {
            state.u(STATE_VIEWBOX, [0, 0, renderer.renderContext.viewWidth, renderer.renderContext.viewHeight]);
            state.u(STATE_ZOOM_GENOME_LOCATION, undefined);
            state.u(STATE_ZOOMED, false);
        }
    };

    countFilterControls(state).forEach((element) => {
        a(g("chrom-data-counts"), element);
    });

    state.ac(STATE_ZOOMED, (s, key) => {
        let body = getFilterBody(
            state,
            genome,
            manifests[0].chromosomes,
            [state.g(STATE_CATEGORICAL_FACET_VALUES), state.g(STATE_NUMERIC_FACET_VALUES)],
            state.g(STATE_COMBO_SET_OP),
        );

        postJson("/search/combined_experiment_coverage", JSON.stringify(body)).then((response_json) => {
            state.u(STATE_COVERAGE_DATA, mergeFilteredData(state.g(STATE_COVERAGE_DATA), response_json.chromosomes));
        });
    });

    state.ac(STATE_ALL_FILTERED, (s, key) => {
        render(state, genomeRenderer);
    });

    function get_all_data() {
        let body = getFilterBody(
            state,
            genome,
            manifests[0].chromosomes,
            [state.g(STATE_CATEGORICAL_FACET_VALUES)],
            state.g(STATE_COMBO_SET_OP),
        );

        postJson("/search/combined_experiment_coverage", JSON.stringify(body)).then((response_json) => {
            state.u(STATE_COVERAGE_DATA, mergeFilteredData(state.g(STATE_COVERAGE_DATA), response_json.chromosomes));
            state.u(STATE_NUMERIC_FILTER_INTERVALS, response_json.numeric_intervals);
            state.u(
                STATE_NUMERIC_FACET_VALUES,
                [response_json.numeric_intervals.effect, response_json.numeric_intervals.sig],
                false,
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
        debounce((s, key) => get_all_data(), 300),
    );

    state.ac(
        STATE_NUMERIC_FACET_VALUES,
        debounce((s, key) => {
            // Send facet data to server to get filtered data and updated numeric facets
            let body = getFilterBody(
                state,
                genome,
                manifests[0].chromosomes,
                [state.g(STATE_CATEGORICAL_FACET_VALUES), state.g(STATE_NUMERIC_FACET_VALUES)],
                state.g(STATE_COMBO_SET_OP),
            );

            postJson("/search/combined_experiment_coverage", JSON.stringify(body)).then((response_json) => {
                state.u(
                    STATE_COVERAGE_DATA,
                    mergeFilteredData(state.g(STATE_COVERAGE_DATA), response_json.chromosomes),
                );
                state.u(STATE_ITEM_COUNTS, [
                    response_json.reo_count,
                    response_json.source_count,
                    response_json.target_count,
                ]);
            });
        }, 300),
    );

    state.ac(STATE_NUMERIC_FILTER_INTERVALS, (s, key) => {
        cc(g("chrom-data-numeric-facets"));
        numericFilterControls(state, state.g(STATE_FACETS)).forEach((element) =>
            a(g("chrom-data-numeric-facets"), element),
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
        }, 60),
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
        false,
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
                    csrfToken,
                ),
            false,
        );

        let dataDownloadAll = g("dataDownloadAll");
        dataDownloadAll.addEventListener(
            "click",
            () =>
                getDownloadAll(
                    [state.g(STATE_CATEGORICAL_FACET_VALUES), state.g(STATE_NUMERIC_FACET_VALUES)],
                    exprAccessionID,
                    csrfToken,
                ),
            false,
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
        false,
    );

    state.ac(STATE_COVERAGE_TYPE, (s, key) => {
        setLegendIntervals(state, state.g(STATE_COVERAGE_DATA));
        render(state, genomeRenderer);
    });

    //
    // Feature Filter Selector
    //
    let featureFilterSelector = g("feature-select");
    featureFilterSelector.addEventListener(
        "change",
        () => {
            state.u(STATE_FEATURE_FILTER_TYPE, featureFilterSelector.value);
        },
        false,
    );

    state.ac(STATE_FEATURE_FILTER_TYPE, (s, key) => {
        get_all_data();
    });

    //
    // Experiment Combination Set Operator Selector
    //
    let setOpSelector = g("set-op-select");
    setOpSelector.addEventListener(
        "change",
        () => {
            state.u(STATE_COMBO_SET_OP, setOpSelector.value);
        },
        false,
    );

    state.ac(STATE_COMBO_SET_OP, (s, key) => {
        get_all_data();
    });
}
