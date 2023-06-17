# create a test.jsonl file to feed to the models
import json.decoder
from argparse import ArgumentParser, Namespace
import os
from random import Random
import json
from transformers import AutoTokenizer, RobertaTokenizer, GPT2Tokenizer

TOKEN_LIMIT_CODEGPT = 924
TOKEN_LIMIT_INCODER = 1948
TOKEN_LIMIT_UNIXCODER = 924

incoder_tokenizer = AutoTokenizer.from_pretrained("facebook/incoder-1B")
unixcoder_tokenizer = RobertaTokenizer.from_pretrained("microsoft/unixcoder-base")
codegpt_tokenizer = GPT2Tokenizer.from_pretrained("./codegpt_checkpoint")

def main():
    parser = ArgumentParser()
    parser.add_argument("-i", "--analyze-output-folder", type=str, required=True, help="The folder containing the output of dist/analyze/master.js")
    parser.add_argument("-o", "--output-file", type=str, required=True, help="The file path to write to")
    parser.add_argument("-m", "--max-completions-per-function", type=int, default=3, help="The maximum number of completions to use per function")
    parser.add_argument("-p", "--completion-probability", type=float, default=0.5, help="The probability of including a completion in the test data")
    parser.add_argument("-s", "--seed", type=int, default=42, help="The seed to use for randomization")
    parser.add_argument("-f", "--force", action="store_true", help="Whether to overwrite the output file if it already exists")
    args = parser.parse_args()

    if os.path.exists(args.output_file):
        if args.force:
            os.remove(args.output_file)
        else:
            raise Exception(f"Output file {args.output_file} already exists. Delete it first.")

    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)

    random = Random(args.seed)

    create_test_file(args, random)


def create_test_file(args: Namespace, random: Random):
    analysis_files = [file for file in os.listdir(args.analyze_output_folder) if file.endswith(".json")]
    analysis_files = sorted(analysis_files)

    print(f"Found {len(analysis_files)} analysis files")

    # analysis_file_fns[analysis_file] = [fn, ...]
    analysis_file_fns = {}

    for analysis_file in analysis_files:
        with open(os.path.join(args.analyze_output_folder, analysis_file), "r") as f:
            try:
                analysis = json.load(f)
            except json.decoder.JSONDecoder:
                continue

        available_signatures = []  # all exported function signatures in the analysis file
        for file_details in analysis:
            for exported_fn in file_details["exportedFunctions"]:
                available_signatures.append(exported_fn["signature"])

        available_signatures = list(set(available_signatures))
        available_signature_names = set(signature[:signature.index("(")] for signature in available_signatures)

        for file_details in analysis:
            for exported_fn in file_details["exportedFunctions"]:
                fn_str = exported_fn["text"]
                fn_calls = []

                handled_fn_call_texts = set()

                for fn_call in exported_fn["functionCalls"]:
                    # functionName, functionSource, text
                    fn_call_text = fn_call["text"]
                    called_fn_name = fn_call_text[:fn_call_text.index("(")]

                    if called_fn_name not in available_signature_names:
                        continue

                    if fn_call_text in handled_fn_call_texts:
                        continue

                    handled_fn_call_texts.add(fn_call_text)

                    # find all points at which this fn call is made
                    begin_cursors = []
                    begin_cursor = -1
                    while True:
                        begin_cursor = fn_str.find(fn_call_text, begin_cursor + 1)
                        if begin_cursor == -1:
                            break
                        begin_cursors.append(begin_cursor)

                    for begin_cursor in begin_cursors:
                        fn_calls.append({
                            "beginCursor": begin_cursor,
                            "endCursor": begin_cursor + len(fn_call_text),
                            "text": fn_call_text
                        })

                if len(fn_calls) == 0:
                    continue

                analysis_file_fns.setdefault(analysis_file, []).append({
                    "fn_str": fn_str,
                    "fn_calls": fn_calls,
                    "available_signatures": available_signatures,
                    "source_file_path": file_details["filePath"],
                })

    valid_analysis_files = list(analysis_file_fns.keys())
    print(f"Found {len(valid_analysis_files)} valid projects")

    with open(args.output_file, "w") as f_out:
        analysis_files = sorted(valid_analysis_files)

        for analysis_file in analysis_files:
            fns = analysis_file_fns[analysis_file]

            for fn in fns:
                # select a number of completions to use and output it
                selected_fn_calls = fn["fn_calls"]
                selected_fn_calls = random.sample(
                    selected_fn_calls,
                    min(int(len(selected_fn_calls) * args.completion_probability), args.max_completions_per_function)
                )

                if len(selected_fn_calls) == 0:
                    continue

                # output each selected function call as an {input, gt} obj

                fn_str = fn["fn_str"]
                fn_available_signatures = fn["available_signatures"]

                for selected_fn_call in selected_fn_calls:
                    begin_cursor = selected_fn_call["beginCursor"]
                    end_cursor = selected_fn_call["endCursor"]

                    model_input = " ".join(fn_available_signatures) + " " + fn_str[:end_cursor]
                    if len(unixcoder_tokenizer.tokenize(model_input)) > TOKEN_LIMIT_UNIXCODER:
                        continue
                    if len(codegpt_tokenizer.tokenize(model_input)) > TOKEN_LIMIT_CODEGPT:
                        continue
                    if len(incoder_tokenizer.tokenize(model_input)) > TOKEN_LIMIT_INCODER:
                        continue

                    f_out.write(json.dumps({
                        "signatures": fn_available_signatures,
                        "input": fn_str[:begin_cursor],
                        "gt": fn_str[begin_cursor:end_cursor],
                        "source_file_path": fn["source_file_path"],
                    }) + "\n")


if __name__ == "__main__":
    main()
