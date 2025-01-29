import {STATE_COVERAGE_TYPE, COVERAGE_TYPE_COUNT, COVERAGE_TYPE_EFFECT, COVERAGE_TYPE_SIG} from "./consts.js";

export function coverageTypeFunctions(count, sig, effect) {
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

export function coverageTypeDeferredFunctions(count, sig, effect) {
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

export function coverageValue(selectedCoverageType) {
    if (selectedCoverageType == "count") {
        return COVERAGE_TYPE_COUNT;
    } else if (selectedCoverageType == "sig") {
        return COVERAGE_TYPE_SIG;
    } else if (selectedCoverageType == "effect") {
        return COVERAGE_TYPE_EFFECT;
    }
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

export const levelCountInterval = valueInterval((d) => d.count);
export const sigInterval = valueInterval((d) => d.log10_sig);
export const effectInterval = valueInterval((d) => d.effect);

let getLegendIntervalFunc = coverageTypeFunctions(levelCountInterval, sigInterval, effectInterval);

export {getLegendIntervalFunc};
