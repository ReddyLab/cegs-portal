def regulatory_effect(reg_effect, json_format=None):
    return {
        "id": reg_effect.id,
        "direction": reg_effect.direction,
        "effect_size": reg_effect.effect_size,
        "significance": reg_effect.significance,
        "raw_p_value": reg_effect.raw_p_value,
        "cell_lines": [str(cl) for cl in reg_effect.cell_lines],
        "tissue_types": [str(tt) for tt in reg_effect.tissue_types],
        "source_ids": [str(source.id) for source in reg_effect.sources.all()],
        "target_ids": [target.ensembl_id for target in reg_effect.targets.all()],
    }
