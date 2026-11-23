# Facial-asymmetry grading for Bell's palsy

A landmark-based pipeline that measures facial asymmetry from an ordinary photograph, built for clinics without a trained examiner.

**Paper:** Ahmed Sultan and Ahsan Numan, *A Machine Learning System for Quantifying Facial Asymmetry in Bell's Palsy across Underrepresented Phenotypes*. Accepted for publication in the Annals of KEMU. Preprint: Research Square, 2026, [doi:10.21203/rs.3.rs-11393331/v1](https://doi.org/10.21203/rs.3.rs-11393331/v1)

## Method

1. MediaPipe Face Mesh places 478 landmarks on a frontal photograph.
2. A facial midline is fitted by least squares through 28 landmarks that lie on it.
3. Eleven regional indices compare paired landmarks on either side of that line: brows, eyes, nose, mouth and jaw.
4. Their mean is the global asymmetry index.

## What the paper shows

Before trying the method on patients, the paper measures how it behaves on 10,954 faces without palsy from the FairFace validation set, balanced across seven groups.

- Faces were detected in 90.1 % of images; failure rates ran from 5.9 % to 12.7 % depending on the group.
- Median global asymmetry on these faces was 0.187. Group differences were statistically detectable but tiny (ε² ≈ 0.003).
- Flagging thresholds set per group ranged from 0.601 to 0.654, around a pooled 0.636.
- The inner corner of the eye came out most asymmetric in every group. The paper traces this to an unstable denominator in that index, not to real asymmetry.

How well the index picks up Bell's palsy itself is the next study, with the Department of Neurology at King Edward Medical University.

## Code

The analysis code goes in this folder once the paper is published.
