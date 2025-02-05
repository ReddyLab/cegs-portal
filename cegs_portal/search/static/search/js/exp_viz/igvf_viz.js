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
    STATE_ITEM_COUNTS,
    STATE_SOURCE_TYPE,
    STATE_COVERAGE_TYPE,
    STATE_LEGEND_INTERVALS,
} from "./consts.js";
import {
    numericFilterControls,
    countFilterControls,
    getFilterBody,
    setFacetControls,
    setCountControls,
    setLegendIntervals,
} from "./ui.js";

function build_state(coverage, genomeRenderer, sourceType) {
    let coverageData = coverage.chromosomes;
    let facets = coverage.facets;
    let default_facets = coverage.default_facets;
    let reoCount = coverage.reo_count;
    let sourceCount = coverage.source_count;
    let targetCount = coverage.target_count;
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

    console.log({effect: effectSizeFilterInterval, sig: sigFilterInterval});
    let state = new State({
        [STATE_ZOOMED]: false,
        [STATE_ZOOM_GENOME_LOCATION]: undefined,
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

async function getCoverageData(staticRoot) {
    let genome;

    try {
        genome = await getJson(`${staticRoot}genome_data/grch38.json`);
    } catch (error) {
        let coverage = g("tabs-overview");
        rc(
            coverage,
            e(
                "div",
                {class: "flex flex-row justify-center"},
                e("div", {class: "content-container grow-0"}, "No experiment coverage information found."),
            ),
        );
        throw new Error("Files necessary to load coverage not found");
    }

    return genome;
}

export async function exp_viz(coverage, staticRoot, csrfToken, loggedIn) {
    let genome;
    try {
        genome = await getCoverageData(staticRoot);
    } catch (error) {
        console.log(error);
        return;
    }
    let genomeName = "GRCH38";
    let sourceType = "Genomic Element";

    rc(g("chrom-data-header"), t("Experiment Overview"));
    const genomeRenderer = new GenomeRenderer(genome);

    let state = build_state(coverage, genomeRenderer, sourceType);

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
            manifest.chromosomes,
            [state.g(STATE_CATEGORICAL_FACET_VALUES), state.g(STATE_NUMERIC_FACET_VALUES)],
            null,
        );

        postJson("/igvf/coverage", JSON.stringify(body)).then((response_json) => {
            state.u(STATE_COVERAGE_DATA, mergeFilteredData(state.g(STATE_COVERAGE_DATA), response_json.chromosomes));
        });
    });

    state.ac(STATE_ALL_FILTERED, (s, key) => {
        render(state, genomeRenderer);
    });

    state.ac(
        STATE_CATEGORICAL_FACET_VALUES,
        debounce((s, key) => {
            // Send facet data to server to get filtered data and updated numeric facets
            let body = getFilterBody(
                state,
                genome,
                manifest.chromosomes,
                [state.g(STATE_CATEGORICAL_FACET_VALUES)],
                null,
            );

            postJson("/igvf/coverage", JSON.stringify(body)).then((response_json) => {
                state.u(
                    STATE_COVERAGE_DATA,
                    mergeFilteredData(state.g(STATE_COVERAGE_DATA), response_json.chromosomes),
                );
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
        }, 300),
    );

    state.ac(
        STATE_NUMERIC_FACET_VALUES,
        debounce((s, key) => {
            // Send facet data to server to get filtered data and updated numeric facets
            let body = getFilterBody(
                state,
                genome,
                manifest.chromosomes,
                [state.g(STATE_CATEGORICAL_FACET_VALUES), state.g(STATE_NUMERIC_FACET_VALUES)],
                null,
            );

            postJson("/igvf/coverage", JSON.stringify(body)).then((response_json) => {
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
}
