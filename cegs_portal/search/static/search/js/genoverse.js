CEGSGenoverse = Genoverse.extend({
    // debug: true,
    _sharedState: {
        location: null,
        "dhs-data": null,
        "dhs-effect-data": null,
        "dhs-effect-data-deferred": null,
    },
    _checkSharedStateKey: function (key) {
        if (!Object.keys(this._sharedState).includes(key)) {
            throw `Invalid State Key: ${key}`;
        }
    },
    getSharedState: function (key) {
        this._checkSharedStateKey(key);
        return this._sharedState[key];
    },
    updateSharedState: function (key, value) {
        this._checkSharedStateKey(key);
        this._sharedState[key] = value;
        for (var callback of this.sharedStateCallbacks) {
            callback(this._sharedState, key);
        }
    },
    sharedStateCallbacks: [],
    init: function () {
        this.base();
        this.updateSharedState("location", {chr: this.chr, start: this.start, end: this.end});
    },
    updateURL: function () {
        this.base();
        this.updateSharedState("location", {chr: this.chr, start: this.start, end: this.end});
    },
});

Genoverse.Track.Model.DHS = Genoverse.Track.Model.extend({
    url: "/search/featureloc/__CHR__/__START__/__END__?assembly=__ASSEMBLY__&search_type=overlap&accept=application/json&format=genoverse&feature_type=dhs&feature_type=ccre&property=regeffects",
    dataRequestLimit: 5000000,
});

Genoverse.Track.View.DHS = Genoverse.Track.View.extend({
    featureHeight: 5,
    labels: true,
    repeatLabels: true,
    bump: true,
    dhsColor: "#e69600",
    fontHeight: 14,
    withEffectColor: "#000",
    withEffectAndTargetColor: "#009e73",
    borderColor: "#f0e442",
    setFeatureColor: function (feature) {
        feature.color = this.dhsColor;
        feature.legend = "DHS w/o Reg Effect";

        if (feature.source_for.length > 0) {
            feature.color = this.withEffectColor;
            feature.legend = "DHS w/ Untargeted Reg Effect";
        }

        for (effect of feature.source_for) {
            if (effect.targets.length > 0) {
                feature.color = this.withEffectAndTargetColor;
                feature.legend = "DHS w/ Targeted Reg Effect";
            }
        }
    },
});

Genoverse.Track.Model.DHS.Effects = Genoverse.Track.Model.DHS.extend({
    init: function (reset) {
        this.base(reset);

        this.browser.sharedStateCallbacks.push((state, key) => {
            if (key !== "dhs-data") {
                return;
            }
            data = state[key];
            this.setData(data);
        });
    },
    setData: function (data) {
        let oldEffectfulDHSs = this.browser.getSharedState("dhs-effect-data");
        let newEffectfulDHSs = data.filter((feature) => feature.source_for.length > 0);
        let allEffectfulDHSs = oldEffectfulDHSs ? oldEffectfulDHSs.concat(newEffectfulDHSs) : newEffectfulDHSs;

        // Sort DHSs with effects
        allEffectfulDHSs.sort((x, y) => {
            if (x.chr < y.chr) {
                return -1;
            } else if (x.chr > y.chr) {
                return 1;
            }

            if (x.start < y.start) {
                return -1;
            } else if (x.start > y.start) {
                return 1;
            }

            if (x.end < y.end) {
                return -1;
            } else if (x.end > y.end) {
                return 1;
            }

            return 0;
        });

        // Remove duplicates
        allEffectfulDHSs = allEffectfulDHSs.reduce((prev, curr) => {
            if (prev.length == 0) {
                prev.push(curr);
                return prev;
            }

            let prevVal = prev[prev.length - 1];

            if (prevVal.chr === curr.chr && prevVal.start === curr.start && prevVal.end === curr.end) {
                return prev;
            }

            prev.push(curr);
            return prev;
        }, []);
        this.browser.updateSharedState("dhs-effect-data", allEffectfulDHSs);
    },
    getData: function (chr, start, end, done) {
        start = Math.max(1, start);
        end = Math.min(this.browser.getChromosomeSize(chr), end);

        var deferred = $.Deferred();

        if (typeof this.data !== "undefined") {
            this.receiveData(
                typeof this.data.sort === "function"
                    ? this.data.sort(function (a, b) {
                          return a.start - b.start;
                      })
                    : this.data,
                chr,
                start,
                end
            );
            return deferred.resolveWith(this);
        }

        var model = this;
        var bins = [];
        var length = end - start + 1;

        if (!this.url) {
            return deferred.resolveWith(this);
        }

        if (this.dataRequestLimit && length > this.dataRequestLimit) {
            var i = Math.ceil(length / this.dataRequestLimit);

            while (i--) {
                bins.push([start, i ? (start += this.dataRequestLimit - 1) : end]);
                start++;
            }
        } else {
            bins.push([start, end]);
        }

        $.when
            .apply(
                $,
                $.map(bins, function (bin) {
                    var request = $.ajax({
                        url: model.parseURL(chr, bin[0], bin[1]),
                        data: model.urlParams,
                        dataType: model.dataType,
                        context: model,
                        xhrFields: model.xhrFields,
                        success: function (data) {
                            this.browser.updateSharedState("dhs-data", data);
                            this.receiveData(data, chr, bin[0], bin[1]);
                        },
                        error: function (xhr, statusText) {
                            this.track.controller.showError(
                                this.showServerErrors && (xhr.responseJSON || {}).message
                                    ? xhr.responseJSON.message
                                    : statusText + " while getting the data, see console for more details",
                                arguments
                            );
                        },
                        complete: function (xhr) {
                            this.dataLoading = $.grep(this.dataLoading, function (t) {
                                return xhr !== t;
                            });
                        },
                    });

                    request.coords = [chr, bin[0], bin[1]]; // store actual chr, start and end on the request, in case they are needed

                    if (typeof done === "function") {
                        request.done(done);
                    }

                    model.dataLoading.push(request);

                    return request;
                })
            )
            .done(function () {
                deferred.resolveWith(model);
            });

        return deferred;
    },
    parseData: function (data, chr) {
        for (var i = 0; i < data.length; i++) {
            var feature = data[i];
            feature.label = feature.accession_id;

            this.insertFeature(feature);
        }
    },
});

