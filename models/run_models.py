import json
from argparse import ArgumentParser, Namespace
import os


def main():
    parser = ArgumentParser()
    parser.add_argument("-o", "--output_dir", required=True, type=str, help="The directory to write the test sets to.")
    parser.add_argument("-i", "--test_file_path", required=True, type=str, help="The path to the test set .jsonl file.")
    parser.add_argument("-m", "--models", type=str, help="Model to use. Supports multiple models",
                                nargs="+", choices=["unixcoder", "incoder", "codegpt"])
    parser.add_argument("-s", "--signatures", action="store_true", help="Whether to include all available signatures in test inputs.")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite existing files instead of raising an exception.")
    args = parser.parse_args()

    if not os.path.exists(args.test_file_path):
        raise Exception(f"Test file {args.test_file_path} does not exist.")

    models = []
    if "unixcoder" in args.models:
        from unixcoder_predict import unixcoder
        models.append(unixcoder)
    if "incoder" in args.models:
        from incoder_predict import incoder
        models.append(incoder)
    if "codegpt" in args.models:
        from codegpt_csn_predict import codegpt_csn
        models.append(codegpt_csn)

    os.makedirs(args.output_dir, exist_ok=True)

    run_test_set(args, models)


def run_test_set(args: Namespace, models):
    for model in models:
        output_file = os.path.join(args.output_dir, model["name"] + ".jsonl")
        if os.path.exists(output_file):
            if args.force:
                os.remove(output_file)
            else:
                raise Exception(f"Output file {output_file} already exists. Delete it first.")

        print(f"Running {model['name']} on {args.test_file_path}...")
        generate = model["generate"]

        with open(args.test_file_path, "r") as f_in, \
             open(output_file, "a") as f_out:
            for line in f_in:
                test_obj = json.loads(line)

                full_input = test_obj["input"]

                if args.signatures:
                    signatures = test_obj["signatures"]
                    full_input = "/* available functions:\n" + "\n".join(signatures) + "\n*/\n" + full_input

                test_obj["prediction"] = generate(full_input)
                f_out.write(json.dumps(test_obj) + "\n")


if __name__ == "__main__":
    main()
