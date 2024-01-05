use pyo3::prelude::*;

use cov_viz_ds::ExperimentFeatureData;

#[derive(Clone, Debug)]
#[pyclass(name = "ExperimentFeatureData")]
pub struct PyExperimentFeatureData {
    pub data: ExperimentFeatureData,
}

#[pymethods]
impl PyExperimentFeatureData {
    fn union(&mut self, other: &PyExperimentFeatureData) {
        self.data.union(&other.data);
    }

    fn intersection(&mut self, other: &PyExperimentFeatureData) {
        self.data.intersection(&other.data);
    }
}