Genoverse.Track.Model.Gene.Portal = Genoverse.Track.Model.Gene.extend({
    url: "/search/featureloc/__CHR__/__START__/__END__?assembly=__ASSEMBLY__&accept=application/json&format=genoverse&feature_type=gene",
    dataRequestLimit: 5000000,
    parseData: function (data, chr) {
        for (let feature of data) {
            feature.label =
                feature.strand === "+"
                    ? `${feature.name} (${feature.ensembl_id}) >`
                    : `< ${feature.name} (${feature.ensembl_id})`;
            this.insertFeature(feature);
        }
    },
});

Genoverse.Track.View.Gene.Portal = Genoverse.Track.View.Gene.extend({
    setFeatureColor: function (feature) {
        var processedTranscript = {
            sense_intronic: 1,
            sense_overlapping: 1,
            processed_transcript: 1,
            nonsense_mediated_decay: 1,
            non_stop_decay: 1,
            antisense: 1,
            retained_intron: 1,
            tec: 1,
            non_coding: 1,
            ambiguous_orf: 1,
            disrupted_domain: 1,
            "3prime_overlapping_ncrna": 1,
        };

        feature.color = "#000000";

        if (processedTranscript[feature.subtype.toLowerCase()]) {
            feature.color = "#0000FF";
            feature.legend = "Processed transcript";
        } else if (feature.subtype === "protein_coding") {
            feature.color = "#A00000";
            feature.legend = "Protein coding";
        } else if (feature.subtype.indexOf("pseudogene") > -1) {
            feature.color = "#666666";
            feature.legend = "Pseudogene";
        } else if (/rna/i.test(feature.subtype) || feature.subtype === "ribozyme") {
            feature.color = "#8B668B";
            feature.legend = "RNA gene";
        } else if (/^tr_.+_gene$/i.test(feature.subtype)) {
            feature.color = "#CD6600";
            feature.legend = "TR gene";
        } else if (/^ig_.+_gene$/i.test(feature.subtype)) {
            feature.color = "#8B4500";
            feature.legend = "IG gene";
        }

        feature.labelColor = feature.labelColor || feature.color;
    },
});

Genoverse.Track.Model.Transcript.Portal = Genoverse.Track.Model.Transcript.extend({
    url: "/search/featureloc/__CHR__/__START__/__END__?assembly=__ASSEMBLY__&accept=application/json&format=genoverse&feature_type=transcript&feature_type=exon",
    dataRequestLimit: 5000000, // As per e! REST API restrictions

    setDefaults: function () {
        this.geneIds = {};
        this.seenGenes = 0;

        this.base.apply(this, arguments);
    },

    // The url above responds in json format, data is an array
    // See rest.ensembl.org/documentation/info/overlap_region for more details
    parseData: function (data, chr) {
        var model = this;
        var featuresById = this.featuresById;
        var ids = [];

        data.filter(function (d) {
            return d.type === "transcript";
        }).forEach(function (transcript, i) {
            if (!featuresById[transcript.accession_id]) {
                model.geneIds[transcript.parent_accession_id] =
                    model.geneIds[transcript.parent_accession_id] || ++model.seenGenes;

                transcript.label =
                    parseInt(transcript.strand, 10) === 1
                        ? (transcript.name || transcript.ensembl_id) + " >"
                        : "< " + (transcript.name || transcript.ensembl_id);
                transcript.sort =
                    model.geneIds[transcript.parent_accession_id] * 1e10 +
                    (transcript.subtype === "protein_coding" ? 0 : 1e9) +
                    transcript.start +
                    i;
                transcript.exons = {};
                transcript.subFeatures = [];

                model.insertFeature(transcript);
            }

            ids.push(transcript.accession_id);
        });

        data.filter(function (d) {
            return d.type === "exon" && featuresById[d.parent_accession_id];
        }).forEach(function (exon) {
            featuresById[exon.parent_accession_id].subFeatures.push(exon);
        });

        ids.forEach(function (id) {
            featuresById[id].subFeatures.sort(function (a, b) {
                return a.start - b.start;
            });
        });
    },
});

