const getLines = function* (text) {
    let textLength = text.length;
    let i = 0;
    let start = 0;
    while (i < textLength) {
        if (text[i] == "\n") {
            yield text.slice(start, i);
            i++;
            start = i;
        } else if (text[i] == "\r") {
            if (i + 1 < textLength && text[i + 1] == "\n") {
                yield text.slice(start, i);
                i += 2;
                start = i;
            } else {
                yield text.slice(start, i);
                i++;
                start = i;
            }
        } else {
            i++;
        }
    }
};

export {getLines};
