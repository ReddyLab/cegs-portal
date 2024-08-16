import {a, cc, e} from "../dom.js";
import {getLegendIntervalFunc, levelCountInterval} from "./covTypeUtils.js";
import {
    STATE_CATEGORICAL_FACET_VALUES,
    STATE_COUNT_FILTER_INTERVALS,
    STATE_COUNT_FILTER_VALUES,
    STATE_FEATURE_FILTER_TYPE,
    STATE_LEGEND_INTERVALS,
    STATE_NUMERIC_FILTER_INTERVALS,
    STATE_NUMERIC_FACET_VALUES,
    STATE_SELECTED_EXPERIMENTS,
    STATE_SOURCE_TYPE,
    STATE_ZOOM_CHROMO_INDEX,
    STATE_ZOOMED,
} from "./consts.js";

export function categoricalFilterControls(facets, default_facets) {
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
                    }),
                ),
            ]);
        });
}

export function numericFilterControls(state, facets) {
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

        filterNodes.push(
            e("div", {class: "h-24 min-w-[12rem]"}, [
                e("div", sliderLabel),
                e("div", {class: "px-4 sm:px-0"}, sliderNode),
            ]),
        );
    }

    sliderNodes.forEach((sliderNode) => {
        sliderNode.noUiSlider.on("slide", function (values, handle) {
            state.u(
                STATE_NUMERIC_FACET_VALUES,
                sliderNodes.map((n) => n.noUiSlider.get(true)),
            );
        });
    });

    return filterNodes;
}

export function countFilterControls(state) {
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

        filterNodes.push(
            e("div", {class: "h-24 min-w-[12rem]"}, [e("div", name), e("div", {class: "px-4 sm:px-0"}, sliderNode)]),
        );
    }

    sliderNodes.forEach((sliderNode) => {
        sliderNode.noUiSlider.on("slide", function (values, handle) {
            state.u(
                STATE_COUNT_FILTER_VALUES,
                sliderNodes.map((n) => n.noUiSlider.get(true)),
            );
        });
    });

    return filterNodes;
}

export function getFilterBody(state, genome, chroms, filter_values, combo_op) {
    let filters = {
        filters: filter_values,
        chromosomes: genome.map((c) => c.chrom),
    };
    if (state.g(STATE_ZOOMED)) {
        let zoomChromoIndex = state.g(STATE_ZOOM_CHROMO_INDEX);
        filters.zoom = chroms[zoomChromoIndex].chrom;
    }
    try {
        let combinations = state.g(STATE_SELECTED_EXPERIMENTS).map((exp) => exp.join("/"));
        filters.combinations = combinations.concat(combinations.slice(1).map((_) => combo_op));
        filters.combination_features = state.g(STATE_FEATURE_FILTER_TYPE);
    } catch (e) {
        // An "Invalid State Key" exception is expected when this is called from
        // the single experiment page, but other exceptions are not
        if (!(typeof e === "string" && e.startsWith("Invalid State Key"))) {
            throw e;
        }
    }

    return filters;
}

export function setFacetControls(state, categoricalFacetControls, defaultFacets, facets) {
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

export function setCountControls(state, coverageData) {
    let sourceCountInterval = levelCountInterval(coverageData, "source_intervals");
    let targetCountInterval = levelCountInterval(coverageData, "target_intervals");
    state.u(STATE_COUNT_FILTER_INTERVALS, {source: sourceCountInterval, target: targetCountInterval});
    state.u(STATE_COUNT_FILTER_VALUES, [sourceCountInterval, targetCountInterval]);
}

export function setLegendIntervals(state, coverageData) {
    let legendInterval = getLegendIntervalFunc(state);
    let sourceLegendInterval = legendInterval(coverageData, "source_intervals");
    let targetLegendInterval = legendInterval(coverageData, "target_intervals");
    state.u(STATE_LEGEND_INTERVALS, {source: sourceLegendInterval, target: targetLegendInterval});
}
