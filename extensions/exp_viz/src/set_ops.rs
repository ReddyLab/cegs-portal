use pyo3::prelude::*;

use cov_viz_ds::ExperimentFeatureData;
use exp_viz::{FeatureDataValue, Op, SetOp};

use std::boxed::Box;

#[pyclass(name = "ExperimentFeatureData")]
#[derive(Clone, Debug)]
pub struct PyExperimentFeatureData {
    pub data: Option<ExperimentFeatureData>,
    pub op: Option<SetOp>,
}

impl PyExperimentFeatureData {
    pub fn into_feature_data(&self) -> FeatureDataValue {
        FeatureDataValue {
            feature_data: self.data.clone(),
            feature_data_set: self.op.as_ref().map(|x| Box::new(x.clone())),
        }
    }
}

#[pymethods]
impl PyExperimentFeatureData {
    pub fn coalesce(&self) -> Option<PyExperimentFeatureData> {
        if self.data.is_some() {
            return Some(PyExperimentFeatureData {
                data: self.data.clone(),
                op: None,
            });
        } else if let Some(op) = &self.op {
            return op.coalesce().map(|x| PyExperimentFeatureData {
                data: Some(x),
                op: None,
            });
        } else {
            None
        }
    }

    fn union(&self, other: PyExperimentFeatureData) -> PyExperimentFeatureData {
        PyExperimentFeatureData {
            data: None,
            op: Some(SetOp {
                op: Op::Union,
                left: self.into_feature_data(),
                right: other.into_feature_data(),
            }),
        }
    }

    fn intersection(&self, other: PyExperimentFeatureData) -> PyExperimentFeatureData {
        PyExperimentFeatureData {
            data: None,
            op: Some(SetOp {
                op: Op::Intersection,
                left: self.into_feature_data(),
                right: other.into_feature_data(),
            }),
        }
    }
}
