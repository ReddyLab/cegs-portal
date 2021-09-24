Genoverse.Track.Model.DHS = Genoverse.Track.Model.extend({
    url              : '/search/dhsloc/__CHR__/__START__/__END__?search_type=overlap&accept=application/json&format=genoverse',
    dataRequestLimit : 5000000,
    parseData        : function (data, chr) {
        gene_names = new Set();

        for (var i = 0; i < data.length; i++) {
            var feature = data[i];
            feature.type = "dhs";
            feature.closest_gene_ensembl_id = feature.closest_gene.ensembl_id;
            this.insertFeature(feature);

            var gene = feature.closest_gene;
            var assembly = feature.closest_gene_assembly;

            if (!gene_names.has(gene.ensembl_id)){
                feature = assembly;
                feature.type = "gene";
                feature.ensembl_id = gene.ensembl_id;
                feature.label = feature.strand === "+" ? `${feature.name} (${feature.ensembl_id}) >` : `< ${feature.name} (${feature.ensembl_id})`;
                this.insertFeature(feature);
            }
        }
      }
});

Genoverse.Track.View.DHS = Genoverse.Track.View.extend({
    bump: true,
    dhsColor: '#e69600',
    geneColor: '#009e73',
    geneLabelColor: '#000',
    setFeatureColor: function (feature) {
        if (feature.type === "dhs") {
            feature.color = this.dhsColor;
            feature.legendColor = this.dhsColor;
            feature.legend = "DNase I Hypersensitive Site";
        }

        if (feature.type === "gene") {
            feature.color = this.geneColor;
            feature.labelColor = this.geneLabelColor;
            feature.legendColor = this.geneColor;
            feature.legend = "Gene";
        }
    },
    bumpFeature: function (bounds, feature, scale, tree) {
        var scaleSettings = this.scaleSettings[feature.chr][scale];
        var labels = tree === scaleSettings.labelPositions && tree !== scaleSettings.featurePositions;
        var bump, clash;

        if (labels) {
            return;
        }

        if (feature.type === "dhs") {
            return;
        }

        if (feature.type === "gene") {
            bounds.y = feature.position[scale]['bounds'].y + feature.position[scale]['bounds'].h;
        }

        do {
            bump  = false;
            clash = tree.search(bounds)[0];

            if (clash && clash.id !== feature.id) {
                bounds.y = clash.position[scale]['bounds'].y + clash.position[scale]['bounds'].h;
                bump = true;
            }
        } while (bump);

        feature.position[scale].Y = bounds.y;
      },
  });

Genoverse.Track.DHS = Genoverse.Track.extend({
    id     : 'dhs',
    name            : 'DNaseI Hypersensitive Sites',
    resizable       : 'auto',
    model           : Genoverse.Track.Model.DHS,
    view            : Genoverse.Track.View.DHS,
    legend          : true,
    populateMenu: function (feature) {
        if (feature.type === "dhs") {
            var url  = `/search/dhs/${feature.id}`
            var menu = {
            title    : `<a target="_blank" href="${url}">DHS:${feature.id}</a>`,
            Location : `chr${feature.chr}:${feature.start}-${feature.end}`,
            Assembly : `${feature.ref_genome} ${feature.ref_genome_patch}`,
            "Closest Gene" : `<a target="_blank" href="${url}">${feature.closest_gene_assembly.name} (${feature.closest_gene.ensembl_id})</a>`
            };

            return menu;
        }

        if (feature.type === "gene") {
            var url  = `/search/gene/ensembl/${feature.ensembl_id}`
            var menu = {
            title    : `<a target="_blank" href="${url}">${feature.name} (${feature.ensembl_id})</a>`,
            Location : `chr${feature.chr}:${feature.start}-${feature.end}`,
            Strand   : feature.strand,
            Assembly : `${feature.ref_genome} ${feature.ref_genome_patch}`
            };

            return menu;
        }
    }
});
