export function State(initialState) {
    this.keys = Object.keys(initialState);
    this._callbacks = {};
    this._sharedState = initialState;

    for (const key of this.keys) {
        this._callbacks[key] = [];
    }

    this._checkSharedStateKey = function (key) {
        if (!Object.keys(this._sharedState).includes(key)) {
            throw `Invalid State Key: ${key}`;
        }
    };

    this.getSharedState = function (key) {
        this._checkSharedStateKey(key);

        return this._sharedState[key];
    };

    this.g = this.getSharedState;

    this.updateSharedState = function (key, value, fire = true) {
        this._checkSharedStateKey(key);

        this._sharedState[key] = value;

        if (!fire) return;

        for (const callback of this._callbacks[key]) {
            callback(this._sharedState, key);
        }
    };

    this.u = this.updateSharedState;

    this.addCallback = function (keys, callback) {
        if (!Array.isArray(keys)) {
            keys = [keys];
        }

        for (const key of keys) {
            this._checkSharedStateKey(key);

            this._callbacks[key].push(callback);
        }
    };

    this.ac = this.addCallback;
}
