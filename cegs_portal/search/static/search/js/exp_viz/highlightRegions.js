export function getHighlightRegions(regionUploadInput, regionReader) {
    if (regionUploadInput.files.length != 1) {
        return;
    }
    regionReader.readAsText(regionUploadInput.files[0]);
}
