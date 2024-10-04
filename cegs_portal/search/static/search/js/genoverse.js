Genoverse.configure({});

// 100 is larger than the sum of the margins we use. By shrinking
// the width by that much it ensures the browser won't "overflow"
// it's container until the window is very narrow.
let browserWidth = () => Math.max(500, window.innerWidth - 100);

/*
 * Title Caps
 *
 * Ported to JavaScript By John Resig - http://ejohn.org/ - 21 May 2008
 * Original by John Gruber - http://daringfireball.net/ - 10 May 2008
 * License: http://www.opensource.org/licenses/mit-license.php
 */

(function () {
    var small = "(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v[.]?|via|vs[.]?)";
    var punct = "([!\"#$%&'()*+,./:;<=>?@[\\\\\\]^_`{|}~-]*)";

    this.titleCaps = function (title) {
        var parts = [],
            split = /[:.;?!] |(?: |^)["Ò]/g,
            index = 0;

        while (true) {
            var m = split.exec(title);

            parts.push(
                title
                    .substring(index, m ? m.index : title.length)
                    .replace(/\b([A-Za-z][a-z.'Õ]*)\b/g, function (all) {
                        return /[A-Za-z]\.[A-Za-z]/.test(all) ? all : upper(all);
                    })
                    .replace(RegExp("\\b" + small + "\\b", "ig"), lower)
                    .replace(RegExp("^" + punct + small + "\\b", "ig"), function (all, punct, word) {
                        return punct + upper(word);
                    })
                    .replace(RegExp("\\b" + small + punct + "$", "ig"), upper),
            );

            index = split.lastIndex;

            if (m) parts.push(m[0]);
            else break;
        }

        return parts
            .join("")
            .replace(/ V(s?)\. /gi, " v$1. ")
            .replace(/(['Õ])S\b/gi, "$1s")
            .replace(/\b(AT&T|Q&A)\b/gi, function (all) {
                return all.toUpperCase();
            });
    };

    function lower(word) {
        return word.toLowerCase();
    }

    function upper(word) {
        return word.substr(0, 1).toUpperCase() + word.substr(1);
    }
})();

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
    fullWidth: 0, // browser.width doesn't include control panels or labels
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

        config.width = browserWidth();

        this.base(config);
    },
    init: function () {
        this.base();
        this.updateSharedState("region", {chr: this.chr, start: this.start, end: this.end});
        this.fullWidth = browserWidth();

        let browser = this;
        window.addEventListener("resize", function () {
            // On iOS devices the "resize" event is dispatched when scrolling, for some reason.
            // In order to avoid constant "resizes" (that are to the same width, but still make network calls
            // to refetch the data) we keep track of the current "full width" and only resize if the new computed width
            // is different.
            let bw = browserWidth();
            if (browser.fullWidth != bw) {
                browser.fullWidth = bw;
                browser.setWidth(bw);
            }
        });
    },
    updateURL: function () {
        this.base();
        this.updateSharedState("region", {chr: this.chr, start: this.start, end: this.end});
    },
});

Genoverse.Track.Model.cCRE = Genoverse.Track.Model.extend({
    url: "/search/featureloc/__CHR__/__START__/__END__?assembly=__ASSEMBLY__&search_type=overlap&accept=application/json&format=genoverse&feature_type=cCRE&property=screen_ccre",
    dataRequestLimit: 5000000,
});

Genoverse.Track.View.cCRE = Genoverse.Track.View.extend({
    featureHeight: 15,
    labels: false,
    repeatLabels: true,
    bump: false,
    color: {
        PLS: "#EB382A",
        pELS: "#F3A94C",
        dELS: "#F7CC63",
        "DNase-H3K4me3": "#F3AEAD",
        "CTCF-only": "#4DB0E4",
        "CTCF-bound": "#4DB0E4",
    },
    setFeatureColor: function (feature) {
        feature.color = this.color[feature.ccre_type];
    },
});

Genoverse.Track.Model.Coverage = Genoverse.Track.Model.extend({
    url: "/search/featureloc/__CHR__/__START__/__END__?assembly=__ASSEMBLY__&search_type=overlap&accept=application/json&format=genoverse&property=reo_source",
    dataRequestLimit: 5000000,
});

Genoverse.Track.View.Coverage = Genoverse.Track.View.extend({
    featureHeight: 15,
    labels: false,
    repeatLabels: true,
    bump: false,
    setFeatureColor: function (feature) {
        feature.color = "#502050";
    },
});

Genoverse.Track.Model.DHS = Genoverse.Track.Model.extend({
    url: "/search/featureloc/__CHR__/__START__/__END__?assembly=__ASSEMBLY__&search_type=overlap&accept=application/json&format=genoverse&feature_type=DHS&feature_type=cCRE&feature_type=gRNA&feature_type=Chromatin%20Accessible%20Region&property=effect_directions&property=significant",
    dataRequestLimit: 5000000,
});

Genoverse.Track.View.DHS = Genoverse.Track.View.extend({
    featureHeight: 15,
    labels: true,
    repeatLabels: true,
    bump: true,
    dhsColor: "#e69600",
    fontHeight: 14,
    withNonSigEffectColor: "#000",
    withSigEffectColor: {
        DHS: "#009e73",
        gRNA: "#E69F00",
        cCRE: "#56B4E9",
        "Chromatin Accessible Region": "#F0E442",
        "Called Regulatory Element": "#F0E442",
    },
    borderColor: "#f0e442",
    setFeatureColor: function (feature) {
        feature.color = this.dhsColor;

        if (
            feature.effect_directions.length > 0 &&
            feature.effect_directions.every((effect) => effect.effect_directions == "Non-significant")
        ) {
            feature.color = this.withNonSigEffectColor;
        } else {
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

        var deferred = Genoverse.jQuery.Deferred();

        if (typeof this.data !== "undefined") {
            this.receiveData(
                typeof this.data.sort === "function"
                    ? this.data.sort(function (a, b) {
                          return a.start - b.start;
                      })
                    : this.data,
                chr,
                start,
                end,
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

        Genoverse.jQuery.when
            .apply(
                $,
                Genoverse.jQuery.map(bins, function (bin) {
                    var request = Genoverse.jQuery.ajax({
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
                                arguments,
                            );
                        },
                        complete: function (xhr) {
                            this.dataLoading = Genoverse.jQuery.grep(this.dataLoading, function (t) {
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
                }),
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
            feature.subtype = titleCaps(feature.subtype.replaceAll("_", " "));
            this.insertFeature(feature);
        }
    },
});

Genoverse.Track.View.Gene.Portal = Genoverse.Track.View.Gene.extend({
    featureHeight: 13,
    setFeatureColor: function (feature) {
        if (feature.subtype === "Protein Coding") {
            feature.color = "#A00000";
        } else if (feature.subtype.indexOf("Pseudogene") > -1) {
            feature.color = "#666666";
        } else if (/rna/i.test(feature.subtype) || feature.subtype === "Ribozyme") {
            feature.color = "#8B668B";
        } else if (/^tr_.+_gene$/i.test(feature.subtype)) {
            feature.color = "#CD6600";
        } else if (/^ig_.+_gene$/i.test(feature.subtype)) {
            feature.color = "#8B4500";
        }

        feature.labelColor = feature.labelColor || feature.color;
    },
});

Genoverse.Track.Model.Transcript.Portal = Genoverse.Track.Model.Transcript.extend({
    url: "/search/featureloc/__CHR__/__START__/__END__?assembly=__ASSEMBLY__&accept=application/json&format=genoverse&feature_type=Transcript&feature_type=Exon&property=parent_info",
    dataRequestLimit: 5000000, // As per e! REST API restrictions

    setDefaults: function () {
        this.geneIds = {};
        this.seenGenes = 0;

        this.base.apply(this, arguments);
    },
    parseData: function (data) {
        let model = this;
        let featuresById = this.featuresById;
        let ids = [];
        let transcript_parents = {};

        data.filter((d) => d.type === "Transcript").forEach(function (transcript, i) {
            transcript_parents[transcript.accession_id] = transcript.parent_accession_id;

            let geneObj = featuresById[transcript.parent_accession_id];
            if (!geneObj) {
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
                    subtype: titleCaps(
                        (transcript.parent_subtype ? transcript.parent_subtype : transcript.subtype).replaceAll(
                            "_",
                            " ",
                        ),
                    ),
                    type: transcript.type,
                };
                geneObj.label =
                    transcript.strand === "+"
                        ? (transcript.parent || transcript.ensembl_id) + " >"
                        : "< " + (transcript.parent || transcript.ensembl_id);
                geneObj.sort =
                    model.geneIds[transcript.parent_accession_id] * 1e10 +
                    (transcript.subtype === "Protein Coding" ? 0 : 1e9) +
                    transcript.start +
                    i;

                // Adds feature to featuresById object
                model.insertFeature(geneObj);
                ids.push(geneObj.accession_id);
            } else {
                geneObj.start = Math.min(geneObj.start, transcript.start);
                geneObj.end = Math.max(geneObj.end, transcript.end);
            }
        });

        // Compute subfeatures for genes
        // This is necessary because there may be multiple "different" exons that exist in the same location.
        // If the start and end are the same, we can skip the new one.
        // If the start is the same but the end is different, we modify the current exon with the largest end
        // If the end is the same but the start is different, we modify the current exon with the smallest start
        let potentialGenes = new Map();
        data.filter((d) => d.type === "Exon" && featuresById[transcript_parents[d.parent_accession_id]]).forEach(
            (exon) => {
                let geneId = transcript_parents[exon.parent_accession_id];
                let gene = potentialGenes.get(geneId);
                // New gene, so we can just add the current exon
                if (!gene) {
                    gene = new Array();
                    gene.push(exon);
                    potentialGenes.set(geneId, gene);
                } else {
                    // cycle through existing exons to see if we can merge with one
                    let merged = false;
                    for (let oldExon of gene) {
                        if (!merged && exon.start <= oldExon.end && exon.end >= oldExon.start) {
                            oldExon.start = Math.min(oldExon.start, exon.start);
                            oldExon.end = Math.max(exon.end, oldExon.end);
                            merged = true;
                        }
                    }
                    if (!merged) {
                        gene.push(exon);
                    }
                }
            },
        );

        // Add computed subfeatures to the genes
        potentialGenes.forEach((gene, geneId) => {
            gene.forEach((exon) => {
                featuresById[geneId].subFeatures.push(exon);
            });
        });

        for (let id in featuresById) {
            featuresById[id].subFeatures.sort((a, b) => a.start - b.start);
        }
    },
});

Genoverse.Track.View.Transcript.Portal = Genoverse.Track.View.Transcript.extend({
    featureHeight: 13,
    setFeatureColor: function (feature) {
        var processedTranscript = {
            "sense intronic": 1,
            "sense overlapping": 1,
            "processed transcript": 1,
            "nonsense mediated decay": 1,
            "non stop decay": 1,
            antisense: 1,
            "retained intron": 1,
            tec: 1,
            "non coding": 1,
            "ambiguous orf": 1,
            "disrupted domain": 1,
            "3prime overlapping ncrna": 1,
        };

        feature.color = "#000000";

        if (processedTranscript[feature.subtype.toLowerCase()]) {
            feature.color = "#0000FF";
        } else if (feature.subtype === "Protein Coding") {
            feature.color = "#A00000";
        } else if (feature.subtype.indexOf("Pseudogene") > -1) {
            feature.color = "#666666";
        } else if (/rna/i.test(feature.subtype) || feature.subtype === "Ribozyme") {
            feature.color = "#8B668B";
        } else if (/^tr_.+_gene$/i.test(feature.subtype)) {
            feature.color = "#CD6600";
        } else if (/^ig_.+_gene$/i.test(feature.subtype)) {
            feature.color = "#8B4500";
        }

        feature.labelColor = feature.labelColor || feature.color;
    },
});

Genoverse.Track.cCRE = Genoverse.Track.extend({
    id: "ccres",
    name: "cCREs",
    resizable: false,
    model: Genoverse.Track.Model.cCRE,
    view: Genoverse.Track.View.cCRE,
    border: false,
    controls: "off",

    populateMenu: function (feature) {
        return {
            title: `<u><a target="_blank" href="https://screen.wenglab.org/assets/about/images/figure3.png">SCREEN cCRE (${feature.ccre_type})</a></u>`,
            Location: `chr${feature.chr}:${feature.start}-${feature.end}`,
            Assembly: feature.ref_genome,
            "Closest Gene": `<a target="_blank" href="/search/feature/ensembl/${feature.closest_gene_ensembl_id}">${feature.closest_gene_name} (${feature.closest_gene_ensembl_id})</a>`,
        };
    },
    click: function (e) {
        var target = Genoverse.jQuery(e.target);
        var x = e.pageX - this.container.parent().offset().left + this.browser.scaledStart;
        var y = e.pageY - target.offset().top;

        if (e.type === "mouseup") {
            this.browser.makeMenu(this.getClickedFeatures(x, y, target), e, this.track);
            return;
        } else if (e.type === "mousemove") {
            var f = this.getClickedFeatures(x, 3, target)[0];
            if (f && f.ccre_type) {
                this.container.tipsy("hide");

                this.container
                    .attr("title", f.ccre_type)
                    .tipsy({trigger: "manual", container: "body", offset: -15})
                    .tipsy("show")
                    .data("tipsy")
                    .$tip.css("left", function () {
                        return e.clientX - Genoverse.jQuery(this).width() / 2;
                    });
            } else {
                this.container.tipsy("hide");
            }
        }
    },
    addUserEventHandlers: function () {
        var track = this;

        this.base();

        this.container.on(
            {
                mousemove: function (e) {
                    track.click(e);
                },
                mouseout: function (e) {
                    track.container.tipsy("hide");
                },
            },
            ".gv-image-container",
        );
    },
});

Genoverse.Track.Coverage = Genoverse.Track.extend({
    id: "coverage",
    name: "Coverage",
    resizable: false,
    model: Genoverse.Track.Model.Coverage,
    view: Genoverse.Track.View.Coverage,
    border: false,
    controls: "off",
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
            let effect_size;
            if (reo.targets.length > 0) {
                effect_size = `<a target="_blank" href="/search/feature/accession/${reo.targets[0][0]}">${reo.targets[0][1]} ${reo.effect_size}</a>`;
            } else {
                effect_size = `${reo.effect_size}`;
            }
            menu[`${i}.`] =
                `<a target="_blank" href="/search/experiment/${reo.experiment.accession_id}">Screen: ${reo.experiment.type}</a>, Effect Size: ${effect_size}`;

            i++;
        }

        if (effects.object_list.length > 5) {
            menu[`Full Effect List`] =
                `<a target="_blank" href="/search/feature/accession/${feature.accession_id}/source_for">All Associated Effects</a>`;
        }

        return menu;
    },
    click: function (e) {
        var target = Genoverse.jQuery(e.target);
        var x = e.pageX - this.container.parent().offset().left + this.browser.scaledStart;
        var y = e.pageY - target.offset().top;
        if (e.type === "mouseup") {
            this.browser.makeMenu(this.getClickedFeatures(x, y, target), e, this.track);
            return;
        } else if (e.type === "mousemove") {
            var f = this.getClickedFeatures(x, 3, target)[0];

            if (f) {
                this.container.tipsy("hide");

                this.container
                    .attr("title", f.type)
                    .tipsy({trigger: "manual", container: "body", offset: -15})
                    .tipsy("show")
                    .data("tipsy")
                    .$tip.css("left", function () {
                        return e.clientX - Genoverse.jQuery(this).width() / 2;
                    });
            } else {
                this.container.tipsy("hide");
            }
        }
    },
    addUserEventHandlers: function () {
        var track = this;

        this.base();

        this.container.on(
            {
                mousemove: function (e) {
                    track.click(e);
                },
                mouseout: function (e) {
                    track.container.tipsy("hide");
                },
            },
            ".gv-image-container",
        );
    },
});

Genoverse.Track.DHS = Genoverse.Track.extend({
    id: "dhs",
    name: "DHSs",
    resizable: "auto",
    model: Genoverse.Track.Model.DHS,
    view: Genoverse.Track.View.DHS,
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
            let effect_size;
            if (reo.targets.length > 0) {
                effect_size = `<a target="_blank" href="/search/feature/accession/${reo.targets[0][0]}">${reo.targets[0][1]} ${reo.effect_size}</a>`;
            } else {
                effect_size = `${reo.effect_size}`;
            }
            menu[`${i}.`] =
                `<a target="_blank" href="/search/experiment/${reo.experiment.accession_id}">Screen: ${reo.experiment.type}</a>, Effect Size: ${effect_size}`;

            i++;
        }

        if (effects.object_list.length > 5) {
            menu[`Full Effect List`] =
                `<a target="_blank" href="/search/feature/accession/${feature.accession_id}/source_for">All Associated Effects</a>`;
        }

        return menu;
    },
    click: function (e) {
        var target = Genoverse.jQuery(e.target);
        var x = e.pageX - this.container.parent().offset().left + this.browser.scaledStart;
        var y = e.pageY - target.offset().top;

        if (e.type === "mouseup") {
            this.browser.makeMenu(this.getClickedFeatures(x, y, target), e, this.track);
            return;
        } else if (e.type === "mousemove") {
            var f = this.getClickedFeatures(x, y, target)[0];
            if (f && f.type) {
                this.container.tipsy("hide");

                this.container
                    .attr("title", f.type)
                    .tipsy({trigger: "manual", container: "body", offset: -15})
                    .tipsy("show")
                    .data("tipsy")
                    .$tip.css("left", function () {
                        return e.clientX - Genoverse.jQuery(this).width() / 2;
                    })
                    .css("top", function () {
                        return e.pageY + 10;
                    });
            } else {
                this.container.tipsy("hide");
            }
        }
    },
    addUserEventHandlers: function () {
        var track = this;

        this.base();

        this.container.on(
            {
                mousemove: function (e) {
                    track.click(e);
                },
                mouseout: function (e) {
                    track.container.tipsy("hide");
                },
            },
            ".gv-image-container",
        );
    },
});

Genoverse.Track.DHS.Effects = Genoverse.Track.DHS.extend({
    id: "dhs-effects",
    name: "Experimentally Tested Elements",
    labels: false,
    model: Genoverse.Track.Model.DHS.Effects,
    controls: [
        Genoverse.jQuery('<a title="Change feature height">Squish</a>').on("click", function () {
            const track = Genoverse.jQuery(this)
                .text((i, text) => (/Un/.test(text) ? "Squish" : "Unsquish"))
                .data("track");

            track.setConfig("squish", !track.config.squish);
        }),
    ],
    configSettings: {
        squish: {
            true: {
                featureHeight: 7,
                featureMargin: {top: 1, right: 1, bottom: 1, left: 0},
                labels: false,
            },
            false: {
                featureHeight: 15,
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
    legend: false,
    controls: "off",
    populateMenu: function (feature) {
        if (["Gene", "Exon", "Transcript"].includes(feature.type)) {
            var url = `/search/feature/accession/${feature.accession_id}`;
            var menu = {
                title: `<u><a target="_blank" href="${url}">${feature.name} (${feature.ensembl_id})</a></u>`,
                Type: feature.subtype,
                Location: `chr${feature.chr}:${feature.start}-${feature.end}:${feature.strand}`,
            };

            return menu;
        }
    },
    // Different settings for different zoom level
    100_001: {
        // more than 100K but less then 1M
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
    click: function (e) {
        var target = Genoverse.jQuery(e.target);
        var x = e.pageX - this.container.parent().offset().left + this.browser.scaledStart;
        var y = e.pageY - target.offset().top;

        if (e.type === "mouseup") {
            this.browser.makeMenu(this.getClickedFeatures(x, y, target), e, this.track);
            return;
        } else if (e.type === "mousemove") {
            var f = this.getClickedFeatures(x, y, target)[0];
            if (f && f.type) {
                this.container.tipsy("hide");

                this.container
                    .attr("title", f.subtype)
                    .tipsy({trigger: "manual", container: "body", offset: -15})
                    .tipsy("show")
                    .data("tipsy")
                    .$tip.css("left", function () {
                        return e.clientX - Genoverse.jQuery(this).width() / 2;
                    })
                    .css("top", function () {
                        return e.pageY + 10;
                    });
            } else {
                this.container.tipsy("hide");
            }
        }
    },
    addUserEventHandlers: function () {
        var track = this;

        this.base();

        this.container.on(
            {
                mousemove: function (e) {
                    track.click(e);
                },
                mouseout: function (e) {
                    track.container.tipsy("hide");
                },
            },
            ".gv-image-container",
        );
    },
});
