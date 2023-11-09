use pyo3::prelude::*;
use roaring::RoaringTreemap;

use cov_viz_ds::ExperimentFeatureData;

#[pyclass(name = "ExperimentFeatureData")]
#[derive(Clone, Debug)]
pub struct PyExperimentFeatureData {
    pub sources: RoaringTreemap,
    pub targets: RoaringTreemap,
}

impl PyExperimentFeatureData {
    pub fn to_feature_data(&self) -> ExperimentFeatureData {
        ExperimentFeatureData {
            sources: self.sources.clone(),
            targets: self.targets.clone(),
        }
    }
}
