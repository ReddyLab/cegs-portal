Genoverse.Track.Model.DHS = Genoverse.Track.Model.extend({});

Genoverse.Track.View.DHS = Genoverse.Track.View.extend({
    featureHeight: 5,
    labels: true,
    repeatLabels: true,
    bump: true,
});

Genoverse.Track.Model.DHS.Portal = Genoverse.Track.Model.DHS.extend({
    url: "/search/dhsloc/__CHR__/__START__/__END__?assembly=__ASSEMBLY__&search_type=overlap&accept=application/json&format=genoverse&region_type=dhs&region_type=ccre",
    dataRequestLimit: 5000000,
    parseData: function (data, chr) {
        gene_names = new Set();

        for (var i = 0; i < data.length; i++) {
            var feature = data[i];
            feature.type = "dhs";
            feature.closest_gene_ensembl_id = feature.closest_gene.ensembl_id;
            this.insertFeature(feature);
        }
    },
});

Genoverse.Track.View.DHS.Portal = Genoverse.Track.View.DHS.extend({
    bump: true,
    dhsColor: "#e69600",
    withEffectColor: "#000",
    withEffectAndTargetColor: "#009e73",
    borderColor: "#f0e442",
    setFeatureColor: function (feature) {
        if (feature.type != "dhs") { return; }

        feature.color = this.dhsColor;
        feature.legend = "DHS w/o Reg Effect";

        if (feature.effects.length > 0) {
            feature.color = this.withEffectColor;
            feature.legend = "DHS w/ Untargeted Reg Effect";
        }

        for (effect of feature.effects) {
            if (effect.targets.length > 0) {
                feature.color = this.withEffectAndTargetColor;
                feature.legend = "DHS w/ Targeted Reg Effect";
            }
        }
    },
});

Genoverse.Track.Model.Gene.Portal = Genoverse.Track.Model.Gene.extend({
    url: "/search/featureloc/__CHR__/__START__/__END__?assembly=__ASSEMBLY__&accept=application/json&format=genoverse&feature=gene",
    dataRequestLimit: 5000000,
    parseData: function (data, chr) {
        for (var i = 0; i < data.length; i++) {
            var feature = data[i];

            feature.type = "gene";
            feature.label =
                feature.strand === "+"
                    ? `${feature.name} (${feature.id}) >`
                    : `< ${feature.name} (${feature.id})`;
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

        if (processedTranscript[feature.feature.subtype.toLowerCase()]) {
            feature.color = "#0000FF";
            feature.legend = "Processed transcript";
        } else if (feature.feature.subtype === "protein_coding") {
            feature.color = "#A00000";
            feature.legend = "Protein coding";
        } else if (feature.feature.subtype.indexOf("pseudogene") > -1) {
            feature.color = "#666666";
            feature.legend = "Pseudogene";
        } else if (/rna/i.test(feature.feature.subtype) || feature.feature.subtype === "ribozyme") {
            feature.color = "#8B668B";
            feature.legend = "RNA gene";
        } else if (/^tr_.+_gene$/i.test(feature.feature.subtype)) {
            feature.color = "#CD6600";
            feature.legend = "TR gene";
        } else if (/^ig_.+_gene$/i.test(feature.feature.subtype)) {
            feature.color = "#8B4500";
            feature.legend = "IG gene";
        }

        feature.labelColor = feature.labelColor || feature.color;
    },
});

Genoverse.Track.Model.Transcript.Portal = Genoverse.Track.Model.Transcript.extend({
    url: "/search/featureloc/__CHR__/__START__/__END__?assembly=__ASSEMBLY__&accept=application/json&format=genoverse&feature=transcript&feature=exon",
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
            return d.feature.type === "transcript";
        }).forEach(function (feature, i) {
            if (!featuresById[feature.id]) {
                model.geneIds[feature.feature.parent_id] =
                    model.geneIds[feature.feature.parent_id] || ++model.seenGenes;

                feature.chr = feature.chr || chr;
                feature.label =
                    parseInt(feature.strand, 10) === 1
                        ? (feature.name || feature.id) + " >"
                        : "< " + (feature.name || feature.id);
                feature.sort =
                    model.geneIds[feature.feature.parent_id] * 1e10 +
                    (feature.feature.subtype === "protein_coding" ? 0 : 1e9) +
                    feature.start +
                    i;
                feature.exons = {};
                feature.subFeatures = [];

                model.insertFeature(feature);
            }

            ids.push(feature.id);
        });

        data.filter(function (d) {
            return d.feature.type === "exon" && featuresById[d.feature.parent_id];
        }).forEach(function (exon) {
            featuresById[exon.feature.parent_id].subFeatures.push(exon);
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

        if (processedTranscript[feature.feature.subtype.toLowerCase()]) {
            feature.color = "#0000FF";
            feature.legend = "Processed transcript";
        } else if (feature.feature.subtype === "protein_coding") {
            feature.color = "#A00000";
            feature.legend = "Protein coding";
        } else if (feature.feature.subtype.indexOf("pseudogene") > -1) {
            feature.color = "#666666";
            feature.legend = "Pseudogene";
        } else if (/rna/i.test(feature.feature.subtype) || feature.feature.subtype === "ribozyme") {
            feature.color = "#8B668B";
            feature.legend = "RNA gene";
        } else if (/^tr_.+_gene$/i.test(feature.feature.subtype)) {
            feature.color = "#CD6600";
            feature.legend = "TR gene";
        } else if (/^ig_.+_gene$/i.test(feature.feature.subtype)) {
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
        if (feature.type === "dhs") {
            var url = `/search/dhs/${feature.id}`;
            var menu = {
                title: `<a target="_blank" href="${url}">DHS:${feature.id}</a>`,
                Location: `chr${feature.chr}:${feature.start}-${feature.end}`,
                Assembly: `${feature.ref_genome} ${feature.ref_genome_patch}`,
                "Closest Gene": `<a target="_blank" href="/search/gene/ensembl/${feature.closest_gene.id}">${feature.closest_gene_assembly.name} (${feature.closest_gene.id})</a>`,
            };

            var i = 1;
            for (effect of feature.effects) {
                for (target of effect.targets) {
                    menu[`Target ${i}`] = `<a target="_blank" href="/search/gene/ensembl/${target}">${target} (${effect.effect_size})</a>`
                    i++;
                }
            }

            return menu;
        }
    },
    // Different settings for different zoom level
    2000000: {
        // This one applies when > 2M base-pairs per screen
        labels: false,
    },
    1: {
        // > 1 base-pair, but less then 100K
        labels: true,
        model: Genoverse.Track.Model.DHS.Portal,
        view: Genoverse.Track.View.DHS.Portal,
    },
});

Genoverse.Track.Gene = Genoverse.Track.extend({
    id: "genes",
    name: "Genes",
    resizable: "auto",
    model: Genoverse.Track.Model.DHS,
    view: Genoverse.Track.View.DHS,
    legend: true,
    populateMenu: function (feature) {
        if (feature.type === "gene") {
            var url = `/search/gene/ensembl/${feature.ensembl_id}`;
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
    2000000: {
        // This one applies when > 2M base-pairs per screen
        labels: false,
    },
    100000: {
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
