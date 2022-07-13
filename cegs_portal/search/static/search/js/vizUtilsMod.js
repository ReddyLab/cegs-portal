export function toPx(size, chromDimensions) {
    return chromDimensions.maxPxChromWidth * (size / chromDimensions.maxChromSize);
}
