import json
import os
import re
from argparse import ArgumentParser
from enum import Enum
from typing import Optional
import Levenshtein as Levenshtein
from scipy.stats import wilcoxon
from cliffs_delta import cliffs_delta


SIGNIFICANT_P_VALUE = 0.05


class MetricKeys(Enum):
    EXACT_MATCH = 'Exact Match'
    EDIT_SIMILARITY = 'Edit Similarity'

max_metric_key_len = max([len(metric_key.value) for metric_key in MetricKeys])


class ResultKeys(Enum):
    FUNCTION_CALL = 'Function Call'
    FUNCTION_NAME = 'Function Name'


fn_name_pattern = re.compile(r'^[$a-zA-Z_][$\w]*')


def main():
    parser = ArgumentParser()
    parser.add_argument('-is', '--input-folder-signatures', type=str, required=True, help='A folder containing .jsonl files with signatures in the inputs')
    parser.add_argument('-in', '--input-folder-no-signatures', type=str, required=True, help='A folder containing .jsonl files without signatures in the inputs')
    args = parser.parse_args()

    if not os.path.exists(args.input_folder_signatures):
        raise Exception(f'File {args.input_folder_signatures} does not exist')

    if not os.path.exists(args.input_folder_no_signatures):
        raise Exception(f'File {args.input_folder_no_signatures} does not exist')

    signatures_files = [file for file in os.listdir(args.input_folder_signatures) if file.endswith(".jsonl")]
    no_signatures_files = [file for file in os.listdir(args.input_folder_no_signatures) if file.endswith(".jsonl")]
    common_files = set(signatures_files).intersection(set(no_signatures_files))

    if not common_files:
        raise Exception(f'There are no common files in {args.input_folder_signatures} and {args.input_folder_no_signatures}')

    for file in common_files:
        print(f'--- Evaluating {file} ---')

        signatures_file_path = os.path.join(args.input_folder_signatures, file)
        no_signatures_file_path = os.path.join(args.input_folder_no_signatures, file)

        signatures_results = evaluate_file(signatures_file_path)
        no_signatures_results = evaluate_file(no_signatures_file_path)

        if len(signatures_results) != len(no_signatures_results):
            raise Exception('Unexpected error - results must be of equal size with and without signatures')

        n = len(signatures_results)

        no_signatures_valid_call_count = sum(1 if result else 0 for result in no_signatures_results)
        signatures_valid_call_count = sum(1 if result else 0 for result in signatures_results)

        # filter out any invalid results
        for i in range(n - 1, -1, -1):
            if not signatures_results[i] or not no_signatures_results[i]:
                signatures_results.pop(i)
                no_signatures_results.pop(i)

        n = len(signatures_results)

        print(f'Valid Samples without Signatures: {no_signatures_valid_call_count}')
        print(f'Valid Samples with Signatures: {signatures_valid_call_count}')
        print(f'Valid Samples: {n}')
        for result_key in ResultKeys:
            print(f'--- {result_key.value} Results ---')

            for metric_key in MetricKeys:
                signatures_metric_values = [result[result_key][metric_key] for result in signatures_results]
                no_signatures_metric_values = [result[result_key][metric_key] for result in no_signatures_results]
                signatures_mean_metric_value = sum(signatures_metric_values) / len(signatures_metric_values) * 100
                no_signatures_mean_metric_value = sum(no_signatures_metric_values) / len(no_signatures_metric_values) * 100

                print(f'- {metric_key.value}:')
                print(f'No Signatures : {no_signatures_mean_metric_value:>2.2f}')
                print(f'Signatures    : {signatures_mean_metric_value:>2.2f}')

                wilcoxon_p_value = wilcoxon(signatures_metric_values, no_signatures_metric_values).pvalue
                wilcoxon_emotion = '😄' if wilcoxon_p_value <= SIGNIFICANT_P_VALUE else '😞'
                print(f'-> p = {wilcoxon_p_value:.3f} {wilcoxon_emotion}')

                if wilcoxon_p_value <= SIGNIFICANT_P_VALUE:
                    cliffs_delta_result = cliffs_delta(signatures_metric_values, no_signatures_metric_values)[0]
                    print(f'-> d = {cliffs_delta_result:.3f}')


def evaluate_file(file_path: str):
    results = []
    with open(file_path) as f:
        for line in f:
            xdyeet = json.loads(line)

            gt = xdyeet["gt"].strip()
            gt_fn_name = find_function_name(gt)

            if not gt_fn_name:
                results.append(None)
                continue

            prediction = xdyeet["prediction"].strip()
            prediction = find_first_function_call(prediction)

            if not prediction:
                results.append(None)
                continue

            prediction_fn_name = find_function_name(prediction)

            if not prediction_fn_name:
                results.append(None)
                continue

            results.append({
                ResultKeys.FUNCTION_CALL: evaluate(gt, prediction),
                ResultKeys.FUNCTION_NAME: evaluate(gt_fn_name, prediction_fn_name)
            })

    return results


def evaluate(gt: str, prediction: str):
    return {
        MetricKeys.EXACT_MATCH: int(gt == prediction),
        MetricKeys.EDIT_SIMILARITY: Levenshtein.ratio(gt, prediction),
    }
        

def find_first_function_call(text: str) -> Optional[str]:
    result_str = ""

    depth = 0
    call_started = False

    for char in text:
        if char == '(':
            call_started = True
            depth += 1
        elif char == ')':
            depth -= 1
            if depth < 0:
                return None

        result_str += char

        if call_started and depth == 0:
            return result_str

    return None


def find_function_name(text: str) -> Optional[str]:
    text = text.lstrip("!")  # function may be negated once or twice to negate/coerce to boolean

    bracket_pos = text.find('(')

    if bracket_pos == -1:
        return None

    fn_name = text[:bracket_pos]

    if not re.match(fn_name_pattern, fn_name):
        return None

    return fn_name


if __name__ == '__main__':
    main()