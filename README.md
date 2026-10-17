# SO-100 motion library

27 expressive arm recordings, with 198 timed keyframes and a small Python loader. These are authoring poses in an empirical coordinate frame, not motor commands.

## Use

Requires Python 3.10 or later. From a clone of this repository:

```sh
python -m pip install .
python -m so100_motion Admiration --time 1.5
```

```python
from so100_motion import JOINTS, load, names

motion = load("Admiration")
pose = motion.sample(1.5)
print(dict(zip(JOINTS, pose)))
```

`names()` lists recordings. `load_file(path)` reads the same JSON format. Sampling is linear and holds the first/last pose outside the recorded interval. At a repeated timestamp it selects the last frame, preserving the jump in `Craving` at 2 seconds. Nothing is sorted, clamped, or retimed.

## Format and limits

Each root JSON has `keyframes` containing seconds in `time` and six stored radians in `pose`: shoulder pan, shoulder lift, elbow flex, wrist flex, wrist roll, gripper. The conversion metadata records offsets from the original authoring frame. The API checks the schema, frame order, joint order, and finite numbers; it does not validate physical motion.

The original conversion's `validation_passed` flags did not test general correctness and have been removed. Against the historically referenced SO-100 model, 13 recordings contain out-of-range joint values. Some transitions are fast or discontinuous, and some clips do not close into a loop. Map and check these poses against your own model before playback. In particular, do not send angle values directly to MuJoCo torque actuators.

The emotion names describe animation intent, not measured viewer responses. No hardware controller or model assets are included.

## Development and license

After installation, run `python -m unittest discover -s tests`.

Code: [MIT](LICENSE). Motion JSON files: [CC BY 4.0](LICENSE-DATA), attributed to Intempus, Inc. Cite the repository and note modifications when reusing the data.
