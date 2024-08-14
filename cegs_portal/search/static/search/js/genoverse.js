CEGSGenoverse = Genoverse.extend({
    // debug: true,
    _sharedState: {
        region: null,
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
    constructor: function (config) {
        // The portal backend uses "hg19/hg38"
        // but genoverse uses "grch37/grch38" so we
        // have to convert here.
        //
        // Portal endpoints do the reverse mapping.
        if (config.genome.toLowerCase() == "hg38") {
            config.genome = "grch38";
            config.assembly = "grch38";
        } else if (config.genome.toLowerCase() == "hg19") {
            config.genome = "grch37";
            config.assembly = "grch37";
        }

        this.base(config);
    },
    init: function () {
        this.base();
        this.updateSharedState("region", {chr: this.chr, start: this.start, end: this.end});
    },
    updateURL: function () {
        this.base();
        this.updateSharedState("region", {chr: this.chr, start: this.start, end: this.end});
    },
});

Genoverse.Track.Model.DHS = Genoverse.Track.Model.extend({
    url: "/search/featureloc/__CHR__/__START__/__END__?assembly=__ASSEMBLY__&search_type=overlap&accept=application/json&format=genoverse&feature_type=DHS&feature_type=cCRE&feature_type=gRNA&feature_type=Chromatin%20Accessible%20Region&property=effect_directions&property=effect_targets&property=significant",
    dataRequestLimit: 5000000,
});

Genoverse.Track.View.DHS = Genoverse.Track.View.extend({
    featureHeight: 10,
    labels: true,
    repeatLabels: true,
    bump: true,
    dhsColor: "#e69600",
    fontHeight: 14,
    withNonSigEffectColor: "#000",
    withSigEffectColor: {DHS: "#009e73", gRNA: "#E69F00", cCRE: "#56B4E9", "Chromatin Accessible Region": "#F0E442"},
    borderColor: "#f0e442",
    setFeatureColor: function (feature) {
        feature.color = this.dhsColor;
        feature.legend = `${feature.type} w/o Reg Effect`;

        if (
            feature.effect_directions.length > 0 &&
            feature.effect_directions.every((effect) => effect.effect_directions == "Non-significant")
        ) {
            feature.color = this.withNonSigEffectColor;
            feature.legend = `${feature.type} w/ Non-significant Effect`;
        } else {
            feature.legend = `${feature.type} w/ Significant Effect`;
            feature.color = this.withSigEffectColor[feature.type];
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
        let newEffectfulDHSs = data.filter((feature) => feature.effect_directions.length > 0);
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
        for (let feature of data) {
            if (feature.effect_directions.length == 0) {
                //  Skip sources that haven't been part of an experiment
                continue;
            }

            this.insertFeature(feature);
        }
    },
});

Genoverse.Track.Model.Gene.Portal = Genoverse.Track.Model.Gene.extend({
    url: "/search/featureloc/__CHR__/__START__/__END__?assembly=__ASSEMBLY__&accept=application/json&format=genoverse&feature_type=Gene",
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
    url: "/search/featureloc/__CHR__/__START__/__END__?assembly=__ASSEMBLY__&accept=application/json&format=genoverse&feature_type=Transcript&feature_type=Exon",
    dataRequestLimit: 5000000, // As per e! REST API restrictions

    setDefaults: function () {
        this.geneIds = {};
        this.seenGenes = 0;

        this.base.apply(this, arguments);
    },
    parseData: function (data, chr) {
        let model = this;
        let featuresById = this.featuresById;
        let ids = [];
        let transcript_parents = {};
        let exons = new Set();

        data.filter((d) => d.type === "Transcript").forEach(function (transcript, i) {
            transcript_parents[transcript.accession_id] = transcript.parent_accession_id;

            if (!featuresById[transcript.parent_accession_id]) {
                model.geneIds[transcript.parent_accession_id] =
                    model.geneIds[transcript.parent_accession_id] || ++model.seenGenes;
                geneObj = {
                    id: transcript.parent_accession_id,
                    accession_id: transcript.parent_accession_id,
                    ensembl_id: transcript.parent_ensembl_id,
                    name: transcript.parent,
                    chr: transcript.chr,
                    start: transcript.start,
                    end: transcript.end,
                    strand: transcript.strand,
                    ref_genome: transcript.ref_genome,
                    exons: {},
                    subFeatures: [],
                    subtype: transcript.subtype,
                    type: transcript.type,
                };
                geneObj.label =
                    transcript.strand === "+"
                        ? (transcript.parent || transcript.ensembl_id) + " >"
                        : "< " + (transcript.parent || transcript.ensembl_id);
                geneObj.sort =
                    model.geneIds[transcript.parent_accession_id] * 1e10 +
                    (transcript.subtype === "protein_coding" ? 0 : 1e9) +
                    transcript.start +
                    i;

                // Adds feature to featuresById object
                model.insertFeature(geneObj);
            }

            ids.push(geneObj.accession_id);
        });

        data.filter((d) => d.type === "Exon" && featuresById[transcript_parents[d.parent_accession_id]]).forEach(
            (exon) => {
                if (!exons.has(exon.accession_id)) {
                    featuresById[transcript_parents[exon.parent_accession_id]].subFeatures.push(exon);
                    exons.add(exon.accession_id);
                }
            }
        );

        ids.forEach((id) => featuresById[id].subFeatures.sort((a, b) => a.start - b.start));
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
    populateMenu: async function (feature) {
        let url = `/search/feature/accession/${feature.accession_id}`;
        let type = feature.type.toUpperCase();
        let menu = {
            title: `<a target="_blank" href="${url}">${type}: ${feature.accession_id}</a>`,
            Location: `chr${feature.chr}:${feature.start}-${feature.end}`,
            Assembly: feature.ref_genome,
            "Closest Gene": `<a target="_blank" href="/search/feature/ensembl/${feature.closest_gene_ensembl_id}">${feature.closest_gene_name} (${feature.closest_gene_ensembl_id})</a>`,
        };

        let effects = await fetch(
            `/search/feature/accession/${feature.accession_id}/source_for?accept=application/json`,
        ).then((response) => {
            if (!response.ok) {
                throw new Error(`${path} fetch failed: ${response.status} ${response.statusText}`);
            }

            return response.json();
        });
        let i = 1;
        for (let reo of effects.object_list.slice(0, 5)) {
            if (reo.targets.length > 0) {
                menu[
                    `${i}. Effect Size`
                ] = `<a target="_blank" href="/search/feature/accession/${reo.targets[0][0]}">${reo.targets[0][1]} ${reo.effect_size}</a>`;
            } else {
                menu[`${i}. Effect Size`] = `${reo.effect_size >= 0 ? "" : "-"}${reo.effect_size}`;
            }

            i++;
        }

        if (effects.object_list.length > 5) {
            menu[
                `Full Effect List`
            ] = `<a target="_blank" href="/search/feature/accession/${feature.accession_id}/source_for">All Associated Effects</a>`;
        }

        return menu;
    },
});

Genoverse.Track.DHS.Effects = Genoverse.Track.DHS.extend({
    id: "dhs-effects",
    name: "Experimentally Tested Elements",
    labels: false,
    legend: Genoverse.Track.Legend.extend({
        name: "Element Types",
    }),
    model: Genoverse.Track.Model.DHS.Effects,
    controls: [
        $('<a title="Change feature height">Squish</a>').on("click", function () {
            const track = $(this)
                .text((i, text) => (/Un/.test(text) ? "Squish" : "Unsquish"))
                .data("track");

            track.setConfig("squish", !track.config.squish);
        }),
    ],
    configSettings: {
        squish: {
            true: {
                featureHeight: 2,
                featureMargin: {top: 1, right: 1, bottom: 1, left: 0},
                labels: false,
            },
            false: {
                featureHeight: 6,
                featureMargin: {top: 2, right: 2, bottom: 2, left: 0},
                labels: true,
            },
        },
    },
    defaultConfig: {
        squish: false,
    },
});

Genoverse.Track.Gene = Genoverse.Track.extend({
    id: "genes",
    name: "Genes",
    resizable: "auto",
    model: Genoverse.Track.Model.Gene.Portal,
    view: Genoverse.Track.View.Gene.Portal,
    legend: Genoverse.Track.Legend.extend({
        name: "Gene Types",
    }),
    populateMenu: function (feature) {
        if (["Gene", "Exon", "Transcript"].includes(feature.type)) {
            var url = `/search/feature/accession/${feature.accession_id}`;
            var menu = {
                title: `<a target="_blank" href="${url}">${feature.name} (${feature.ensembl_id})</a>`,
                Location: `chr${feature.chr}:${feature.start}-${feature.end}`,
                Strand: feature.strand,
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
