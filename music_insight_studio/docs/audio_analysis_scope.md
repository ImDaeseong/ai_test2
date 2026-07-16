# Audio Analysis Scope

## Reliable Measurements

- duration
- sample rate
- BPM estimate
- key estimate
- RMS level
- dynamic range proxy
- spectral centroid and rolloff
- frequency band energy
- LUFS when pyloudnorm is available

## Heuristic Interpretations

- low-end strength
- high-end brightness
- vocal presence proxy
- mix density
- mastering loudness suitability
- section energy flow

## Known Limits

- Key detection can fail for modal, noisy, or heavily processed tracks.
- BPM can be half-time or double-time.
- Vocal balance requires stem separation or a trained model for better accuracy.
- Genre cannot be perfectly inferred from basic spectral features alone.
