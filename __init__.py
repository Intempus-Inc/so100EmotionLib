"""SO-100 authoring motions. This module does not control hardware."""

from bisect import bisect_right
from dataclasses import dataclass
from importlib.resources import files
import json
import math
from pathlib import Path

__all__ = ["JOINTS", "Frame", "Motion", "names", "load", "load_file"]

JOINTS = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper")


def _number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    try:
        value = float(value)
    except OverflowError as error:
        raise ValueError(f"{field} must be a finite number") from error
    if not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    return value


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


@dataclass(frozen=True)
class Frame:
    time: float
    pose: tuple[float, ...]


@dataclass(frozen=True)
class Motion:
    name: str
    frames: tuple[Frame, ...]
    coordinate_system: str

    @property
    def duration(self):
        return self.frames[-1].time

    def sample(self, time):
        """Interpolate stored values; hold endpoints and use the last equal-time frame."""
        time = _number(time, "time")
        index = bisect_right(tuple(frame.time for frame in self.frames), time)
        if index == 0:
            return self.frames[0].pose
        if index == len(self.frames):
            return self.frames[-1].pose
        before, after = self.frames[index - 1], self.frames[index]
        weight = (time - before.time) / (after.time - before.time)
        return tuple((1 - weight) * a + weight * b for a, b in zip(before.pose, after.pose))


def _parse(data):
    if not isinstance(data, dict) or not isinstance(data.get("name"), str) or not data["name"]:
        raise ValueError("motion must have a nonempty name")
    if data.get("coordinate_system") != "new_radians_empirical":
        raise ValueError("unsupported coordinate_system; expected new_radians_empirical")
    conversion = data.get("conversion_info")
    if not isinstance(conversion, dict) or conversion.get("joint_order") != list(JOINTS):
        raise ValueError("conversion_info.joint_order must match JOINTS")
    raw_frames = data.get("keyframes")
    if not isinstance(raw_frames, list) or not raw_frames:
        raise ValueError("keyframes must be a nonempty list")
    frames = []
    for i, raw in enumerate(raw_frames):
        if not isinstance(raw, dict):
            raise ValueError(f"keyframes[{i}] must be an object")
        time = _number(raw.get("time"), f"keyframes[{i}].time")
        if time < 0 or (frames and time < frames[-1].time):
            raise ValueError("keyframe times must be nonnegative and nondecreasing")
        pose = raw.get("pose")
        if not isinstance(pose, list) or len(pose) != len(JOINTS):
            raise ValueError(f"keyframes[{i}].pose must contain six numbers")
        frames.append(Frame(time, tuple(_number(v, f"keyframes[{i}].pose") for v in pose)))
    return Motion(data["name"], tuple(frames), data["coordinate_system"])


def names():
    """Return the names of the bundled recordings."""
    return tuple(sorted(p.name[:-5] for p in files("so100_motion").iterdir() if p.name.endswith(".json")))


def load(name):
    """Load a bundled recording by name, ignoring case."""
    if not isinstance(name, str):
        raise ValueError("name must be a string")
    available = {n.casefold(): n for n in names()}
    if name.casefold() not in available:
        raise ValueError(f"unknown motion: {name!r}; use names() to list recordings")
    resource = files("so100_motion").joinpath(available[name.casefold()] + ".json")
    return _parse(json.loads(resource.read_text(encoding="utf-8"), object_pairs_hook=_object))


def load_file(path):
    """Load a local JSON file, checking structure and numeric values."""
    return _parse(json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_object))
