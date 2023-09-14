// Debounce and Throttle: https://dev.to/iyashsoni/javascript-debounce-vs-throttle-392i

const debounce = (func, delay) => {
    let debounced = null;
    return (...args) => {
        clearTimeout(debounced);
        debounced = setTimeout(() => {
            func.apply(this, args);
        }, delay);
    };
};

// Throttle with guaranteed final call -- essentially throttle + debounce
const throttle = (func, delay) => {
    let debounced = null;
    let nullFuncCall = (args) => {
        clearTimeout(debounced);
        debounced = setTimeout(() => {
            func.apply(this, args);
        }, delay);
    };
    let throttleFuncCall = (args) => {
        func.apply(this, args);
        currentFuncCall = nullFuncCall;
        setTimeout(() => {
            currentFuncCall = throttleFuncCall;
        }, delay);
    };
    let currentFuncCall = throttleFuncCall;
    return (...args) => {
        currentFuncCall(args);
    };
};

export {debounce, throttle};
