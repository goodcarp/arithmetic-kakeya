//! Python `repr`/`json.dumps` renderings of the exact shapes the drivers print.

use crate::graph::Label;

/// `repr` of a list of ints: `[2, 2]`.
pub fn list_usize(v: &[usize]) -> String {
    let parts: Vec<String> = v.iter().map(|x| x.to_string()).collect();
    format!("[{}]", parts.join(", "))
}

/// `repr` of a tuple of ints: `(0, 1, 1)` (with the 1-tuple comma).
pub fn tuple_u8(v: &[u8]) -> String {
    let parts: Vec<String> = v.iter().map(|x| x.to_string()).collect();
    if v.len() == 1 {
        format!("({},)", parts[0])
    } else {
        format!("({})", parts.join(", "))
    }
}

pub fn repr_label(l: Label) -> String {
    format!("({}, {})", l.0, l.1)
}

/// `repr` of a tuple of labels: `((1, 0), (0, 1))`.
pub fn tuple_labels(v: &[Label]) -> String {
    let parts: Vec<String> = v.iter().map(|&l| repr_label(l)).collect();
    if v.len() == 1 {
        format!("({},)", parts[0])
    } else {
        format!("({})", parts.join(", "))
    }
}

/// `repr` of the generator list: `[(0, (1, 0)), (3, (0, 1))]`.
pub fn repr_gens(v: &[(usize, Label)]) -> String {
    let parts: Vec<String> = v
        .iter()
        .map(|&(j, l)| format!("({}, {})", j, repr_label(l)))
        .collect();
    format!("[{}]", parts.join(", "))
}

/// `json.dumps` of a label list: `[[1, 0], [0, 1]]`.
pub fn json_labels(v: &[Label]) -> String {
    let parts: Vec<String> = v.iter().map(|l| format!("[{}, {}]", l.0, l.1)).collect();
    format!("[{}]", parts.join(", "))
}

/// `json.dumps` of the generator list: `[[0, [1, 0]]]`.
pub fn json_gens(v: &[(usize, Label)]) -> String {
    let parts: Vec<String> = v
        .iter()
        .map(|&(j, l)| format!("[{}, [{}, {}]]", j, l.0, l.1))
        .collect();
    format!("[{}]", parts.join(", "))
}

pub fn json_usize(v: &[usize]) -> String {
    let parts: Vec<String> = v.iter().map(|x| x.to_string()).collect();
    format!("[{}]", parts.join(", "))
}

pub fn json_u8(v: &[u8]) -> String {
    let parts: Vec<String> = v.iter().map(|x| x.to_string()).collect();
    format!("[{}]", parts.join(", "))
}

/// `json.dumps(round(seconds, 1))`.
pub fn seconds(x: f64) -> String {
    format!("{x:.1}")
}

/// `f"{float(sc):.4f}"`.
pub fn f4(x: f64) -> String {
    format!("{x:.4}")
}

/// `json.dumps(str(b) if b else None)` for an optional score.
pub fn json_opt_str(s: Option<String>) -> String {
    match s {
        None => "null".to_string(),
        Some(v) => format!("\"{v}\""),
    }
}

pub fn json_bool(b: bool) -> &'static str {
    if b {
        "true"
    } else {
        "false"
    }
}
