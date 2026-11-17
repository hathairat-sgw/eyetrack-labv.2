# Drive source integration

Source folder: https://drive.google.com/drive/folders/118tlLCUjhipPrQisDKVlXnM3kxBiewtl
Read collect_data.py, server.py and README_DEV.md through Google Drive connector.
Original Python files saved under work/reference-drive for inspection only; not executed or installed as runtime services.

collect_data.py uses Tobii SDK subscribe/unsubscribe, pupil diameter, monitor geometry and a <30px sample movement heuristic. It also contains older commented/triple-quoted versions. Native pynput listeners capture system-wide mouse activity. server.py is a separate WebSocket proof of concept averaging eye positions and replacing timestamps; its fallback behavior is not merged.

Reused: per-trial exploratory gaze feature derivation in backend/gaze_features.py, exported for external sessions as gaze_features_exploratory.csv. Uses SDK validity, leaves raw gaze.csv unchanged, preserves pupil values without rounding, resets on invalid/missing samples. No display pixels calculated without screen metadata. Display mapping remains unverified. The distance is sample-to-sample pixel distance, not a validated saccade amplitude; stationary_candidate_ms is not validated fixation duration.

Not integrated yet: native OS mouse listener, full RAR archive inspection, live hardware/display/timing validation. Hardware lock retained. No existing datasets imported as new research data.
