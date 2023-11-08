use pyo3::prelude::*;
use roaring::RoaringTreemap;

use exp_viz::IncludedFeatures;

#[pyclass(name = "IncludedFeatures")]
pub struct PyIncludedFeatures {
    pub sources: RoaringTreemap,
    pub targets: RoaringTreemap,
}

impl PyIncludedFeatures {
    pub fn to_included_features(&self) -> IncludedFeatures {
        IncludedFeatures {
            sources: self.sources.clone(),
            targets: self.targets.clone(),
        }
    }
}