Genoverse.Track.View.Transcript.Portal = Genoverse.Track.View.Transcript.extend({
    setFeatureColor: function (feature) {
        var processedTranscript = {
            sense_intronic: 1,
            sense_overlapping: 1,
            processed_transcript: 1,
            nonsense_mediated_decay: 1,
            non_stop_decay: 1,
            antisense: 1,
            retained_intron: 1,
            tec: 1,
            non_coding: 1,
            ambiguous_orf: 1,
            disrupted_domain: 1,
            "3prime_overlapping_ncrna": 1,
        };

        feature.color = "#000000";

        if (processedTranscript[feature.subtype.toLowerCase()]) {
            feature.color = "#0000FF";
            feature.legend = "Processed transcript";
        } else if (feature.subtype === "protein_coding") {
            feature.color = "#A00000";
            feature.legend = "Protein coding";
        } else if (feature.subtype.indexOf("pseudogene") > -1) {
            feature.color = "#666666";
            feature.legend = "Pseudogene";
        } else if (/rna/i.test(feature.subtype) || feature.subtype === "ribozyme") {
            feature.color = "#8B668B";
            feature.legend = "RNA gene";
        } else if (/^tr_.+_gene$/i.test(feature.subtype)) {
            feature.color = "#CD6600";
            feature.legend = "TR gene";
        } else if (/^ig_.+_gene$/i.test(feature.subtype)) {
            feature.color = "#8B4500";
            feature.legend = "IG gene";
        }

        feature.labelColor = feature.labelColor || feature.color;
    },
});

Genoverse.Track.DHS = Genoverse.Track.extend({
    id: "dhs",
    name: "DHSs",
    resizable: "auto",
    model: Genoverse.Track.Model.DHS,
    view: Genoverse.Track.View.DHS,
    legend: true,
    populateMenu: function (feature) {
        var url = `/search/feature/accession/${feature.accession_id}`;
        var type = feature.type.toUpperCase();
        var menu = {
            title: `<a target="_blank" href="${url}">${type}: ${feature.accession_id}</a>`,
            Location: `chr${feature.chr}:${feature.start}-${feature.end}`,
            Assembly: `${feature.ref_genome} ${feature.ref_genome_patch}`,
            "Closest Gene": `<a target="_blank" href="/search/feature/ensembl/${feature.closest_gene_ensembl_id}">${feature.closest_gene_name} (${feature.closest_gene_ensembl_id})</a>`,
        };

        var i = 1;
        for (effect of feature.source_for) {
            for (target of effect.targets) {
                menu[`Target ${i}`] = `<a target="_blank" href="/search/feature/ensembl/${target.ensembl_id}">${
                    target.name
                } ${effect.effect_size >= 0 ? "+" : "-"}${effect.effect_size}</a>`;
                i++;
            }
        }

        return menu;
    },
});

Genoverse.Track.DHS.Effects = Genoverse.Track.DHS.extend({
    id: "dhs-effects",
    name: "DHSs",
    labels: true,
    legend: false,
    model: Genoverse.Track.Model.DHS.Effects,
});

Genoverse.Track.Gene = Genoverse.Track.extend({
    id: "genes",
    name: "Genes",
    resizable: "auto",
    model: Genoverse.Track.Model.Gene.Portal,
    view: Genoverse.Track.View.Gene.Portal,
    legend: Genoverse.Track.Legend.extend({
        name: "Results Legend",
    }),
    populateMenu: function (feature) {
        if (["gene", "exon", "transcript"].includes(feature.type)) {
            var url = `/search/feature/ensembl/${feature.ensembl_id}`;
            var menu = {
                title: `<a target="_blank" href="${url}">${feature.name} (${feature.ensembl_id})</a>`,
                Location: `chr${feature.chr}:${feature.start}-${feature.end}`,
                Strand: feature.strand,
                Assembly: `${feature.ref_genome} ${feature.ref_genome_patch}`,
            };

            return menu;
        }
    },
    // Different settings for different zoom level
    1000000: {
        // This one applies when > 1M base-pairs per screen
        labels: false,
        model: Genoverse.Track.Model.Gene.Portal,
        view: Genoverse.Track.View.Gene.Portal,
    },
    100001: {
        // more than 100K but less then 2M
        labels: true,
        model: Genoverse.Track.Model.Gene.Portal,
        view: Genoverse.Track.View.Gene.Portal,
    },
    1: {
        // > 1 base-pair, but less then 100K
        labels: true,
        model: Genoverse.Track.Model.Transcript.Portal,
        view: Genoverse.Track.View.Transcript.Portal,
    },
});
