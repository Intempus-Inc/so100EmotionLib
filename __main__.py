import argparse
import json
from . import load, names


def main():
    parser = argparse.ArgumentParser(description="Inspect or sample SO-100 authoring motions.")
    parser.add_argument("name", nargs="?", help="motion name; omit to list")
    parser.add_argument("--time", type=float, help="sample time in seconds")
    args = parser.parse_args()
    try:
        if args.name is None:
            if args.time is not None:
                parser.error("--time requires a motion name")
            print("\n".join(names()))
            return
        motion = load(args.name)
        result = {"name": motion.name, "duration": motion.duration, "keyframes": len(motion.frames)}
        if args.time is not None:
            result["pose"] = motion.sample(args.time)
        print(json.dumps(result, indent=2))
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
