function State(keys) {
    this.keys = keys;
    this._callbacks = {}
    this._sharedState = {};
    for (var key of keys) {
        this._sharedState[key] = null;
        this._callbacks[key] = [];
    };

    this._checkSharedStateKey = function (key) {
        if (!Object.keys(this._sharedState).includes(key)) {
            throw `Invalid State Key: ${key}`;
        }
    };

    this.getSharedState = function (key) {
        this._checkSharedStateKey(key);

        return this._sharedState[key];
    };

    this.updateSharedState = function (key, value) {
        this._checkSharedStateKey(key);

        this._sharedState[key] = value;
        for (var callback of this._callbacks[key]) {
            callback(this._sharedState, key);
        }
    };

    this.addCallback = function(key, callback) {
        this._checkSharedStateKey(key);

        this._callbacks[key].push(callback)
    }
}
