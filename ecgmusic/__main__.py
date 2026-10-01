"""Command line: python -m ecgmusic {download,build,analyze} ..."""
import argparse
import sys

CAVEAT = ("Note: this describes the emotional character of the generated MUSIC, not a validated reading\n"
          "of the person's actual emotion. See the validation plan and ethics in project_description.md.")


def _parser():
    parser = argparse.ArgumentParser(prog="python -m ecgmusic", description="Turn ECG recordings into music.")
    commands = parser.add_subparsers(dest="command", required=True)

    download = commands.add_parser("download", help="download a PhysioNet database into data/")
    download.add_argument("db", help="database name: afdb or mitdb")

    build = commands.add_parser("build", help="rebuild the 14 example pieces and the result tables")
    build.add_argument("--no-audio", action="store_true", help="write MIDI and plots only (no FluidSynth)")
    build.add_argument("--no-essentia", action="store_true", help="skip the pretrained Essentia models")

    analyze = commands.add_parser("analyze", help="turn any ECG file into music and an emotion estimate")
    analyze.add_argument("path", help="WFDB record path without extension, or a one-column sample file")
    analyze.add_argument("--fs", type=float, help="sampling rate in Hz (required for sample files)")
    analyze.add_argument("--channel", type=int, default=0, help="ECG lead to use (default: the first)")
    analyze.add_argument("--start", type=float, default=0.0, help="seconds into the recording to start")
    analyze.add_argument("--duration", type=float, default=60.0, help="seconds to turn into music (default 60)")
    analyze.add_argument("--out", help="output folder (default: output/analysis/<file name>)")
    analyze.add_argument("--no-audio", action="store_true", help="write MIDI and the score only")
    analyze.add_argument("--essentia", action="store_true", help="add a second opinion from Essentia")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)

    if args.command == "download":
        from .data import download_database
        failed = download_database(args.db)
        print(f"{len(failed)} files failed - run the command again to retry them." if failed else "Done.")

    elif args.command == "build":
        from .pipeline import build_examples
        summary, _ = build_examples(audio=not args.no_audio, essentia=not (args.no_essentia or args.no_audio))
        print(f"Wrote {len(summary)} examples to output/examples/")

    elif args.command == "analyze":
        from .pipeline import analyze_file
        try:
            result = analyze_file(args.path, fs=args.fs, channel=args.channel, start=args.start,
                                  duration=args.duration, out_dir=args.out, audio=not args.no_audio,
                                  essentia=args.essentia)
        except ValueError as error:
            sys.exit(f"Could not analyze {args.path}: {error}")
        clip, piece = result["clip"], result["piece"]
        summary = piece.summary()
        print(f"Beats: {len(clip.peaks)}  mean R-R: {clip.mean_rr_ms:.0f} ms  RMSSD: {clip.rmssd_ms:.1f} ms")
        print(f"Emotion: {piece.emotion.quadrant} (valence {piece.emotion.valence:+.2f}, "
              f"arousal {piece.emotion.arousal:+.2f})")
        print(f"Harmony: {summary['consonant_chords']} consonant, {summary['tense_chords']} tense, "
              f"{summary['chaotic_chords']} chaotic chords")
        if result["essentia"]:
            scores = result["essentia"]
            top = max(("happy", "sad", "relaxed", "aggressive"), key=scores.get)
            print(f"Essentia (plain melody): valence {scores['valence']:.2f}, arousal {scores['arousal']:.2f} "
                  f"(1-9 scale), strongest mood: {top}")
        print(f"Music and score written to {result['files']['score_png'].parent}/")
        print(CAVEAT)


if __name__ == "__main__":
    main()
