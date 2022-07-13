import { toPx } from "./vizUtilsMod.js";

export function chromosomeOutline(scales, chromDimensions, d, i) {
    const width = toPx(d.size, chromDimensions) * scales.scaleX;
    const top = chromDimensions.yInset + (chromDimensions.chromSpacing + chromDimensions.chromHeight) * i * scales.scaleY;
    const bottom = top + chromDimensions.chromHeight * scales.scaleY;
    const outlinePath = ["M", chromDimensions.xInset, ",", top];
    outlinePath.push(
        "C", chromDimensions.xInset - (12 * scales.scale) ,",", top, " ",
        chromDimensions. xInset - (12 * scales.scale) , ",", bottom, " ",
        chromDimensions.xInset, ",", bottom,
    );
    outlinePath.push("M", chromDimensions.xInset + width ,",", top);
    outlinePath.push(
        "C", chromDimensions.xInset + width + (12 * scales.scale) ,",", top, " ",
        chromDimensions.xInset + width + (12 * scales.scale) , ",", bottom, " ",
        chromDimensions.xInset + width, ",", bottom,
    );

    for(const band of d.bands) {
        let bandStart = band.start < band.end ? band.start : band.end;
        let bandEnd = band.start > band.end ? band.start : band.end;
        let bandPxStart = toPx(bandStart, chromDimensions) * scales.scaleX;
        let bandPxEnd = toPx(bandEnd, chromDimensions) * scales.scaleX;
        let bandPxWidth = bandPxEnd - bandPxStart;

        if(band.type == "acen") {
            if(band.id.startsWith("p")) {
                outlinePath.push("M", chromDimensions.xInset + bandPxStart ,",", top);
                outlinePath.push("l", bandPxWidth, ",", chromDimensions.chromHeight / 2 * scales.scaleY);
                outlinePath.push("l", -bandPxWidth, ",", chromDimensions.chromHeight / 2 * scales.scaleY);
            } else {
                outlinePath.push("M", chromDimensions.xInset + bandPxEnd ,",", top);
                outlinePath.push("l", -bandPxWidth, ",", chromDimensions.chromHeight / 2 * scales.scaleY);
                outlinePath.push("l", bandPxWidth, ",", chromDimensions.chromHeight / 2 * scales.scaleY);
            }
        } else {
            outlinePath.push("M", chromDimensions.xInset + bandPxStart ,",", top);
            outlinePath.push("l", bandPxWidth, ",", 0);
            outlinePath.push("M", chromDimensions.xInset + bandPxStart ,",", bottom);
            outlinePath.push("l", bandPxWidth, ",", 0);
        }
    }

    return outlinePath.join("");
}

export function chromosomeBand(scales, chromDimensions, chromIndex) {
    return function(band) {
        const top = chromDimensions.yInset + (chromDimensions.chromSpacing + chromDimensions.chromHeight) * chromIndex * scales.scaleY;
        let bandStart = band.start < band.end ? band.start : band.end;
        let bandPxStart = toPx(bandStart, chromDimensions) * scales.scaleX;
        let bandEnd = band.start > band.end ? band.start : band.end;
        let bandPxEnd = toPx(bandEnd, chromDimensions) * scales.scaleX;
        let bandPxWidth = bandPxEnd - bandPxStart;
        let outlinePath = ["M", chromDimensions.xInset + bandPxStart, ",", top];
        if(band.type == "acen") {
            if(band.id.startsWith("p")) {
                outlinePath.push("M", chromDimensions.xInset + bandPxStart ,",", top);
                outlinePath.push("l", bandPxWidth, ",", chromDimensions.chromHeight / 2 * scales.scaleY);
                outlinePath.push("l", -bandPxWidth, ",", chromDimensions.chromHeight / 2 * scales.scaleY);
            } else {
                outlinePath.push("M", chromDimensions.xInset + bandPxEnd ,",", top);
                outlinePath.push("l", -bandPxWidth, ",", chromDimensions.chromHeight / 2 * scales.scaleY);
                outlinePath.push("l", bandPxWidth, ",", chromDimensions.chromHeight / 2 * scales.scaleY);
            }
        } else {
            outlinePath.push("l", 0, ",", chromDimensions.chromHeight * scales.scaleY);
            outlinePath.push("l", bandPxWidth, ",", 0);
            outlinePath.push("l", 0, ",", -chromDimensions.chromHeight * scales.scaleY);
            outlinePath.push("l", -bandPxWidth, ",", 0);
        }

        return outlinePath.join("");
    }
}
